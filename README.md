# Vps — Self-hosted control panel

An original, modular server platform bringing app hosting, Docker, storage, and terminal into one dashboard. Inspired by ideas from Coolify, Dokploy, CasaOS, Portainer, and File Browser—not a clone of any one panel.

## Current repository status

- **Dashboard:** responsive Next.js UI prototype; metrics/app rows are sample data.
- **Terminal UI:** xterm.js at `/terminal`.
- **Agent:** experimental Python PTY WebSocket bridge under `agent/`. It can open a real shell when run locally with the right configuration, but is not production hardened or multi-user ready.
- **Not implemented yet:** production authentication/roles, live metrics API, Docker lifecycle API, file manager backend, Git deploy engine, domains/TLS automation, database provisioning, backups, audit system, secure agent tunnel/installer.

Please don't treat demo metrics or app cards as live server state.

## Frontend
```bash
npm install
npm run dev
```
Open `http://localhost:3000`. Terminal UI: `http://localhost:3000/terminal`.

## Experimental local terminal agent
Read [agent/README.md](agent/README.md) and [Terminal & Agent architecture](docs/TERMINAL-AND-AGENT.md) first. Use a dedicated non-root Linux account, a strong secret, and loopback binding. Do not expose the prototype directly to the internet. Production needs TLS/WSS, short-lived tickets, per-user permissions, session auditing, limits, and a secure outbound agent tunnel.

## Architecture and roadmap
- [Product roadmap](ROADMAP.md)
- [Terminal and agent security design](docs/TERMINAL-AND-AGENT.md)

## Planned platform modules
Overview/live metrics · Applications/Git deploy · Docker/Compose · Terminal · scoped File Manager · Domains/reverse proxy/SSL · Databases · Storage/volumes · Networking · Backups/restore · Team/RBAC · API tokens · audit logs · notifications · agent updates.

## Security baseline
Never execute arbitrary shell commands from unauthenticated endpoints. Never expose Docker's socket to the public web app. All agent operations must validate permissions and inputs; file access must be confined to configured roots; secrets must remain server-side and never be committed.
