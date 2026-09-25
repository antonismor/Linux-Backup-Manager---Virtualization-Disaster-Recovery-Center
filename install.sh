#!/usr/bin/env bash
set -euo pipefail

[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "Run with sudo."; exit 1; }
ROOT="$(cd "$(dirname "$0")" && pwd)"
PREFIX="/opt/vmmigration"
BIN="$PREFIX/vmmigration"

echo "════════════════════════════════════════════════════════════════"
echo " VM MIGRATION CENTER"
echo " Design and Development by : antonios.mortos@oultook.com"
echo "════════════════════════════════════════════════════════════════"
echo

install_deps() {
  echo "[1/4] Detecting package manager and installing dependencies..."
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      python3 python3-venv python3-pip build-essential patchelf ccache \
      openssh-client sshpass qemu-utils rsync curl ca-certificates \
      nfs-common cifs-utils open-iscsi zstd tar gzip
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y \
      python3 python3-pip gcc gcc-c++ make patchelf ccache \
      openssh-clients sshpass qemu-img rsync curl ca-certificates \
      nfs-utils cifs-utils iscsi-initiator-utils zstd tar gzip
  elif command -v yum >/dev/null 2>&1; then
    yum install -y \
      python3 python3-pip gcc gcc-c++ make patchelf \
      openssh-clients sshpass qemu-img rsync curl ca-certificates \
      nfs-utils cifs-utils iscsi-initiator-utils zstd tar gzip
  elif command -v zypper >/dev/null 2>&1; then
    zypper --non-interactive install \
      python3 python3-pip gcc gcc-c++ make patchelf \
      openssh sshpass qemu-tools rsync curl ca-certificates \
      nfs-client cifs-utils open-iscsi zstd tar gzip
  elif command -v pacman >/dev/null 2>&1; then
    pacman -Sy --noconfirm --needed \
      python python-pip base-devel patchelf ccache \
      openssh sshpass qemu-img rsync curl ca-certificates \
      nfs-utils cifs-utils open-iscsi zstd tar gzip
  elif command -v apk >/dev/null 2>&1; then
    apk add --no-cache \
      python3 py3-pip py3-virtualenv build-base patchelf \
      openssh-client-default sshpass qemu-img rsync curl ca-certificates \
      nfs-utils cifs-utils open-iscsi zstd tar gzip
  else
    echo "Unsupported package manager." >&2
    echo "Supported families: Debian/Ubuntu, RHEL/Rocky/Alma/Fedora, openSUSE/SLES, Arch, Alpine." >&2
    exit 2
  fi
}

install_govc() {
  if command -v govc >/dev/null 2>&1; then
    echo "[2/4] govc already installed: $(command -v govc)"
    return 0
  fi
  echo "[2/4] Installing VMware govc connector..."
  local machine arch api url tmp
  machine="$(uname -m)"
  case "$machine" in
    x86_64|amd64) arch="x86_64" ;;
    aarch64|arm64) arch="arm64" ;;
    *) echo "govc automatic install skipped for architecture: $machine"; return 0 ;;
  esac
  api="https://api.github.com/repos/vmware/govmomi/releases/latest"
  url="$(curl -fsSL "$api" | sed -nE 's/.*"browser_download_url":[[:space:]]*"([^"]*govc_Linux_'"$arch"'\.tar\.gz)".*/\1/p' | head -n1)"
  if [[ -z "$url" ]]; then
    echo "WARNING: Could not resolve latest govc release automatically. ESXi features will report govc as missing." >&2
    return 0
  fi
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN
  curl -fsSL "$url" -o "$tmp/govc.tar.gz"
  tar -xzf "$tmp/govc.tar.gz" -C "$tmp" govc
  install -m 0755 "$tmp/govc" /usr/local/bin/govc
  rm -rf "$tmp"
  trap - RETURN
}

install_binary() {
  echo "[3/4] Installing compiled VM Migration Center..."
  install -d -m 0755 "$PREFIX"
  local candidate=""
  if [[ -x "$ROOT/dist/vmmigration" ]]; then
    candidate="$ROOT/dist/vmmigration"
  else
    echo "No prebuilt binary found. Building locally with Nuitka..."
    chmod +x "$ROOT/build-binary.sh"
    "$ROOT/build-binary.sh"
    candidate="$ROOT/dist/vmmigration"
  fi
  [[ -x "$candidate" ]] || { echo "Binary build failed: $candidate not found." >&2; exit 3; }
  install -m 0755 "$candidate" "$BIN"
  ln -sfn "$BIN" /usr/local/bin/vmmigration
  ln -sfn "$BIN" /usr/local/bin/lbm-vdrc
  rm -rf "$ROOT/.build-vmmigration" || true
}

prepare_state() {
  echo "[4/4] Preparing protected state directories..."
  install -d -m 0700 /etc/lbm-vdrc /var/lib/lbm-vdrc /run/lbm-vdrc
  install -d -m 0755 /var/log/lbm-vdrc /mnt/lbm-vdrc
  if [[ ! -f /etc/lbm-vdrc/secrets.json ]]; then
    printf "{}\n" >/etc/lbm-vdrc/secrets.json
  fi
  chmod 0600 /etc/lbm-vdrc/secrets.json
}

install_deps
install_govc
install_binary
prepare_state

echo
echo "════════════════════════════════════════════════════════════════"
echo " INSTALLATION COMPLETE"
echo " Design and Development by : antonios.mortos@oultook.com"
echo "════════════════════════════════════════════════════════════════"
echo
echo "Start the application with:"
echo
echo "  sudo vmmigration"
echo
echo "Compatibility command also available:"
echo "  sudo lbm-vdrc"
echo
echo "Installed program file:"
echo "  $BIN"
echo
echo "No Python source files are installed under $PREFIX."
echo
/usr/local/bin/vmmigration --version
