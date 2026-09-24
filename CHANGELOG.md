# Changelog

## 1.0.0 — 2026-09-24

Initial independent public release of **Linux Backup Manager - Virtualization & Disaster Recovery Center**.

### User interface

- Fixed-width ANSI terminal renderer.
- ANSI-aware visible-width calculation.
- Long-value clipping instead of frame wrapping.
- Right-side vertical borders remain in the same terminal column.
- Arrow-key / ENTER / ESC navigation.
- Colored ONLINE / OFFLINE / SUCCESS / FAILED / WARNING states.
- Interactive submenus for hypervisors, storage, credentials, scheduled jobs, email, and diagnostics.

### Hypervisors

- Proxmox VE HTTPS API connector.
- Proxmox VM/CT inventory.
- Native `vzdump` backup orchestration through the PVE API.
- VMware ESXi/vCenter inventory through `govc`.
- VMware OVF export through `govc`.
- Microsoft Hyper-V inventory through PowerShell over SSH.
- Hyper-V `Export-VM` orchestration with SCP transfer.

### Storage

- Local paths.
- NFS.
- SMB/CIFS/Samba with reusable credential profiles.
- iSCSI with optional CHAP and filesystem UUID support.
- Read/write target testing.

### Automation

- Per-job `systemd` oneshot services.
- Per-job `systemd` timers.
- `Persistent=true` missed-run behavior.
- Configurable `OnCalendar` schedules.
- Manual run, enable/update schedule, and disable schedule commands.

### Reporting and operations

- SMTP SUCCESS / FAILED notifications.
- JSONL history.
- Application log.
- Doctor/diagnostics command.
- Installer/uninstaller.
- Optional automatic installation of supported core Linux dependencies.

### Migration framework

- Source/destination migration job definitions.
- Cross-hypervisor plan/preflight framework for Proxmox, ESXi/vCenter, and Hyper-V.
- Production cutover remains safety-locked until each adapter is validated against real source/destination environments.

### Quality

- Unit test enforcing ANSI frame alignment.
- Small-terminal width regression test.
- Core name-sanitization test.
- GitHub Actions CI for compile, unit, shell syntax, and CLI smoke tests.
- Complete English documentation set.

---

Designed & Developed by **antonios.mortos@outlook.com**
