# Real terminal and server agent

## Requirement
The Vps terminal must be a real interactive shell on the user's own Linux host—not a fake command prompt or browser-only simulation.

## Architecture
```
Browser (xterm.js)
  └─ HTTPS/WSS → Vps API (authentication + authorization)
       └─ private agent channel → Vps Linux Agent
            └─ PTY session (bash/zsh) under a restricted OS identity
```

- Browser terminal: xterm.js + WebSocket; resize support, reconnect handling, clipboard, scrollback.
- API: authenticate sessions, authorize server access, issue short-lived terminal tickets, rate-limit and audit.
- Agent: outbound authenticated connection to API (works behind NAT); creates PTY sessions and streams input/output.
- Shell: dedicated non-root user by default; optional admin shell only after explicit secure configuration.
- Isolation: per-user/session limits, idle timeout, max concurrent sessions, command/session audit metadata.
- Transport: TLS/WSS, agent identity and key rotation. Never expose an unauthenticated terminal endpoint.
- Never run shell commands directly from frontend code or accept arbitrary commands through a public REST endpoint.
- Never expose or mount Docker socket into the public web frontend.

## Agent capabilities (permissioned)
- Live system metrics and host info
- Docker inventory, inspect, start/stop/restart, logs and Compose stacks
- Scoped file operations with path traversal protection
- App deployment/build jobs
- Domain/reverse-proxy and TLS status
- Backup jobs and database lifecycle
- Terminal PTY sessions
- Health checks, agent version and upgrade status

Every operation must be validated by the agent, checked against permissions, and recorded in audit logs. File access must be restricted to configured roots unless an administrator explicitly grants broader access.
