# Complete Administrator Manual

## Linux Backup Manager - Virtualization & Disaster Recovery Center

**Version 1.0.0**  
**Designed & Developed by antonios.mortos@outlook.com**

## 1. Purpose

LBM-VDRC centralizes virtualization backup administration from a Linux terminal. It provides one interface for hypervisor inventory, reusable credentials, NAS/SAN backup destinations, recurring services, reporting, and safe migration planning.

It is deliberately an orchestration layer. Where a hypervisor already has a mature native backup/export mechanism, LBM-VDRC calls that mechanism rather than inventing an incompatible proprietary format.

## 2. Components

```text
ANSI TUI / CLI
      │
      ├── Credential Vault
      ├── Hypervisor Connectors
      │      ├── Proxmox API
      │      ├── VMware govc
      │      └── Hyper-V PowerShell over SSH
      │
      ├── Storage Manager
      │      ├── Local
      │      ├── NFS
      │      ├── SMB/CIFS
      │      └── iSCSI
      │
      ├── Job Engine
      │      ├── Backup Jobs
      │      └── Migration Plan Jobs
      │
      ├── systemd Scheduler
      ├── SMTP Reporter
      ├── History / Logs
      └── Diagnostics
```

## 3. Installation

Clone:

```bash
git clone https://github.com/antonismor/Linux-Backup-Manager---Virtualization-Disaster-Recovery-Center.git
cd Linux-Backup-Manager---Virtualization-Disaster-Recovery-Center
```

Debian/Ubuntu dependencies:

```bash
sudo apt update
sudo apt install -y python3 nfs-common cifs-utils open-iscsi openssh-client qemu-utils
```

Install:

```bash
sudo ./install.sh
```

Or request supported dependency installation first:

```bash
sudo ./install.sh --install-deps
```

Run:

```bash
sudo lbm-vdrc
```

## 4. UI operation

The ANSI UI supports:

```text
↑ / ↓     move selection
ENTER     select
ESC       back/cancel
Ctrl+C    emergency exit from the program
```

The interface is rendered to a fixed detected width. Every row is padded or clipped before the right border is printed, and ANSI escape sequences are excluded from visible-width calculations.

## 5. Credential Vault

Credential profiles must normally be created before hypervisor or SMB/iSCSI profiles.

```bash
sudo lbm-vdrc credential add NAME --type TYPE
```

Secrets live in:

```text
/etc/lbm-vdrc/secrets.json
```

with root-only permissions.

For unattended production operation:

- prefer Proxmox API tokens;
- prefer SSH public keys for Hyper-V;
- use dedicated backup accounts;
- avoid passing passwords as CLI arguments;
- protect `/etc/lbm-vdrc` with backup/security controls appropriate to your environment.

## 6. Storage profiles

Storage profiles separate credentials and mount details from jobs. A job refers to a storage profile name.

### Local

```bash
sudo lbm-vdrc storage add local-backup --type local
```

### NFS

```bash
sudo lbm-vdrc storage add backup-nfs --type nfs
```

### SMB/CIFS

```bash
sudo lbm-vdrc credential add nas-smb --type smb
sudo lbm-vdrc storage add backup-smb --type smb
```

### iSCSI

```bash
sudo lbm-vdrc credential add san-chap --type iscsi
sudo lbm-vdrc storage add backup-san --type iscsi
```

Test any target:

```bash
sudo lbm-vdrc storage test TARGET
```

See [STORAGE.md](STORAGE.md) for SAN/NAS safety details.

## 7. Proxmox VE

Add credentials and host:

```bash
sudo lbm-vdrc credential add pve-admin --type proxmox
sudo lbm-vdrc hypervisor add PVE01 --type proxmox --host 10.10.10.10 --credential pve-admin
```

Test:

```bash
sudo lbm-vdrc hypervisor test PVE01
sudo lbm-vdrc hypervisor vms PVE01
```

Backup jobs call native `vzdump`. The destination must therefore also exist as a Proxmox storage ID visible to the node executing the backup.

## 8. VMware ESXi / vCenter

Install `govc`, create credentials, then:

