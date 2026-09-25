from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import time
from pathlib import Path

from ..core import STATE, command_exists, history, now_iso, run, safe_name

SSH_OPTIONS = [
    "-o", "BatchMode=no",
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "ConnectTimeout=10",
    "-o", "ServerAliveInterval=15",
    "-o", "ServerAliveCountMax=3",
]


def _require_tools():
    missing = [name for name in ("ssh", "scp", "sshpass") if not command_exists(name)]
    if missing:
        raise RuntimeError(
            "Missing required tool(s) for password-based Proxmox copy: "
            + ", ".join(missing)
            + ". On Debian/Ubuntu run: sudo apt install -y openssh-client sshpass"
        )


def _env(password: str):
    env = os.environ.copy()
    env["SSHPASS"] = password
    return env


def _ssh(host: str, username: str, password: str, remote_command: str, *,
         capture: bool = True, check: bool = True, timeout: int | None = None):
    _require_tools()
    cmd = ["sshpass", "-e", "ssh", *SSH_OPTIONS, f"{username}@{host}", remote_command]
    return run(cmd, env=_env(password), capture=capture, check=check, timeout=timeout)


def _scp_pull(host: str, username: str, password: str, remote_path: str, local_path: Path):
    _require_tools()
    cmd = [
        "sshpass", "-e", "scp", "-p", *SSH_OPTIONS,
        f"{username}@{host}:{remote_path}", str(local_path),
    ]
    return run(cmd, env=_env(password), capture=False, timeout=None)


def _scp_push(host: str, username: str, password: str, local_path: Path, remote_path: str):
    _require_tools()
    cmd = [
        "sshpass", "-e", "scp", "-p", *SSH_OPTIONS,
        str(local_path), f"{username}@{host}:{remote_path}",
    ]
    return run(cmd, env=_env(password), capture=False, timeout=None)


def _json_remote(host: str, username: str, password: str, command: str):
    cp = _ssh(host, username, password, command, timeout=30)
    try:
        return json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Remote command did not return valid JSON from {host}.") from exc


def test_proxmox_host(host: str, username: str, password: str):
    cp = _ssh(
        host, username, password,
        "set -e; printf '__HOST__='; hostname; printf '__PVE__='; pveversion | head -n1",
        timeout=20,
    )
    hostname = ""
    version = ""
    for line in cp.stdout.splitlines():
        if line.startswith("__HOST__="):
            hostname = line.split("=", 1)[1].strip()
        elif line.startswith("__PVE__="):
            version = line.split("=", 1)[1].strip()
    if not version:
        raise RuntimeError(f"{host} is reachable by SSH but Proxmox VE was not detected.")
    return {"host": host, "hostname": hostname or host, "version": version}


def _parse_vms(data):
    out = []
    for item in data or []:
        typ = str(item.get("type", "")).lower()
        if typ not in ("qemu", "vm"):
            continue
        if int(item.get("template", 0) or 0) == 1:
            continue
        out.append({
            "vmid": int(item.get("vmid")),
            "name": item.get("name") or f"vm-{item.get('vmid')}",
            "status": str(item.get("status", "unknown")).lower(),
            "node": item.get("node", ""),
            "cpu": item.get("maxcpu", 0),
            "memory": int(item.get("maxmem", 0) or 0),
            "disk": int(item.get("maxdisk", 0) or 0),
        })
    return sorted(out, key=lambda x: x["vmid"])


def list_qemu_vms(host: str, username: str, password: str):
    data = _json_remote(
        host, username, password,
        "pvesh get /cluster/resources --type vm --output-format json",
    )
    return _parse_vms(data)


