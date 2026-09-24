# Quick Start

This guide takes a new Debian/Ubuntu system from a clean checkout to its first scheduled VM backup.

## 1. Clone

```bash
git clone https://github.com/antonismor/Linux-Backup-Manager---Virtualization-Disaster-Recovery-Center.git
cd Linux-Backup-Manager---Virtualization-Disaster-Recovery-Center
```

## 2. Dependencies

```bash
sudo apt update
sudo apt install -y python3 nfs-common cifs-utils open-iscsi openssh-client qemu-utils
```

Install `govc` separately when VMware ESXi/vCenter is required.

## 3. Install

```bash
sudo ./install.sh
sudo lbm-vdrc doctor
```

## 4. Start the UI

```bash
sudo lbm-vdrc
```

Recommended order inside the UI:

```text
Credential Vault
      ↓
Storage Mapping
      ↓
Hypervisor Hosts
      ↓
Virtual Machines
      ↓
Backup VM
      ↓
Scheduled Jobs
      ↓
Email Reports
```

## 5. CLI example: Proxmox + NFS

Create a Proxmox API credential:

```bash
sudo lbm-vdrc credential add pve-admin --type proxmox
```

Add the Proxmox host:

```bash
sudo lbm-vdrc hypervisor add PVE01 --type proxmox --host 10.10.10.10 --credential pve-admin
sudo lbm-vdrc hypervisor test PVE01
sudo lbm-vdrc hypervisor vms PVE01
```

Add the controller-side NFS target:

```bash
sudo lbm-vdrc storage add backup-nfs --type nfs
sudo lbm-vdrc storage test backup-nfs
```

Create the backup job:

```bash
sudo lbm-vdrc job add-backup nightly-vm101
```

For Proxmox, enter the Proxmox storage ID that `vzdump` should use. If the target is an NFS/CIFS/iSCSI datastore, register it in Proxmox first.

Run once manually:

```bash
sudo lbm-vdrc job run nightly-vm101
```

Inspect the timer:

```bash
systemctl list-timers 'lbm-vdrc-job-*' --all
```

## 6. Test recovery

Do not consider the deployment complete until you have tested recovery on a non-production target. Backup completion and actual recoverability are different things.

Designed & Developed by **antonios.mortos@outlook.com**
