# Vps — Product roadmap

Vps is an original, modern self-hosting and server management platform. It is not a Pterodactyl clone. The product should combine the strongest ideas from Coolify, Dokploy, CasaOS, Portainer, File Browser, and secure web-terminal projects into one coherent experience.

## Product principles
- One clean dashboard for infrastructure, apps, containers, files, domains, and terminal.
- Mobile-first responsive UX; desktop gets a full workspace layout.
- Real server data only when an authenticated agent is connected. Clearly label demo data.
- Secure-by-default: least privilege, scoped file roots, audited actions, session controls, TLS, and no public Docker socket.
- Keep modules independent and usable; avoid fake buttons presented as working features.

## Modules
1. Overview: live CPU/RAM/disk/network metrics, uptime, health, recent events.
2. Applications: Git repository deployments, build/deploy history, environment variables, logs, restart/rollback.
3. Containers: Docker inventory, lifecycle, inspect, logs, resource limits, compose stacks.
4. Terminal: browser terminal over authenticated WebSocket to a restricted server agent; per-user sessions and audit trail.
5. Files: scoped file browser, upload/download, editor, archive extraction, permissions.
6. Domains & TLS: domain routing, reverse proxy, certificate status/renewal.
7. Databases: provision/manage supported database containers, credentials, backups.
8. Storage: disk volumes, mount points, usage and cleanup.
9. Networking: ports, service routes, firewall status (safe read-first controls).
10. Backups: scheduled snapshots, restore workflow, retention.
11. Team & security: roles, API tokens, SSH keys, audit logs, 2FA.
12. Settings: agent connection, notifications, preferences, system updates.

## Delivery phases
- Phase 1: complete responsive frontend, reusable layout, real navigation, empty/loading/error states, mock mode clearly indicated.
- Phase 2: authenticated API and Linux agent; live system metrics and safe actions.
- Phase 3: Docker and file APIs, terminal WebSocket.
- Phase 4: Git deployments, domains/TLS, databases, backups.
- Phase 5: roles, audit, hardening, installation/update tooling.

## Security boundaries
Never execute arbitrary shell commands from unauthenticated endpoints. Do not expose Docker's socket to the browser or public API. Terminal and file APIs must enforce identity, authorization, quotas, path confinement, and audit logging. Production secrets must be stored server-side and never committed.
