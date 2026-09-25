# Cross-Hypervisor Migration Design & Safety

LBM-VDRC is designed to cover these directions:

```text
Proxmox  -> VMware ESXi
Proxmox  -> Microsoft Hyper-V
VMware   -> Proxmox
VMware   -> Microsoft Hyper-V
Hyper-V  -> Proxmox
Hyper-V  -> VMware ESXi
```

## Version 1.0.0 behavior

Version 1.0.0 implements the control-plane framework, job definitions, source/destination inventory, storage staging selection, migration history, scheduling framework, and preflight/plan generation.

Automatic final cross-hypervisor cutover is intentionally safety-locked.

## Why the lock exists

A disk-format conversion alone is not a migration. The engine must account for:

- BIOS versus UEFI;
- Secure Boot;
- TPM/vTPM state;
- BitLocker or other TPM-bound encryption;
- guest storage-controller drivers;
- VirtIO/VMware/Hyper-V integration drivers;
- disk topology and boot order;
- snapshots/checkpoints;
- thin/thick/sparse disk semantics;
- NIC model changes;
- VLAN and virtual-switch mapping;
- static MAC requirements and conflicts;
- PCI/GPU/USB passthrough;
- shared disks;
- source and destination storage capacity;
- guest application consistency;
- Windows activation/licensing implications;
- post-boot validation.

## Safe target workflow

A future fully validated adapter should use this sequence:

```text
Inventory
   ↓
Preflight
   ↓
Safety backup
   ↓
Quiesce / graceful shutdown when required
   ↓
Final disk capture
   ↓
Disk conversion
   ↓
Create target VM
   ↓
Map firmware / CPU / memory / network
   ↓
Isolated boot validation
   ↓
Health checks
   ↓
Operator-approved cutover
   ↓
Preserve source VM until acceptance
```

## Create a migration plan

```bash
sudo lbm-vdrc job add-migration ERP01-PVE-to-ESXI
sudo lbm-vdrc job run ERP01-PVE-to-ESXI
```

The resulting plan is recorded in job history and can be staged on the configured storage target.

## Scheduling

A migration job may be assigned a systemd schedule, but version 1.0.0 repeats only the safe plan/preflight stage. It does not silently shut down or delete source VMs.

## Production rule

Do not enable automated source→target cutover for a hypervisor pair until that exact adapter has been validated on representative non-production VMs, including both Linux and Windows guests if both are in scope.

Designed & Developed by **antonios.mortos@outlook.com**


## Independent Proxmox → Proxmox cold copy

A lab-validated implementation is being introduced separately from cross-hypervisor conversion.

Run the ANSI/TUI workflow with:

```bash
sudo lbm-vdrc
```

then select:

```text
VM Migration
  └─ Proxmox → Proxmox Cold Copy (Independent Hosts)
```

or start the same interactive wizard directly:

```bash
sudo lbm-vdrc pve-copy
```

No migration parameters are required on the command line. The wizard reads both Proxmox hosts live over SSH, lists the source QEMU VMs, discovers destination storage and guest IDs, and performs a cold `vzdump → transfer → qmrestore` workflow with SHA256 validation.

The source VM must already be powered off. The destination copy remains powered off and is forced to `onboot=0` until administrator validation.

See [PROXMOX_COLD_COPY.md](PROXMOX_COLD_COPY.md).
