#!/usr/bin/env bash
set -euo pipefail

[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "Run with sudo."; exit 1; }
ROOT="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DEPS=0
[[ "${1:-}" == "--install-deps" ]] && INSTALL_DEPS=1

install_deps() {
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      python3 nfs-common cifs-utils open-iscsi openssh-client sshpass qemu-utils
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y python3 nfs-utils cifs-utils iscsi-initiator-utils openssh-clients sshpass qemu-img
  elif command -v yum >/dev/null 2>&1; then
    yum install -y python3 nfs-utils cifs-utils iscsi-initiator-utils openssh-clients qemu-img
  else
    echo "Automatic dependency installation is not supported on this distribution." >&2
    echo "Install Python 3, NFS, CIFS, iSCSI, OpenSSH client, sshpass and qemu-img manually." >&2
    exit 2
  fi
}

if (( INSTALL_DEPS )); then
  echo "Installing supported core dependencies..."
  install_deps
fi

echo "Installing LINUX BACKUP MANAGER - VIRTUALIZATION & DISASTER RECOVERY CENTER"
install -d -m 755 /opt/lbm-vdrc
rm -rf /opt/lbm-vdrc/lbm_vdrc
cp -a "$ROOT/lbm_vdrc" /opt/lbm-vdrc/

cat >/usr/local/bin/lbm-vdrc <<'WRAP'
#!/usr/bin/env bash
export PYTHONPATH="/opt/lbm-vdrc${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m lbm_vdrc.cli "$@"
WRAP
chmod 755 /usr/local/bin/lbm-vdrc

install -d -m 700 /etc/lbm-vdrc /var/lib/lbm-vdrc /run/lbm-vdrc
install -d -m 755 /var/log/lbm-vdrc /mnt/lbm-vdrc
if [[ ! -f /etc/lbm-vdrc/secrets.json ]]; then
  echo '{}' >/etc/lbm-vdrc/secrets.json
fi
chmod 600 /etc/lbm-vdrc/secrets.json

echo
echo "Installed successfully."
echo
echo "Core Debian/Ubuntu dependencies:"
echo "  python3 nfs-common cifs-utils open-iscsi openssh-client sshpass qemu-utils"
echo "Optional connectors:"
echo "  govc    - VMware ESXi/vCenter"
echo "  sshpass - required by the interactive password-only Proxmox cold-copy wizard"
echo
echo "Start the ANSI interface:"
echo "  sudo lbm-vdrc"
echo
echo "Run diagnostics:"
echo "  sudo lbm-vdrc doctor"
echo
/usr/local/bin/lbm-vdrc --version
