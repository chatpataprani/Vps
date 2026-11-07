#!/usr/bin/env bash
set -euo pipefail
# Ubuntu 24.04+ / Debian 12+ first-run prep. Review before running as root.
[[ $EUID -eq 0 ]] || { echo "Run with sudo."; exit 1; }
. /etc/os-release
case "${ID:-}" in
  ubuntu) version_ok=$(dpkg --compare-versions "${VERSION_ID:-0}" ge 24.04 && echo yes || echo no) ;;
  debian) version_ok=$(dpkg --compare-versions "${VERSION_ID:-0}" ge 12 && echo yes || echo no) ;;
  *) version_ok=no ;;
esac
if [[ "$version_ok" != yes ]]; then
  echo "STOP: supported OS is Ubuntu 24.04+ or Debian 12+. Detected ${PRETTY_NAME:-unknown}."; exit 1
fi
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git curl ca-certificates openssl python3 python3-venv python3-dev build-essential ufw fail2ban unattended-upgrades docker.io docker-compose-v2
python_minor=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'; then
  echo "STOP: Python 3.11+ required; detected $python_minor."; exit 1
fi
# Install Node.js 22 LTS (or newer); upgrade Node 20 and older.
node_major=0
if command -v node >/dev/null; then node_major=$(node -p 'Number(process.versions.node.split(".")[0])'); fi
if (( node_major < 22 )); then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
fi
node -v
# Add 2 GiB swap on small hosts to reduce build OOMs.
ram_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
if (( ram_kb < 2097152 )) && ! swapon --show=NAME | grep -q '^/swapfile$'; then
  echo "RAM is below 2 GiB; creating 2 GiB swap..."
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
  chmod 600 /swapfile; mkswap /swapfile; swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
# Install/start Docker before the Vps agent; enable at boot.
systemctl enable --now docker
# Tailscale install script is upstream maintained.
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
