#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/kaliworkbench"
SERVICE_SRC="${1:-./install/kaliworkbench.service}"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv python3-pip nodejs npm git tshark bluez libpcap-dev libcap2-bin

id -u kaliworkbench >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin kaliworkbench
mkdir -p "$APP_DIR" /var/lib/kaliworkbench
chown -R kaliworkbench:kaliworkbench "$APP_DIR" /var/lib/kaliworkbench

if [[ ! -d "$APP_DIR/backend" ]]; then
  echo "Copy the repository to $APP_DIR before running this script." >&2
  exit 1
fi

cd "$APP_DIR/backend"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"

setcap cap_net_raw,cap_net_admin+eip "$(command -v tshark)" || true
setcap cap_net_raw,cap_net_admin+eip "$APP_DIR/backend/.venv/bin/python" || true

install -m 0644 "$SERVICE_SRC" /etc/systemd/system/kaliworkbench.service
systemctl daemon-reload
systemctl enable --now kaliworkbench.service
systemctl status kaliworkbench.service --no-pager