```bash
sudo lbm-vdrc hypervisor add ESXI01 --type esxi --host https://10.10.10.20/sdk --credential vmware-admin
sudo lbm-vdrc hypervisor test ESXI01
```

VM backups are exported as OVF to the mounted LBM target.

## 9. Microsoft Hyper-V

Hyper-V uses PowerShell over Windows OpenSSH.

```bash
sudo lbm-vdrc hypervisor add HV01 --type hyperv --host 10.10.10.30 --credential hyperv-admin
sudo lbm-vdrc hypervisor test HV01
```

Backup jobs invoke `Export-VM` and transfer the result over SCP.

## 10. Backup jobs

Create interactively:

```bash
sudo lbm-vdrc job add-backup nightly-erp
```

The wizard asks for source hypervisor, VM, storage, schedule, and backend-specific data.

Run manually:

```bash
sudo lbm-vdrc job run nightly-erp
```

Always test a manual run before enabling a recurring schedule.

## 11. Background execution

Every recurring job receives one `.service` and one `.timer` in `/etc/systemd/system`.

Example:

```text
lbm-vdrc-job-nightly-erp.service
lbm-vdrc-job-nightly-erp.timer
```

The service is `Type=oneshot`; it starts, performs one job, writes history/reports, then exits.

## 12. Email reporting

```bash
sudo lbm-vdrc credential add smtp --type generic
sudo lbm-vdrc email configure
```

The job engine attempts email after success or failure. An email failure does not rewrite a successful backup result into a failed backup; inspect mail delivery independently if notifications are operationally critical.

## 13. Logs and history

Application log:

```text
/var/log/lbm-vdrc/lbm-vdrc.log
```

Structured history:

```text
/var/lib/lbm-vdrc/history.jsonl
```

systemd job output:

```bash
journalctl -u lbm-vdrc-job-JOB.service
```

## 14. Migration planning

Create:

```bash
sudo lbm-vdrc job add-migration VM-PVE-to-ESXI
```

Run:

```bash
sudo lbm-vdrc job run VM-PVE-to-ESXI
```

Version 1.0.0 produces a safe plan/preflight baseline. It does not enable automatic destructive cutover.

See [MIGRATION.md](MIGRATION.md).

## 15. Diagnostics

```bash
sudo lbm-vdrc doctor
```

Core dependencies are distinguished from optional connector dependencies.

## 16. Backup verification policy

A job saying SUCCESS means its configured export/backup operation completed without an error returned to LBM-VDRC. It does not prove that the guest application is recoverable.

Production procedure should include periodic restore tests to isolated networks or non-production targets.

## 17. Security baseline

- keep TLS validation enabled;
- use dedicated accounts/tokens;
- restrict controller root access;
- use SSH keys for Hyper-V;
- separate at least one recovery copy from hypervisor administrator credentials;
- use immutable/offline retention where your storage platform supports it;
- do not mount one ordinary iSCSI filesystem read/write from multiple hosts;
- never test restores by overwriting the only production VM.

## 18. Upgrade approach

Before replacing a production install:

```bash
sudo cp -a /etc/lbm-vdrc /root/lbm-vdrc-config-backup
sudo cp -a /var/lib/lbm-vdrc /root/lbm-vdrc-state-backup
```

Then install the newer package. The installer does not intentionally delete existing configuration.

## 19. Uninstall

```bash
sudo ./uninstall.sh
```

The uninstaller disables LBM-VDRC timers and removes program files. Configuration, credentials, history, logs, and backup data are intentionally preserved.

## 20. Recommended go-live checklist

Before relying on a scheduled backup:

```text
[ ] lbm-vdrc doctor has no missing dependency required by this deployment
[ ] hypervisor connection test passes
[ ] VM inventory is correct
[ ] storage test passes
[ ] sufficient storage capacity is available
[ ] one manual backup succeeds
[ ] a recovery test succeeds
[ ] systemd timer shows the expected next run
[ ] SMTP success/failure delivery has been tested
[ ] controller clock/timezone is correct
[ ] credentials are least privilege where possible
[ ] an off-host/immutable recovery copy exists for critical workloads
```

---

**Designed & Developed by antonios.mortos@outlook.com**