def _parse_storages(config_rows, status_rows):
    status = {str(x.get("storage")): x for x in (status_rows or [])}
    out = []
    for row in config_rows or []:
        name = str(row.get("storage", "")).strip()
        if not name:
            continue
        content = row.get("content", "")
        if isinstance(content, list):
            content_items = {str(x).strip() for x in content}
        else:
            content_items = {x.strip() for x in str(content).split(",") if x.strip()}
        if "images" not in content_items:
            continue
        st = status.get(name, {})
        active = int(st.get("active", 1) or 0) == 1
        if not active:
            continue
        out.append({
            "storage": name,
            "type": row.get("type", ""),
            "content": ",".join(sorted(content_items)),
            "total": int(st.get("total", 0) or 0),
            "avail": int(st.get("avail", 0) or 0),
            "used": int(st.get("used", 0) or 0),
        })
    return sorted(out, key=lambda x: x["storage"])


def list_image_storages(host: str, username: str, password: str):
    config_rows = _json_remote(host, username, password, "pvesh get /storage --output-format json")
    status_rows = _json_remote(host, username, password, "pvesm status --output-format json")
    return _parse_storages(config_rows, status_rows)


def _all_guest_ids(host: str, username: str, password: str):
    data = _json_remote(
        host, username, password,
        "pvesh get /cluster/resources --type vm --output-format json",
    )
    return {int(x["vmid"]) for x in (data or []) if x.get("vmid") is not None}


def choose_target_vmid(host: str, username: str, password: str, preferred_vmid: int):
    used = _all_guest_ids(host, username, password)
    if int(preferred_vmid) not in used:
        return int(preferred_vmid)
    cp = _ssh(host, username, password, "pvesh get /cluster/nextid", timeout=20)
    m = re.search(r"\b(\d{3,9})\b", cp.stdout)
    if not m:
        raise RuntimeError("Could not determine the next available destination VMID.")
    return int(m.group(1))


def _remote_sha256(host: str, username: str, password: str, path: str):
    cp = _ssh(
        host, username, password,
        f"sha256sum -- {shlex.quote(path)} | awk '{{print $1}}'",
        timeout=3600,
    )
    value = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else ""
    if not re.fullmatch(r"[0-9a-fA-F]{64}", value):
        raise RuntimeError(f"Could not calculate SHA256 for {path} on {host}.")
    return value.lower()


def _local_sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _remote_size(host: str, username: str, password: str, path: str):
    cp = _ssh(host, username, password, f"stat -c %s -- {shlex.quote(path)}", timeout=30)
    try:
        return int(cp.stdout.strip().splitlines()[-1])
    except Exception as exc:
        raise RuntimeError(f"Could not determine backup size on {host}.") from exc


def _vm_status(host: str, username: str, password: str, vmid: int):
    cp = _ssh(host, username, password, f"qm status {int(vmid)}", timeout=20)
    m = re.search(r"status:\s*(\S+)", cp.stdout, re.I)
    return (m.group(1).lower() if m else "unknown")


def _vm_exists(host: str, username: str, password: str, vmid: int):
    return int(vmid) in _all_guest_ids(host, username, password)


def _bridges_from_config(config_text: str):
    return sorted(set(re.findall(r"(?:^|,)bridge=([^,\s]+)", config_text, flags=re.M)))


def _destination_bridges(host: str, username: str, password: str):
    cp = _ssh(
        host, username, password,
        r"ip -o link show | awk -F': ' '{print $2}' | cut -d@ -f1 | grep -E '^(vmbr|ovs)' || true",
        timeout=20,
    )
    return sorted({x.strip() for x in cp.stdout.splitlines() if x.strip()})


def _emit(progress, step: int, total: int, title: str, detail: str = ""):
    if progress:
        progress(step, total, title, detail)


