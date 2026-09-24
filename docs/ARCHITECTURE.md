# Architecture

## Overview

LBM-VDRC is a Linux-hosted control plane. It does not require an always-running application daemon for scheduled work. Persistent configuration is stored locally, while `systemd` starts each job only when required.

```text
                         ┌──────────────────────────┐
                         │      ANSI TUI / CLI      │
                         └────────────┬─────────────┘
                                      │
                     ┌────────────────┼────────────────┐
                     │                │                │
               Credential Vault   Configuration    Diagnostics
                     │                │
              ┌──────┴──────┐         │
              │             │         ▼
       Hypervisor creds  Storage creds      Job Engine
              │             │                 │
        ┌─────┼─────┐   ┌───┼─────┐     ┌────┴─────────┐
        │     │     │   │   │     │     │              │
      PVE   ESXi Hyper-V NFS SMB  iSCSI Backup     Migration Plan
       │     │     │    │   │     │     │              │
       └─────┴─────┴────┴───┴─────┴─────┴──────────────┘
                                      │
                              systemd service/timer
                                      │
                           history / log / SMTP report
```

## UI renderer

All screens share `lbm_vdrc/ui.py`. Backend modules do not draw independent frames.

The renderer:

1. detects terminal width;
2. caps the wide layout;
3. strips ANSI escape codes when measuring visible width;
4. clips values that exceed a cell width;
5. pads every row to a deterministic width;
6. emits the right-hand border only after padding.

Unit tests verify that all frame rows have the same visible character count.

## Configuration model

```text
/etc/lbm-vdrc/
├── hypervisors.json
├── storage.json
├── jobs.json
├── settings.json
└── secrets.json
```

Secrets are deliberately separated from ordinary profiles.

## State model

```text
/var/lib/lbm-vdrc/history.jsonl
```

Each job start/success/failure is appended as a JSON object for easy processing by standard Unix tooling.

## Hypervisor adapters

### Proxmox

Uses the PVE HTTPS API. Backup jobs request native `vzdump` tasks and poll the returned task identifier to completion.

### VMware

Uses `govc` to avoid reimplementing the vSphere client stack. Inventory and OVF export run with a per-command environment built from the selected credential profile.

### Hyper-V

Uses PowerShell through Windows OpenSSH. `Export-VM` runs on the Hyper-V host; SCP transfers the resulting export to controller-side storage.

## Storage adapters

### NFS

Mounted with the system `mount.nfs` implementation.

### SMB/CIFS

A temporary 0600 credentials file is created in `/run/lbm-vdrc`, used by `mount.cifs`, and deleted immediately after the mount attempt.

### iSCSI

Uses `iscsiadm` for discovery/login. Optional CHAP settings are applied to the node. LBM-VDRC then mounts an already-existing filesystem by UUID/device.

## Scheduling

Every scheduled job has:

```text
lbm-vdrc-job-<job>.service
lbm-vdrc-job-<job>.timer
```

Services are `Type=oneshot`; timers use `Persistent=true`.

## Email

SMTP configuration lives in `settings.json` and references a credential profile rather than embedding a password.

## Migration architecture

The migration subsystem intentionally separates:

```text
Discovery → Preflight → Plan → Conversion/Import Adapter → Validation → Cutover
```

Version 1.0.0 exposes the first three stages but leaves production cutover locked. This prevents the user interface from implying that a generic disk conversion is automatically a safe VM migration.

---

Designed & Developed by **antonios.mortos@outlook.com**
