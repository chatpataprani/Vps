"""Vps Linux agent: authenticated PTY plus live host and Docker APIs.

Run as a dedicated service account. Membership in the Docker group is effectively
root-equivalent; only grant it to trusted operators and keep this agent private.
"""
import asyncio
import hmac
import os
import pty
import select
import struct
import termios
import fcntl
import signal
import shutil
import platform
from datetime import datetime, timezone

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Vps Linux Agent", docs_url=None, redoc_url=None)
from sites import router as sites_router
from files import router as files_router
from deployments import router as deployments_router
app.include_router(sites_router)
app.include_router(files_router)
app.include_router(deployments_router)

TOKEN = os.environ.get("VPS_AGENT_TOKEN", "")
ORIGIN = os.environ.get("VPS_AGENT_ORIGIN", "")
TERMINAL_LIMIT = max(1, min(int(os.environ.get("VPS_MAX_TERMINAL_SESSIONS", "2")), 10))
TERMINAL_ACTIVE = 0
TERMINAL_LOCK = asyncio.Lock()
try:
    import docker
    DOCKER = docker.from_env()
    DOCKER.ping()
    DOCKER_ERROR = None
except Exception as exc:
    DOCKER = None
    DOCKER_ERROR = str(exc)[:240]


def authorize(value: str):
    if not TOKEN or not hmac.compare_digest(value.removeprefix("Bearer ").strip(), TOKEN):
        raise HTTPException(401, "Unauthorized")


@app.get("/health")
def health():
    return {"status": "ok", "agent": "v1", "terminal": "enabled",
            "docker": DOCKER is not None, "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/system")
def system(authorization: str = Header(default="")):
    authorize(authorization)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    boot = datetime.fromtimestamp(psutil.boot_time(), timezone.utc).isoformat()
    return {
        "hostname": platform.node(), "platform": platform.platform(),
        "architecture": platform.machine(), "python": platform.python_version(),
        "cpu": {"cores": psutil.cpu_count(), "usage_percent": psutil.cpu_percent(interval=0.15)},
        "memory": {"total": vm.total, "used": vm.used, "available": vm.available, "percent": vm.percent},
        "disk": {"total": disk.total, "used": disk.used, "free": disk.free, "percent": disk.percent},
        "network": {"bytes_sent": net.bytes_sent, "bytes_recv": net.bytes_recv},
        "uptime_seconds": int(datetime.now(timezone.utc).timestamp() - psutil.boot_time()),
        "boot_time": boot,
    }


@app.get("/api/docker/status")
def docker_status(authorization: str = Header(default="")):
    authorize(authorization)
    return {"available": DOCKER is not None, "error": DOCKER_ERROR}


@app.get("/api/docker/containers")
def containers(authorization: str = Header(default="")):
    authorize(authorization)
    if DOCKER is None:
        raise HTTPException(503, "Docker unavailable: " + (DOCKER_ERROR or "not installed"))
    try:
        rows = []
        for c in DOCKER.containers.list(all=True):
            c.reload()
            rows.append({"id": c.short_id, "name": c.name, "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                        "status": c.status, "state": c.attrs.get("State", {}),
                        "created": c.attrs.get("Created"), "ports": c.attrs.get("NetworkSettings", {}).get("Ports", {}),
                        "labels": c.labels})
        return rows
    except Exception as exc:
        raise HTTPException(502, "Docker API error: " + str(exc)[:200])


@app.get("/api/docker/containers/{container_id}/stats")
def container_stats(container_id: str, authorization: str = Header(default="")):
    authorize(authorization)
    if DOCKER is None: raise HTTPException(503, "Docker unavailable")
    try:
        c=DOCKER.containers.get(container_id); s=c.stats(stream=False)
        cpu=s.get("cpu_stats",{}); pre=s.get("precpu_stats",{})
        cpu_delta=cpu.get("cpu_usage",{}).get("total_usage",0)-pre.get("cpu_usage",{}).get("total_usage",0)
        sys_delta=cpu.get("system_cpu_usage",0)-pre.get("system_cpu_usage",0)
        cores=len(cpu.get("cpu_usage",{}).get("percpu_usage",[]) or [1])
        percent=(cpu_delta/sys_delta*cores*100) if sys_delta>0 and cpu_delta>=0 else 0
        mem=s.get("memory_stats",{}); usage=mem.get("usage",0); cache=mem.get("stats",{}).get("cache",mem.get("stats",{}).get("inactive_file",0)); used=max(0,usage-cache); limit=mem.get("limit",0)
        net=list(s.get("networks",{}).values()); rx=sum(x.get("rx_bytes",0) for x in net); tx=sum(x.get("tx_bytes",0) for x in net)
        return {"cpu_percent":round(percent,2),"memory_bytes":used,"memory_limit":limit,"network_rx":rx,"network_tx":tx,"pids":s.get("pids_stats",{}).get("current",0)}
    except Exception as exc: raise HTTPException(502,"Container stats failed: "+str(exc)[:180])

class ContainerCommand(BaseModel):
    command: str = Field(min_length=1,max_length=4000)
