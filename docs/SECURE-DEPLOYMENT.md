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
Review and run `sudo bash deploy/bootstrap-ubuntu.sh` on Ubuntu/Debian. It installs build prerequisites, Node 22, Tailscale, creates 2 GiB swap if RAM is under 2 GiB, and configures UFW. It asks for the actual SSH port and adds that allow rule BEFORE enabling UFW. Confirm SSH works in a second session before enabling a firewall on a remote server.

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

## SSH hardening (manual, avoid lockout)
Bootstrap installs and enables Fail2ban and unattended-upgrades. Before changing SSH:
1. Keep your current SSH session open and open a SECOND session.
2. On your phone/laptop, create an SSH key (Ed25519 recommended) and add its public key to the VPS user's `~/.ssh/authorized_keys`; permissions: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`.
3. Verify key login in a NEW session: `ssh -i <private-key> -p <port> user@server`. Do not proceed until it succeeds.
4. Create `/etc/ssh/sshd_config.d/99-vps-hardening.conf`:
   ```
   PubkeyAuthentication yes
   PasswordAuthentication no
   KbdInteractiveAuthentication no
   PermitRootLogin no
   ```
   (If your provider requires root or password auth for recovery, adjust deliberately.)
5. Validate config: `sudo sshd -t`; then reload (not stop): `sudo systemctl reload ssh` (some distros name it `sshd`). Test another new key session before closing old sessions.
6. Check Fail2ban: `sudo fail2ban-client status sshd`. Check unattended upgrades: `systemctl status unattended-upgrades`; logs: `sudo journalctl -u unattended-upgrades`. Review reboot notices; no automatic reboot is configured.

## HTTPS and terminal
The browser terminal selects `wss://` automatically whenever the dashboard origin is HTTPS, and `ws://` for HTTP. WSS needs a TLS-enabled agent endpoint reachable on the same hostname/port (or a private TLS reverse proxy). Plain Uvicorn on port 8787 is **not TLS**. If using HTTPS, do not point `wss://` at plain HTTP Uvicorn; configure a TLS listener/proxy on the Tailscale network and set the agent WebSocket URL accordingly. Keep that endpoint private and token-authenticated.

## Secret inventory / rotation
This repository contains **no generated live credentials**. The strings in env examples/docs are placeholders. Generate these on the VPS (never commit them):
- `VPS_AGENT_TOKEN`: `openssl rand -hex 32`; same random value in root-owned `/etc/vps/agent.env` and `/etc/vps/panel.env`. Rotate by generating a new value, updating both files, chmod 600, then restart both services.
- `PANEL_PASSWORD`: `openssl rand -hex 32`; only in `/etc/vps/panel.env`. Rotate by replacing it and restarting panel; clear browser saved Basic Auth credentials/session if needed.
- `PANEL_USERNAME`: set to your chosen admin name in panel.env (not secret by itself; change if desired).
- SSH private key: generated and kept ONLY on your phone/computer; never upload it to GitHub or the VPS. Rotate/revoke by removing old public key from authorized_keys and adding a new key.
- Tailscale identity/device authorization: handled by your Tailscale account; revoke lost devices in Tailscale admin.
No credentials have been generated or stored by this repository automation. If any token/password was ever pasted into a chat, terminal log, or committed file, treat it as compromised and rotate it immediately.
