#!/usr/bin/env bash
set -euo pipefail
[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "Run with sudo."; exit 1; }
systemctl list-unit-files 'lbm-vdrc-job-*.timer' --no-legend 2>/dev/null | awk '{print $1}' | while read -r u; do [[ -n "$u" ]] && systemctl disable --now "$u" || true; done
rm -f /etc/systemd/system/lbm-vdrc-job-*.timer /etc/systemd/system/lbm-vdrc-job-*.service
systemctl daemon-reload || true
rm -f /usr/local/bin/lbm-vdrc /usr/local/bin/vmmigration
rm -rf /opt/lbm-vdrc /opt/vmmigration
echo "Program files removed. Configuration, secrets, logs and backups were preserved."
