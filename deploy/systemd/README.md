# Vps service templates

These are examples for a Debian/Ubuntu installation where the checkout is
`/opt/vps` and the service account is `vpsagent`.

- Copy `vps-agent.service` to `/etc/systemd/system/vps-agent.service`.
- Copy `vps-panel.service` to `/etc/systemd/system/vps-panel.service`.
- Create root-owned `/etc/vps/agent.env` (chmod 600) containing
  `VPS_AGENT_TOKEN`, exact `VPS_AGENT_ORIGIN`, and `VPS_SITES_ROOT=/opt/vps/sites`.
- Create root-owned `/etc/vps/panel.env` (chmod 600) with
  `VPS_AGENT_URL=http://127.0.0.1:8787` and the same `VPS_AGENT_TOKEN`.
- Build the dashboard as the deployment user before enabling the panel unit.
- `sudo systemctl daemon-reload`, then `sudo systemctl enable --now vps-agent vps-panel`.

The agent stays loopback-only. Do not open port 8787 in any firewall. If Docker
controls are desired, Docker socket access is root-equivalent; review the security
trade-off before adding the agent to the docker group.

Restart:
- Agent: `sudo systemctl restart vps-agent`
- Dashboard: `sudo systemctl restart vps-panel`
- Logs: `sudo journalctl -u vps-agent -f` or `sudo journalctl -u vps-panel -f`

These templates assume npm is at `/usr/bin/npm`; change ExecStart to the actual
Node/npm path installed on the host if needed (e.g. NodeSource).
