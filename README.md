# Linux Backup Manager - Virtualization & Disaster Recovery Center

**Linux Backup Manager - Virtualization & Disaster Recovery Center (LBM-VDRC)** is an independent open-source control plane for virtual-machine inventory, backup orchestration, storage targets, scheduling, reporting, and safe cross-hypervisor disaster-recovery planning.

**Version:** `1.0.0`  
**License:** MIT  
**Designed & Developed by:** `antonios.mortos@outlook.com`

> This project is independent from the original Linux Backup Manager. It has its own executable, configuration tree, state, logs, schedules and managed storage mounts.

## Highlights

- Fixed-width ANSI terminal UI with aligned right-side borders.
- Arrow-key / ENTER / ESC navigation and colored status states.
- Proxmox VE inventory through the PVE HTTPS API.
- Proxmox native `vzdump` backup orchestration.
- VMware ESXi/vCenter inventory and OVF export through `govc`.
- Microsoft Hyper-V inventory and `Export-VM` through PowerShell over SSH.
- Local, NFS, SMB/CIFS/Samba and iSCSI storage profiles.
- Reusable credential profiles created before jobs.
- Root-only unattended credential storage.
- Per-job `systemd` services and recurring timers.
- `Persistent=true` so missed scheduled work can run after reboot.
- SMTP SUCCESS / FAILED reports.
- JSONL history, application log and diagnostics.
- Cross-hypervisor migration planning/preflight framework.
- GitHub Actions CI and unit tests for UI alignment.

## Production status

| Area | Status in 1.0.0 |
|---|---|
| ANSI TUI / CLI | Ready |
| Credential profiles | Ready |
| NFS / SMB / iSCSI targets | Ready |
| Proxmox inventory | Ready |
| Proxmox native `vzdump` orchestration | Ready, requires a PVE storage ID |
| ESXi/vCenter inventory and OVF export | Ready when `govc` is installed |
| Hyper-V inventory / `Export-VM` | Ready when Windows OpenSSH is configured |
| systemd recurring backup jobs | Ready |
| SMTP success/failure reports | Ready |
| Cross-hypervisor migration preflight/planning | Ready |
| Automatic PVE ↔ ESXi ↔ Hyper-V production cutover | **Safety-locked / not enabled in 1.0.0** |

The migration lock is deliberate. Firmware, Secure Boot, TPM/vTPM, BitLocker, guest drivers, storage controllers, snapshots/checkpoints, VLANs and passthrough hardware can make a mechanically converted VM unbootable. Version 1.0.0 does not claim unattended cutover support that has not been validated against real source and destination hosts.

## Interface preview

```text
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ ◆ LINUX BACKUP MANAGER - VIRTUALIZATION & DISASTER RECOVERY CENTER                              2026-09-24 21:00:00 ║
║   Backup • Restore • Convert • Migrate • Disaster Recovery                                                        ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║┌─ CONNECTED HYPERVISORS ──────────────────────────────────────────────────────────────────────────────────────────┐║
║│  #   HOST             PLATFORM                 ADDRESS             VMs     STATE                                │║
║│  1   PVE01            Proxmox VE 9.x           10.10.10.10          12      ● ONLINE                           │║
║│  2   ESXI01           VMware ESXi 8            10.10.10.20           8      ● ONLINE                           │║
║│  3   HV01             Microsoft Hyper-V 2025   10.10.10.30          10      ● ONLINE                           │║
║└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘║
║                                                                                                                      ║
║┌─ MAIN MENU ──────────────────────────────────────────────────────────────────────────────────────────────────────┐║
║│  ▶  Hypervisor Hosts                                                                                            │║
║│     Virtual Machines                                                                                            │║
║│     Backup VM                                                                                                   │║
║│     Restore VM                                                                                                  │║
║│     VM Migration                                                                                                │║
║│     Disk Conversion                                                                                             │║
║│     Network Mapping                                                                                             │║
║│     Storage Mapping                                                                                             │║
║│     Scheduled Jobs                                                                                              │║
║│     Backup History                                                                                              │║
║│     Email Reports                                                                                               │║
║│     Credential Vault                                                                                            │║
║│     Doctor / Diagnostics                                                                                        │║
║└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ ↑/↓ Navigate   ENTER Select   ESC Back   F1 Help   F5 Refresh                                          ● READY     ║
║ Designed & Developed by antonios.mortos@outlook.com                                                               ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

The renderer measures visible characters after removing ANSI escape codes, clips oversized fields, pads every row and then draws the right border. This is what keeps all right-hand vertical lines aligned.

## Installation

### Debian / Ubuntu

```bash
git clone https://github.com/antonismor/Linux-Backup-Manager---Virtualization-Disaster-Recovery-Center.git
cd Linux-Backup-Manager---Virtualization-Disaster-Recovery-Center

