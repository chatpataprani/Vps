# Vps — Product roadmap & engineering principles

Vps is an original, cohesive server control plane—not a theme wrapper or clone. Goal: a polished, mobile-friendly dashboard managing real Linux hosts, Docker workloads, websites, files, domains, databases, and interactive terminals.

## Open-source references (learn patterns; don't copy assets/source blindly)
- [Coolify](https://github.com/coollabsio/coolify) — Git deployments, Dockerfile/Compose, databases, domains/TLS, backups, logs and resources. Its control plane connects to servers over SSH and workloads remain standard Docker resources.
- [Dokploy](https://github.com/Dokploy/dokploy) — app workspaces, deployment lifecycle, multi-server architecture, Traefik integration and monitoring.
- [Portainer CE](https://github.com/portainer/portainer) — Docker lifecycle, inspect, logs, exec, images, volumes and networks.
- [ReCasaOS](https://github.com/ReCasaOS/CasaOS) — approachable dashboard, app catalog, storage/files and phone-friendly UI. Independent community distribution; not affiliated with upstream CasaOS.
- [File Browser](https://github.com/filebrowser/filebrowser) — file navigation, uploads/downloads and safe operations.
- [ttyd](https://github.com/tsl0922/ttyd) / [xterm.js](https://github.com/xtermjs/xterm.js) — terminal UI/transport patterns; use PTY + secure gateway, never simulated output.

Respect each project's license, attribution, trademarks and contribution rules. Don't copy proprietary assets or large source blocks.

## UX quality bar
- Responsive from 360px mobile to desktop; mobile drawer, sticky headers and touch-friendly controls.
- Consistent design tokens, spacing, typography, icons, empty/loading/error states, skeletons and toast feedback.
- Dark/light/system themes, keyboard navigation, accessible focus and reduced motion.
- Truthful states: connected, demo, degraded, offline. Never show sample metrics/activity as live.
- Fast pages: pagination, debounced search, streamed logs and safe optimistic actions.
- Every navigation item opens a working page or is explicitly marked Coming soon—no dead buttons.

## Architecture
- Next.js dashboard/control plane; PostgreSQL durable state; queue/events for long-running jobs.
- Server-side sessions + RBAC (owner/admin/operator/read-only), MFA, CSRF protection and audit trail.
- Linux agent on managed hosts; outbound mTLS connection with short-lived scoped operation tickets. No public inbound agent port required.
- Agent capabilities: metrics, Docker Engine API, PTY, scoped filesystem, deployment jobs, proxy/domain status and backup jobs. Strict allowlists/quotas.
- Traefik or Caddy for domains/TLS; Docker Compose as portable workload format.
- Secrets encrypted at rest; never sent to browser logs or committed.
- Background jobs with progress, cancellation, retries, idempotency, logs and notifications.

## Delivery phases
### P0 — Foundation
Responsive shell/mobile drawer; remove fake connected indicators and demo events; clear Demo banner; shared components; loading/error/empty states; CI typecheck/lint/build/audit.
### P1 — Agent + terminal
Ubuntu/Debian installer, least-privilege service user, pairing, health/upgrades; WebSocket gateway, short-lived tickets, Origin checks, rate/concurrency/idle limits, resize/cleanup; per-host/user audited sessions, no root by default.
### P2 — Docker + files
Live containers/images/volumes/networks, lifecycle, inspect, logs, exec and Compose; root-confined file manager with upload/download/rename/move/delete, confirmations and traversal/symlink protection.
### P3 — Hosting
Git deploys, Dockerfile/Compose/static/Node/Python/PHP templates, build logs/rollback; domains, reverse proxy, automatic TLS, health checks; env and secrets.
### P4 — Databases & operations
Database provisioning, credentials, backups/restores/schedules; multi-server metrics, alerts, notifications/audit; roles, API tokens and webhooks.

## Definition of done
A feature is complete only with a working backend, authorization, validation, tests, error handling, audit coverage, responsive UI and truthful status. UI mocks must be clearly labeled. Terminal and file operations must never expose unauthenticated arbitrary host commands.
