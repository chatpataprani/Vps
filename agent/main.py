"""Experimental authenticated local PTY WebSocket bridge. Not production-ready."""
import asyncio, hmac, os, pty, select, struct, termios, fcntl, signal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="Vps Agent", docs_url=None, redoc_url=None)\nfrom sites import router as sites_router\napp.include_router(sites_router)
TOKEN = os.environ.get("VPS_AGENT_TOKEN", "")
ORIGIN = os.environ.get("VPS_AGENT_ORIGIN", "")

@app.get("/health")
def health():
    return {"status":"ok","agent":"experimental","terminal":"enabled"}

@app.websocket("/terminal")
async def terminal(ws: WebSocket):
    if not TOKEN or (ORIGIN and ws.headers.get("origin","") != ORIGIN):
        await ws.close(code=1008); return
    await ws.accept()
    try:
        auth = await asyncio.wait_for(ws.receive_json(), timeout=8)
        if auth.get("type") != "auth" or not hmac.compare_digest(str(auth.get("token","")), TOKEN):
            await ws.close(code=1008); return
        await ws.send_json({"type":"ready"})
    except Exception:
        await ws.close(code=1008); return
    master, slave = pty.openpty()
    env=os.environ.copy(); env.update({"TERM":"xterm-256color","COLORTERM":"truecolor"})
    pid=os.fork()
    if pid == 0:
        os.close(master); os.setsid(); fcntl.ioctl(slave,termios.TIOCSCTTY,0)
        for fd in (0,1,2): os.dup2(slave,fd)
        if slave>2: os.close(slave)
        shell=os.environ.get("SHELL","/bin/bash")
        os.execvpe(shell,[shell,"-l"],env)
    os.close(slave); os.set_blocking(master,False)
    async def read_pty():
        while True:
            try:
                ready,_,_=select.select([master],[],[],0.1)
                if ready:
                    data=os.read(master,4096)
                    if not data: break
                    await ws.send_text(data.decode("utf-8","replace"))
            except (OSError,WebSocketDisconnect): break
            await asyncio.sleep(0)
    reader=asyncio.create_task(read_pty())
    try:
        while True:
            msg=await ws.receive_json()
            if msg.get("type")=="input": os.write(master,str(msg.get("data",""))[:8192].encode())
            elif msg.get("type")=="resize":
                cols=max(20,min(int(msg.get("cols",100)),300)); rows=max(5,min(int(msg.get("rows",30)),120))
                fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack("HHHH",rows,cols,0,0))
    except WebSocketDisconnect: pass
    finally:
        reader.cancel()
        try: os.close(master)
        except OSError: pass
        try: os.kill(pid,signal.SIGHUP)
        except ProcessLookupError: pass
