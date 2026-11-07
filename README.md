# Vps — Self-hosted control panel

A modular server platform for apps, Docker, static sites, storage, and terminal. Inspired by ideas from Coolify, Dokploy, CasaOS, Portainer, and File Browser—not a clone.

## Status (prototype)
- Next.js responsive dashboard and xterm terminal UI.
- Python agent with authenticated REST endpoints for system metrics, Docker, static site folders, and PTY.
- Websites page now uses the agent's `/api/sites` through a server-side allowlisted proxy.
- File manager supports confined browsing, syntax-highlighted code editing (Monaco; language auto-detection/manual selection), folder/file creation, saving, 8 MiB binary upload/download, and individual file deletion.
- Applications page can clone public GitHub/GitLab/Codeberg HTTPS repos with Dockerfiles, build images, run resource-limited managed containers, inspect logs, restart/stop/start, and delete.
- HTTP Basic gate is enabled via `PANEL_USERNAME` and `PANEL_PASSWORD`; it fails closed if unset.
- This is still a single-admin prototype—not production multi-user RBAC, audited terminal sessions, or a full app deployment platform. Never treat sample dashboard cards as real server state.

## Secure remote access (important)
**Do not expose TCP 3000 or 8787 publicly.** Use Tailscale and bind panel/agent to the VPS's Tailscale IP. Connect Android to the same tailnet, then open `http://<VPS-TAILSCALE-IP>:3000`. Terminal URL is `ws://<VPS-TAILSCALE-IP>:8787/terminal`. Set `VPS_AGENT_ORIGIN` to the exact dashboard origin you open (scheme + IP/hostname + port). Keep 3000/8787 restricted to `tailscale0`.

Follow [Secure deployment and phone access](docs/SECURE-DEPLOYMENT.md) and [agent setup](agent/DEPLOYMENT.md). The optional [Ubuntu/Debian bootstrap](deploy/bootstrap-ubuntu.sh) checks Ubuntu 24.04+/Debian 12+ and Python 3.11+, installs Node.js 22 LTS or newer and Tailscale, adds 2 GiB swap when RAM <2 GiB, and configures UFW with SSH allowed before enable. Review it first and confirm your real SSH port.

## Run frontend locally
```bash
npm install
npm run dev
```
Open `http://localhost:3000`. Configure Basic auth env variables before serving remotely.

## Applications / Git deployments
- Only public HTTPS Git repositories hosted on GitHub, GitLab, or Codeberg are accepted. A repository must include a Dockerfile.
- Containers are limited to 512 MiB RAM, 1 CPU, and 256 PIDs, and their host ports bind to `127.0.0.1` (not public). Deployment forms accept runtime `KEY=VALUE` environment variables (keep secrets private). Configure Caddy/reverse proxy explicitly to publish a domain with TLS.
- Git builds execute repository Dockerfiles; only trusted administrators should have access. Build contexts and Docker access are privileged.

## File manager
- The agent file API is confined to `VPS_FILES_ROOT` (defaults to `./sites`); it rejects traversal and symlinks.
- Directory deletion and binary editing are intentionally disabled. Configure the root to a dedicated data directory when possible.

## Static website hosting
Docker Caddy is **static-site-only**. It serves folders under `sites/<domain>`, and can provide HTTPS for public domains with DNS and ports 80/443. It must not proxy the panel or agent. See [hosting README](hosting/README.md).

## Security baseline
- Never expose the agent or panel ports publicly.
- Keep tokens and panel credentials server-side in root-owned/600 env files; no `NEXT_PUBLIC_` secrets.
- Agent APIs require Bearer auth; the terminal requires a token handshake and exact origin.
- Docker socket access is root-equivalent. Only grant it to trusted operators.
- File/site paths must stay within configured roots. Destructive operations require explicit confirmation.
