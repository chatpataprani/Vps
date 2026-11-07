# Vps — Self-hosted control panel

A modular server platform for apps, Docker, static sites, storage, and terminal. Inspired by ideas from Coolify, Dokploy, CasaOS, Portainer, and File Browser—not a clone.

## Status (prototype)
- Next.js responsive dashboard and xterm terminal UI.
- Python agent with authenticated REST endpoints for system metrics, Docker, static site folders, and PTY.
- Websites page now uses the agent's `/api/sites` through a server-side allowlisted proxy.
- HTTP Basic gate is enabled via `PANEL_USERNAME` and `PANEL_PASSWORD`; it fails closed if unset.
- This is still a single-admin prototype—not production multi-user RBAC, audited terminal sessions, or a full app deployment platform. Never treat sample dashboard cards as real server state.

## Secure remote access (important)
**Do not expose TCP 3000 or 8787 publicly.** Use Tailscale and bind panel/agent to the VPS's Tailscale IP. Connect Android to the same tailnet, then open `http://<VPS-TAILSCALE-IP>:3000`. Terminal URL is `ws://<VPS-TAILSCALE-IP>:8787/terminal`. Set `VPS_AGENT_ORIGIN` to the exact dashboard origin you open (scheme + IP/hostname + port). Keep 3000/8787 restricted to `tailscale0`.

Follow [Secure deployment and phone access](docs/SECURE-DEPLOYMENT.md) and [agent setup](agent/DEPLOYMENT.md). The optional [Ubuntu bootstrap](deploy/bootstrap-ubuntu.sh) installs prerequisites, Node 20, Tailscale, adds 2 GiB swap when RAM <2 GiB, and configures UFW with SSH allowed before enable. Review it first and confirm your real SSH port.

## Run frontend locally
```bash
npm install
npm run dev
```
Open `http://localhost:3000`. Configure Basic auth env variables before serving remotely.

## Static website hosting
Docker Caddy is **static-site-only**. It serves folders under `sites/<domain>`, and can provide HTTPS for public domains with DNS and ports 80/443. It must not proxy the panel or agent. See [hosting README](hosting/README.md).

## Security baseline
- Never expose the agent or panel ports publicly.
- Keep tokens and panel credentials server-side in root-owned/600 env files; no `NEXT_PUBLIC_` secrets.
- Agent APIs require Bearer auth; the terminal requires a token handshake and exact origin.
- Docker socket access is root-equivalent. Only grant it to trusted operators.
- File/site paths must stay within configured roots. Destructive operations require explicit confirmation.