@app.post("/api/docker/containers/{container_id}/exec")
def container_exec(container_id:str,data:ContainerCommand,authorization:str=Header(default="")):
    authorize(authorization)
    if DOCKER is None: raise HTTPException(503,"Docker unavailable")
    try:
        c=DOCKER.containers.get(container_id)
        if c.status!="running": raise HTTPException(409,"Container must be running")
        result=DOCKER.api.exec_create(c.id,cmd=["/bin/sh","-lc",data.command],stdin=False,stdout=True,stderr=True,tty=False)
        DOCKER.api.exec_start(result["Id"],detach=True)
        import time
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            state=DOCKER.api.exec_inspect(result["Id"])
            if not state.get("Running"): break
            time.sleep(.15)
        else: raise HTTPException(504,"Command timed out after 20 seconds")
        output=DOCKER.api.exec_start(result["Id"],detach=False) if False else DOCKER.api.exec_inspect(result["Id"])
        logs=DOCKER.api.exec_start(result["Id"],detach=False,tty=False) if False else b""
        # Read the exec output from the non-streaming start endpoint.
        logs=DOCKER.api.exec_start(result["Id"],detach=False,tty=False)
        return {"output":logs.decode("utf-8","replace")[-16000:],"exit_code":state.get("ExitCode")}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(502,"Container command failed: "+str(exc)[:200])

class ContainerAction(BaseModel):
    action: str = Field(pattern="^(start|stop|restart)$")


@app.post("/api/docker/containers/{container_id}/action")
def container_action(container_id: str, data: ContainerAction, authorization: str = Header(default="")):
    authorize(authorization)
    if DOCKER is None:
        raise HTTPException(503, "Docker unavailable")
    if not container_id or len(container_id) > 128:
        raise HTTPException(400, "Invalid container ID")
    try:
        c = DOCKER.containers.get(container_id)
        if data.action == "start": c.start()
        elif data.action == "stop": c.stop(timeout=10)
        else: c.restart(timeout=10)
        c.reload()
        return {"id": c.short_id, "name": c.name, "status": c.status, "action": data.action}
    except Exception as exc:
        raise HTTPException(502, "Docker action failed: " + str(exc)[:200])


@app.get("/api/docker/containers/{container_id}/logs")
def container_logs(container_id: str, tail: int = 200, authorization: str = Header(default="")):
    authorize(authorization)
    if DOCKER is None:
        raise HTTPException(503, "Docker unavailable")
    tail = max(1, min(tail, 1000))
    try:
        c = DOCKER.containers.get(container_id)
        return {"id": c.short_id, "logs": c.logs(tail=tail, timestamps=True).decode("utf-8", "replace")}
    except Exception as exc:
        raise HTTPException(502, "Docker logs failed: " + str(exc)[:200])


@app.websocket("/terminal")
async def terminal(ws: WebSocket):
    if not TOKEN or not ORIGIN or ws.headers.get("origin", "") != ORIGIN:
        await ws.close(code=1008); return
    await ws.accept()
    try:
        auth = await asyncio.wait_for(ws.receive_json(), timeout=8)
        if auth.get("type") != "auth" or not hmac.compare_digest(str(auth.get("token", "")), TOKEN):
            await ws.close(code=1008); return
        await ws.send_json({"type": "ready"})
    except Exception:
        await ws.close(code=1008); return

    global TERMINAL_ACTIVE
    async with TERMINAL_LOCK:
        if TERMINAL_ACTIVE >= TERMINAL_LIMIT:
            await ws.close(code=1013, reason="Terminal session limit reached"); return
        TERMINAL_ACTIVE += 1

    master = slave = pid = None
    reader = None
    try:
        master, slave = pty.openpty()
        env = os.environ.copy()
        env.update({"TERM": "xterm-256color", "COLORTERM": "truecolor"})
        pid = os.fork()
        if pid == 0:
            os.close(master); os.setsid(); fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
            for fd in (0, 1, 2): os.dup2(slave, fd)
            if slave > 2: os.close(slave)
            shell = os.environ.get("SHELL", "/bin/bash")
            os.execvpe(shell, [shell, "-l"], env)
        os.close(slave); slave = None
        os.set_blocking(master, False)

        async def read_pty():
            while True:
                try:
                    ready, _, _ = select.select([master], [], [], 0.1)
                    if ready:
                        data = os.read(master, 4096)
                        if not data: break
                        await ws.send_text(data.decode("utf-8", "replace"))
                except (OSError, WebSocketDisconnect): break
                await asyncio.sleep(0)

        reader = asyncio.create_task(read_pty())
        try:
            while True:
                msg = await ws.receive_json()
                if msg.get("type") == "input":
                    os.write(master, str(msg.get("data", ""))[:8192].encode())
                elif msg.get("type") == "resize":
                    cols = max(20, min(int(msg.get("cols", 100)), 300))
                    rows = max(5, min(int(msg.get("rows", 30)), 120))
                    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        except WebSocketDisconnect:
            pass
    finally:
        if reader:
            reader.cancel()
            try: await reader
            except (asyncio.CancelledError, Exception): pass
        for fd in (master, slave):
            if fd is not None:
                try: os.close(fd)
                except OSError: pass
        if pid is not None:
            # The shell owns a process group (setsid in the child). Close the
            # whole interactive job tree, then reap the shell to avoid zombies.
            try: os.killpg(pid, signal.SIGHUP)
            except ProcessLookupError: pass
            deadline = asyncio.get_running_loop().time() + 1.0
            reaped = False
            while asyncio.get_running_loop().time() < deadline:
                try:
                    got, _ = os.waitpid(pid, os.WNOHANG)
                    if got == pid:
                        reaped = True
                        break
                except (ChildProcessError, OSError):
                    reaped = True
                    break
                await asyncio.sleep(0.05)
            if not reaped:
                try: os.killpg(pid, signal.SIGKILL)
                except ProcessLookupError: pass
                try: os.waitpid(pid, 0)
                except (ChildProcessError, OSError): pass
        async with TERMINAL_LOCK:
            TERMINAL_ACTIVE = max(0, TERMINAL_ACTIVE - 1)