def cold_copy_vm(*, source: dict, destination: dict, vm: dict, target_storage: str,
                 target_vmid: int | None = None, progress=None):
    """
    Cold-copy one stopped QEMU VM between independent Proxmox hosts.

    Passwords are accepted only in the in-memory source/destination dictionaries.
    They are never written to history, receipts, config files, or command arguments.
    The source VM is never deleted or started/stopped by this routine.
    The restored destination VM is intentionally left powered off.
    """
    _require_tools()
    source_host = source["host"]
    source_user = source["username"]
    source_password = source["password"]
    destination_host = destination["host"]
    destination_user = destination["username"]
    destination_password = destination["password"]
    vmid = int(vm["vmid"])
    vm_name = str(vm.get("name") or f"vm-{vmid}")
    total_steps = 10

    _emit(progress, 1, total_steps, "Preflight", "Checking source and destination")
    src_info = test_proxmox_host(source_host, source_user, source_password)
    dst_info = test_proxmox_host(destination_host, destination_user, destination_password)

    status = _vm_status(source_host, source_user, source_password, vmid)
    if status != "stopped":
        raise RuntimeError(
            f"Safety stop: source VM {vmid} ({vm_name}) is {status.upper()}. "
            "This wizard only copies a VM that is already powered off."
        )

    if target_vmid is None:
        target_vmid = choose_target_vmid(
            destination_host, destination_user, destination_password, vmid
        )
    target_vmid = int(target_vmid)
    if _vm_exists(destination_host, destination_user, destination_password, target_vmid):
        raise RuntimeError(f"Destination VMID {target_vmid} already exists. Nothing was changed.")

    storages = list_image_storages(
        destination_host, destination_user, destination_password
    )
    storage = next((s for s in storages if s["storage"] == target_storage), None)
    if storage is None:
        raise RuntimeError(
            f"Destination storage '{target_storage}' is unavailable or does not support VM images."
        )

    _emit(progress, 2, total_steps, "Source configuration", f"Reading VM {vmid}")
    src_cfg = _ssh(
        source_host, source_user, source_password, f"qm config {vmid}", timeout=30
    ).stdout
    source_bridges = _bridges_from_config(src_cfg)

    run_id = time.strftime("%Y%m%d-%H%M%S")
    receipt_dir = STATE / "migrations" / safe_name(f"{vm_name}-{vmid}-to-{destination_host}-{run_id}")
    receipt_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(receipt_dir, 0o700)
    except PermissionError:
        pass

    marker = f"/tmp/lbm-vdrc-{safe_name(vm_name)}-{vmid}-{run_id}.marker"
    dump_dir = "/var/lib/vz/dump"
    pattern = f"vzdump-qemu-{vmid}-*.vma.zst"

    _emit(progress, 3, total_steps, "Creating final backup", "vzdump --mode stop --compress zstd")
    remote_backup_command = (
        "set -e; "
        f"mkdir -p {shlex.quote(dump_dir)}; "
        f"touch {shlex.quote(marker)}; "
        f"vzdump {vmid} --mode stop --compress zstd --dumpdir {shlex.quote(dump_dir)}; "
        f"f=$(find {shlex.quote(dump_dir)} -maxdepth 1 -type f "
        f"-name {shlex.quote(pattern)} -newer {shlex.quote(marker)} "
        r"-printf '%T@ %p\n' | sort -nr | head -n1 | cut -d' ' -f2-); "
        f"rm -f {shlex.quote(marker)}; "
        r'test -n "$f"; printf "__LBM_BACKUP__=%s\n" "$f"'
    )
    cp = _ssh(
        source_host, source_user, source_password,
        remote_backup_command, timeout=None,
    )
    backup_path = ""
    for line in cp.stdout.splitlines():
        if line.startswith("__LBM_BACKUP__="):
            backup_path = line.split("=", 1)[1].strip()
    if not backup_path:
        raise RuntimeError("vzdump completed but the generated backup file could not be identified.")

    backup_name = Path(backup_path).name
    backup_size = _remote_size(source_host, source_user, source_password, backup_path)
    source_sha = _remote_sha256(source_host, source_user, source_password, backup_path)

    local_backup = receipt_dir / backup_name
    free = shutil.disk_usage(receipt_dir).free
    if free < int(backup_size * 1.05):
        raise RuntimeError(
            f"Controller staging does not have enough free space. "
            f"Need about {int(backup_size * 1.05)} bytes; available {free} bytes. "
            f"Source backup is preserved at {backup_path}."
        )

    _emit(progress, 4, total_steps, "Transfer source → controller", backup_name)
    _scp_pull(source_host, source_user, source_password, backup_path, local_backup)

    _emit(progress, 5, total_steps, "Verify controller copy", "SHA256")
    local_sha = _local_sha256(local_backup)
    if local_sha != source_sha:
        raise RuntimeError(
            "SHA256 mismatch after source → controller transfer. "
            "Restore was not attempted; source VM and source backup are preserved."
        )

    destination_dump = f"{dump_dir}/{backup_name}"
    _emit(progress, 6, total_steps, "Transfer controller → destination", backup_name)
    _ssh(
        destination_host, destination_user, destination_password,
        f"mkdir -p {shlex.quote(dump_dir)}", timeout=30,
    )
    _scp_push(
        destination_host, destination_user, destination_password,
        local_backup, destination_dump,
    )

    _emit(progress, 7, total_steps, "Verify destination copy", "SHA256")
    destination_sha = _remote_sha256(
        destination_host, destination_user, destination_password, destination_dump
    )
    if destination_sha != source_sha:
        raise RuntimeError(
            "SHA256 mismatch on destination. qmrestore was not attempted. "
            "Source VM is unchanged and remains powered off."
        )

    _emit(progress, 8, total_steps, "Restore destination VM", f"VMID {target_vmid} → {target_storage}")
    restore_command = (
        f"qmrestore {shlex.quote(destination_dump)} {target_vmid} "
        f"--storage {shlex.quote(target_storage)}"
    )
    try:
        _ssh(
            destination_host, destination_user, destination_password,
            restore_command, capture=False, timeout=None,
        )
    except Exception as exc:
        raise RuntimeError(
            f"qmrestore failed. The source VM was not modified. "
            f"Destination VMID {target_vmid} may be partially created and must be reviewed manually."
        ) from exc

    _emit(progress, 9, total_steps, "Safety validation", "Destination must remain OFF")
    restored_status = _vm_status(
        destination_host, destination_user, destination_password, target_vmid
    )
    if restored_status != "stopped":
        _ssh(
            destination_host, destination_user, destination_password,
            f"qm stop {target_vmid}", timeout=60, check=False,
        )
        restored_status = _vm_status(
            destination_host, destination_user, destination_password, target_vmid
        )

    dst_cfg = _ssh(
        destination_host, destination_user, destination_password,
        f"qm config {target_vmid}", timeout=30,
    ).stdout
    destination_bridges = _destination_bridges(
        destination_host, destination_user, destination_password
    )
    restored_bridges = _bridges_from_config(dst_cfg)
    missing_bridges = sorted(set(restored_bridges) - set(destination_bridges))

    result = {
        "status": "SUCCESS",
        "time": now_iso(),
        "source": {
            "host": source_host,
            "hostname": src_info["hostname"],
            "version": src_info["version"],
            "vmid": vmid,
            "vm_name": vm_name,
            "vm_status": "stopped",
            "backup": backup_path,
        },
        "destination": {
            "host": destination_host,
            "hostname": dst_info["hostname"],
            "version": dst_info["version"],
            "vmid": target_vmid,
            "storage": target_storage,
            "vm_status": restored_status,
            "backup": destination_dump,
        },
        "controller_staging": str(local_backup),
        "sha256": source_sha,
        "backup_bytes": backup_size,
        "source_bridges": source_bridges,
        "destination_bridges": destination_bridges,
        "missing_bridges": missing_bridges,
        "source_preserved": True,
        "destination_autostarted": False,
    }
    receipt = receipt_dir / "migration-receipt.json"
    receipt.write_text(json.dumps(result, indent=2), encoding="utf-8")
    try:
        os.chmod(receipt, 0o600)
    except PermissionError:
        pass

    history({
        "event": "pve_cold_copy_success",
        "source_host": source_host,
        "destination_host": destination_host,
        "source_vmid": vmid,
        "destination_vmid": target_vmid,
        "vm": vm_name,
        "storage": target_storage,
        "sha256": source_sha,
        "missing_bridges": missing_bridges,
    })

    _emit(progress, 10, total_steps, "Completed", f"Destination VM {target_vmid} is {restored_status.upper()}")
    return result
