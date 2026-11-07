# Vps Static Website Hosting (Docker + Caddy)

This is a starter deployment for hosting HTML/CSS/JS sites on a Linux VPS. It is independent of the experimental terminal agent.

## What it provides
- Host multiple static sites from folders under `sites/`
- Caddy reverse proxy and automatic HTTPS (requires public DNS pointing to the VPS and ports 80/443 open)
- Docker Compose deployment and persistent site files
- No arbitrary shell exposed through the web UI

## Quick start (Ubuntu/Debian VPS)
1. Install Docker Engine + Compose plugin using Docker's official installation guide.
2. Clone this repository on the VPS.
3. Copy `hosting/Caddyfile.example` to `hosting/Caddyfile` and replace domains.
4. Create folders, e.g. `sites/example.com/`, and put `index.html` inside.
5. Run from repository root: `docker compose -f hosting/compose.yml up -d`.
6. Point DNS A/AAAA records to the VPS. Ensure ports 80 and 443 are reachable.

## Add another site
Create `sites/your-domain/`, add HTML assets, add a matching site block to Caddyfile, then reload:
`docker compose -f hosting/compose.yml exec caddy caddy reload --config /etc/caddy/Caddyfile`.

## Important
This is a deployment template—not a finished multi-tenant panel. Do not mount the Docker socket into the public dashboard. For a production UI, site creation must be authorized and validated by a privileged agent with a narrow operation allowlist, per-site quotas, audit logs, and safe path handling.