sudo apt update
sudo apt install -y python3 nfs-common cifs-utils open-iscsi openssh-client qemu-utils

sudo ./install.sh
sudo lbm-vdrc
```

Or let the installer install the supported core dependencies on a recognized distribution:

```bash
sudo ./install.sh --install-deps
```

Check the installation:

```bash
lbm-vdrc --version
sudo lbm-vdrc doctor
```

Expected version:

```text
lbm-vdrc 1.0.0
```

For VMware ESXi/vCenter, install `govc` separately. Password-based Hyper-V SSH can use `sshpass`, although SSH public keys are strongly preferred.

## Recommended first-run workflow

1. Open **Credential Vault** and create credential profiles.
2. Open **Storage Mapping** and create NFS, SMB/CIFS, iSCSI or local targets.
3. Open **Hypervisor Hosts** and add Proxmox, ESXi/vCenter or Hyper-V.
4. Open **Virtual Machines** and verify inventory.
5. Open **Backup VM** and select the source VM and backup destination.
6. Use **Scheduled Jobs** to set the recurring schedule.
7. Configure **Email Reports**.
8. Run one manual backup and perform a recovery test before trusting automation.

## Credentials

```bash
sudo lbm-vdrc credential add pve-admin --type proxmox
sudo lbm-vdrc credential add vmware-admin --type esxi
sudo lbm-vdrc credential add hyperv-admin --type hyperv
sudo lbm-vdrc credential add nas-smb --type smb
sudo lbm-vdrc credential add san-chap --type iscsi
sudo lbm-vdrc credential add smtp --type generic
```

List profile names without displaying the stored secret values:

```bash
sudo lbm-vdrc credential list
```

## Hypervisors

### Proxmox VE

```bash
sudo lbm-vdrc hypervisor add PVE01 --type proxmox --host 10.10.10.10 --credential pve-admin
sudo lbm-vdrc hypervisor test PVE01
sudo lbm-vdrc hypervisor vms PVE01
```

API tokens are preferred for unattended use.

### VMware ESXi / vCenter

After installing `govc`:

```bash
sudo lbm-vdrc hypervisor add ESXI01 --type esxi --host https://10.10.10.20/sdk --credential vmware-admin
sudo lbm-vdrc hypervisor test ESXI01
sudo lbm-vdrc hypervisor vms ESXI01
```

### Microsoft Hyper-V

LBM-VDRC uses PowerShell through Windows OpenSSH:

```bash
sudo lbm-vdrc hypervisor add HV01 --type hyperv --host 10.10.10.30 --credential hyperv-admin
sudo lbm-vdrc hypervisor test HV01
sudo lbm-vdrc hypervisor vms HV01
```

For unattended scheduled jobs, configure SSH public-key authentication.

## Storage targets

### NFS

```bash
sudo lbm-vdrc storage add backup-nfs --type nfs
sudo lbm-vdrc storage test backup-nfs
```

### SMB / Samba / CIFS

Create the SMB credential first:

```bash
sudo lbm-vdrc credential add nas-smb --type smb
sudo lbm-vdrc storage add backup-smb --type smb
sudo lbm-vdrc storage test backup-smb
```

### iSCSI

Create an optional CHAP profile first, then:

```bash
sudo lbm-vdrc credential add san-chap --type iscsi
sudo lbm-vdrc storage add backup-san --type iscsi
sudo lbm-vdrc storage test backup-san
```

**LBM-VDRC never formats the LUN.** It expects an existing filesystem and prefers a filesystem UUID over a volatile `/dev/sdX` device name.

### Local path

```bash
sudo lbm-vdrc storage add local-backup --type local
```

## Create and schedule a backup

```bash
sudo lbm-vdrc job add-backup nightly-erp
```

The wizard asks for the source hypervisor, VM name/ID, storage target, schedule and hypervisor-specific options.

A daily 02:00 timer uses:

```text
*-*-* 02:00:00
```

Run once manually:

```bash
sudo lbm-vdrc job run nightly-erp
```

Inspect timers:

```bash
systemctl list-timers 'lbm-vdrc-job-*' --all
```

Inspect a job log:

```bash
journalctl -u lbm-vdrc-job-nightly-erp.service
```

Change or enable a schedule:

```bash
sudo lbm-vdrc job enable nightly-erp --schedule '*-*-* 03:30:00'
```

Disable it:

```bash
sudo lbm-vdrc job disable nightly-erp
```

LBM-VDRC uses one-shot systemd services rather than leaving a Python process sleeping permanently. Timers use `Persistent=true` and `RandomizedDelaySec=120`.

## Hypervisor-specific backup behavior

**Proxmox:** the job calls native `vzdump`. The destination must exist as a Proxmox storage ID visible to the node. If the physical destination is NFS/CIFS/iSCSI, configure it in Proxmox and provide that PVE storage ID to the job.

**VMware:** the connector uses `govc export.ovf` and writes the export to the selected mounted LBM-VDRC storage target.

**Hyper-V:** the connector requests `Export-VM` on the Windows host and transfers the export to the selected storage target over SCP.

## Email reports

```bash
sudo lbm-vdrc credential add smtp --type generic
sudo lbm-vdrc email configure
```

When enabled, the job engine sends SUCCESS or FAILED reports with the job name, type, duration and result/error.

## Migration jobs

```bash
sudo lbm-vdrc job add-migration ERP01-PVE-to-ESXI
sudo lbm-vdrc job run ERP01-PVE-to-ESXI
```

In 1.0.0, migration jobs create a safe plan/preflight result. A scheduled migration repeats that safe planning stage; it does **not** silently shut down or delete the source VM or perform an unvalidated automatic cutover.

## Important paths

```text
/etc/lbm-vdrc/             configuration and root-only secrets
/var/lib/lbm-vdrc/         history and persistent state
/var/log/lbm-vdrc/         application log
/run/lbm-vdrc/             short-lived runtime data
/mnt/lbm-vdrc/             managed storage mounts
/opt/lbm-vdrc/             installed Python package
/usr/local/bin/lbm-vdrc    executable wrapper
```

## Documentation

- [Quick Start](docs/QUICKSTART.md)
- [Complete Administrator Manual](docs/MANUAL.md)
- [Hypervisor Setup](docs/HYPERVISORS.md)
- [Storage Guide](docs/STORAGE.md)
- [Scheduling & Services](docs/SCHEDULING.md)
- [Email Reporting](docs/EMAIL.md)
- [Migration Design & Safety](docs/MIGRATION.md)
- [CLI Reference](docs/CLI_REFERENCE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Testing

```bash
python3 -m compileall -q lbm_vdrc
PYTHONPATH=. python3 -m unittest discover -s tests -v
bash -n install.sh
bash -n uninstall.sh
```

## Uninstall

```bash
sudo ./uninstall.sh
```

Program files and LBM-VDRC timers are removed. Configuration, credentials, history, logs and backup data are deliberately preserved.

## Security baseline

LBM-VDRC is an administrative tool and normally runs as root. Use dedicated accounts/tokens where possible, keep TLS validation enabled, prefer API tokens and SSH keys, restrict controller access, and keep at least one recovery copy outside the virtualization hosts' administrative blast radius.

## Author

**Antonios Mortos**  
**Designed & Developed by antonios.mortos@outlook.com**
