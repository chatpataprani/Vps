# Vps Agent configuration

The Next.js control panel can proxy agent operations server-side. Add these variables
to the panel deployment (never use NEXT_PUBLIC_ for secrets):

- `VPS_AGENT_URL`: private/reachable agent base URL, e.g. `http://127.0.0.1:8787`
- `VPS_AGENT_TOKEN`: same strong random token as the agent

The proxy is allowlisted: system metrics, Docker status/list/logs and start/stop/restart.
The token is only read by server route handlers and is never returned to the browser.
For multiple hosts, add a database-backed server registry and per-user authorization
before exposing these endpoints to operators.

Agent setup:
1. Use Ubuntu/Debian and create a dedicated non-root account.
2. Install Python 3.11+, Docker Engine (optional), then `pip install -r requirements.txt`.
3. Generate a strong token (e.g. `openssl rand -hex 32`); set `VPS_AGENT_TOKEN`.
4. Set `VPS_AGENT_ORIGIN` to the exact panel origin for WebSocket terminal checks.
5. Keep the agent bound to loopback/private network; connect over private networking or
   an authenticated tunnel. Do not publish port 8787 to the internet.
6. Docker API requires access to the Docker socket. Docker-group membership is root-equivalent;
   grant it only to trusted administrators and do not expose raw Docker APIs publicly.

The browser terminal is a separate direct WebSocket connection and currently uses a
shared development token. It is not multi-user production auth; use a gateway-issued,
short-lived per-session ticket before production deployment.
