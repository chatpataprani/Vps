# Secure VPS deployment (phone + Tailscale)

## Threat model / network
The dashboard has no native user/role system yet. It is protected by HTTP Basic auth middleware and MUST also be private. Do not publish TCP 3000 or 8787 on the public interface. Do not use Caddy to proxy the control panel.

Use the VPS Tailscale IPv4 (100.x.y.z) for both services:
- Panel URL on phone: `http://100.x.y.z:3000`\n- Set `PANEL_BIND_IP=100.x.y.z` in `/etc/vps/panel.env` and `VPS_AGENT_BIND_IP=100.x.y.z` in `/etc/vps/agent.env` (systemd units default to loopback for safety).
- Agent URL in terminal: `ws://100.x.y.z:8787/terminal`
- `VPS_AGENT_ORIGIN` must exactly match the URL in the phone browser, including scheme, host and port, e.g. `http://100.x.y.z:3000` (no trailing slash).
- `VPS_AGENT_URL` for the Next server is `http://100.x.y.z:8787`.
- Agent Uvicorn bind: `--host 100.x.y.z --port 8787`; panel bind: `next start --hostname 100.x.y.z --port 3000`. Replace the address with the VPS's actual Tailscale IP. Restart services after changing it.
- If the dashboard is opened using a different hostname/IP, update `VPS_AGENT_ORIGIN` to that exact origin and restart the agent. Browser terminal is direct WebSocket and must reach the agent over Tailscale.
- On Android, install Tailscale from Play Store, sign into the same tailnet, enable its VPN toggle, then open the panel URL above. Keep Tailscale connected while using the terminal.

## Initial setup
Review and run `sudo bash deploy/bootstrap-ubuntu.sh` on Ubuntu/Debian. It installs build prerequisites, Node 20, Tailscale, creates 2 GiB swap if RAM is under 2 GiB, and configures UFW. It asks for the actual SSH port and adds that allow rule BEFORE enabling UFW. Confirm SSH works in a second session before enabling a firewall on a remote server.

UFW public rules: SSH + 80 + 443 only. TCP 3000/8787 are permitted only on `tailscale0`. Verify with `sudo ufw status numbered`. Do not add public 3000/8787 rules.

Install Docker only if you need container management/static hosting. Docker-group membership is root-equivalent.

## Panel credentials
Set server-only values in `/etc/vps/panel.env`:
```env
PANEL_USERNAME=admin
PANEL_PASSWORD=<long-random-password>
VPS_AGENT_URL=http://100.x.y.z:8787
VPS_AGENT_TOKEN=<same-long-random-token-as-agent>
```
Generate values with `openssl rand -hex 32`. Restrict file: `sudo chmod 600 /etc/vps/panel.env`. Never use NEXT_PUBLIC_ for these values or commit them. Middleware fails closed (503) if credentials are missing. HTTP Basic auth is not a replacement for proper multi-user RBAC; use it only with Tailscale/private access and HTTPS for public-facing deployments.

Agent `/etc/vps/agent.env`:
```env
VPS_AGENT_TOKEN=<same-token>
VPS_AGENT_ORIGIN=http://100.x.y.z:3000
VPS_SITES_ROOT=/opt/vps/sites
```
`VPS_AGENT_ORIGIN` is exact browser dashboard origin. Protect both env files with chmod 600. Run `sudo systemctl daemon-reload && sudo systemctl restart vps-agent vps-panel` after setting these bind addresses. Agent is authenticated by Bearer token for REST and first-message token for WebSocket.

## Build safely
Check memory before building: `free -h`. If RAM <2 GiB and swap is absent, bootstrap creates 2 GiB swap. Install `build-essential` and `python3-dev`. Then:
```bash
npm ci
npm run build
```
Builds can still be slow on tiny VPS; build locally/CI and deploy artifacts if memory is insufficient.

## Static sites only
The Docker Caddy service is for static HTML/CSS/JS sites only. Site folders live at `/opt/vps/sites/<domain>`; Websites UI uses authenticated panel proxy -> agent `/api/sites`. Caddy serves those folders and handles their public HTTP/HTTPS domains. Do NOT put panel or agent routes into Caddy. Panel/agent remain on Tailscale.

After DNS A/AAAA points to VPS and public 80/443 are allowed, copy `hosting/Caddyfile.example` to `hosting/Caddyfile`, add a site block per domain, then start/reload Caddy. Never mount Docker socket into Caddy or public frontend.
