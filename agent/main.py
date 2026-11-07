"""Experimental authenticated local PTY WebSocket bridge. Not production-ready."""
import asyncio, hmac, os, pty, select, struct, termios, fcntl
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

app = FastAPI(title="Vps Agent", docs_url=None, redoc_url=None)
TOKEN = os.environ.get("VPS_AGENT_TOKEN", "")
ORIGIN = os.environ.get("VPS_AGENT_ORIGIN", "")
HOST = os.environ.get("VPS_AGENT_HOST", "127.0.0.1")
PORT = int(os.environ.get("VPS_AGENT_PORT", "8787"))

@app.get("/health")
def health():
    return {"status":"ok","agent":"experimental","terminal":"enabled"}

@app.websocket("/terminal")
async def terminal(ws: WebSocket):
    origin = ws.headers.get("origin", "")
    auth = ws.headers.get("authorization", "")
    # Browser WebSocket cannot set Authorization; use a secure reverse proxy to inject it.
    if not TOKEN or not hmac.compare_digest(auth.removeprefix("Bearer "), TOKEN) or (ORIGIN and origin != ORIGIN):
        await ws.close(code=1008); return
    await ws.accept()
    master, slave = pty.openpty()
    env = os.environ.copy(); env.update({"TERM":"xterm-256color","COLORTERM":"truecolor"})
    pid = os.fork()
    if pid == 0:
        os.close(master); os.setsid(); fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        for fd in (0,1,2): os.dup2(slave,fd)
        if slave > 2: os.close(slave)
        os.execvpe(os.environ.get("SHELL","/bin/bash"), [os.environ.get("SHELL","/bin/bash"),"-l"], env)
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
            if msg.get("type")=="input":
                data=str(msg.get("data",""))[:8192]
                os.write(master,data.encode())
            elif msg.get("type")=="resize":
                cols=max(20,min(int(msg.get("cols",100)),300)); rows=max(5,min(int(msg.get("rows",30)),120))
                fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack("HHHH",rows,cols,0,0))
    except WebSocketDisconnect: pass
    finally:
        reader.cancel()
        try: os.close(master)
        except OSError: pass
        try: os.kill(pid, signal.SIGHUP)
        except Exception: pass
