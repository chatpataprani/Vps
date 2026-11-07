# Vps — Self-hosted control panel

A custom hosting dashboard inspired by the best open-source self-hosting projects:

- **Coolify / Dokploy:** application deployments, Git-based workflows, domains, logs, container terminal concepts.
- **CasaOS / ReCasaOS:** storage overview, file manager, app dashboard.
- **File Browser:** browser-based file operations.
- **xterm.js:** browser terminal UI (terminal backend must be connected securely).

## Project status

This repository starts with a responsive dashboard UI prototype. Metrics and app entries are demo data until a Linux agent/API is implemented and connected.

## Stack

- Next.js App Router + TypeScript
- Tailwind CSS
- Lucide icons
- Docker Engine + a separate least-privilege server agent (planned)
- WebSocket terminal gateway (planned; never expose Docker socket or host shell directly to the browser)

## Local development

```bash
npm install
npm run dev
```

## Planned modules

- Overview: CPU, memory, disk, uptime
- Applications: deploy, start/stop, logs, domains
- Containers: Docker lifecycle and resource stats
- Files: scoped file browser/upload/download
- Terminal: authenticated WebSocket session
- Domains & TLS
- Databases and backups
- Server settings and audit logs

## Security

A production installation must use authentication, authorization, isolated terminal sessions, path allowlists, command auditing, rate limits, TLS, and a restricted agent. Do not run arbitrary shell commands from unauthenticated HTTP endpoints. Never mount Docker socket into a public web app.
