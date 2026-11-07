#!/usr/bin/env bash
set -euo pipefail
# Ubuntu/Debian first-run prep. Review before running as root.
[[ $EUID -eq 0 ]] || { echo "Run with sudo."; exit 1; }
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git curl ca-certificates openssl python3 python3-venv python3-dev build-essential ufw fail2ban unattended-upgrades docker.io docker-compose-v2
# Keep Next.js builds from OOMing on small machines: create 2 GiB swap only below 2 GiB RAM.
ram_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
if (( ram_kb < 2097152 )) && ! swapon --show=NAME | grep -q '^/swapfile$'; then
  echo "RAM is below 2 GiB; creating 2 GiB swap..."
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
  chmod 600 /swapfile; mkswap /swapfile; swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
# Install Node 22 from NodeSource (required for current Next.js project).
if ! command -v node >/dev/null || [[ $(node -p 'Number(process.versions.node.split(".")[0])') -lt 20 ]]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
fi
# Install/start Docker before the Vps agent; enable at boot.\nsystemctl enable --now docker\n\n# Tailscale install script is upstream maintained.
if ! command -v tailscale >/dev/null; then curl -fsSL https://tailscale.com/install.sh | sh; fi
# Firewall: add SSH first (custom SSH port supported), then web ports, then tailnet-only panel/agent.
read -r -p "SSH port (default 22; confirm your actual sshd port): " SSH_PORT
SSH_PORT=${SSH_PORT:-22}
ufw allow "${SSH_PORT}/tcp" comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow in on tailscale0 to any port 3000 proto tcp comment 'Vps panel via Tailscale'
ufw allow in on tailscale0 to any port 8787 proto tcp comment 'Vps agent via Tailscale'
ufw default deny incoming
ufw default allow outgoing
echo "Rules added. SSH allow is already in place. Enabling UFW now."
ufw --force enable
ufw status verbose
echo "Prep complete. Join Tailscale: sudo tailscale up"
