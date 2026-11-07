# Vps Agent (experimental terminal bridge)

This is a **development-only** PTY bridge. Do not expose it directly to the internet or use it as a production multi-user terminal service. It requires a strong bearer token and Origin check, but production still needs per-user authorization, short-lived tickets, audit logging, quotas, and an outbound agent tunnel.

## Run locally
1. Create a dedicated, non-root Linux user for the agent.
2. Install Python 3.11+ and dependencies: `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`, generate a random token, set your exact panel origin.
4. Export the variables in your shell (this sample does not load .env automatically).
5. Run `uvicorn main:app --host 127.0.0.1 --port 8787`.
6. Use an authenticated reverse proxy/tunnel for WSS. Never bind publicly in this prototype.

## Browser protocol
Client sends JSON `{"type":"input","data":"..."}` or `{"type":"resize","cols":120,"rows":30}`. Agent streams raw PTY output as text frames.

The shell runs as the OS account running this process. **Do not run this process as root.**


## Static website API (prototype)
The agent mounts `/api/sites` endpoints. Set `VPS_SITES_ROOT` to the same directory mounted read-only by Caddy (e.g. `../sites`). Requests require `Authorization: Bearer <VPS_AGENT_TOKEN>`.

- `GET /api/sites` — list site folders
- `POST /api/sites` JSON `{"domain":"example.com","title":"My site"}` — create folder and starter index.html
- `DELETE /api/sites/example.com` — delete folder (destructive)

Keep agent bound to loopback/private network. This prototype uses a shared agent token; do not expose it to browser JavaScript or use it as a multi-user production authorization model. Production panel should issue scoped, short-lived tickets via a backend gateway.
