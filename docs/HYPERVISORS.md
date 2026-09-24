# Hypervisor Setup

## Proxmox VE

Create a credential profile:

```bash
sudo lbm-vdrc credential add pve-admin --type proxmox
```

API-token authentication is preferred for unattended operation.

Add the host:

```bash
sudo lbm-vdrc hypervisor add PVE01 --type proxmox --host 10.10.10.10 --credential pve-admin
```

Test and list VMs:

```bash
sudo lbm-vdrc hypervisor test PVE01
sudo lbm-vdrc hypervisor vms PVE01
```

The default PVE API port is `8006`.

For VM backup, LBM-VDRC calls native `vzdump` through the API and therefore asks for a PVE storage ID.

## VMware ESXi / vCenter

LBM-VDRC uses the `govc` command-line client as its VMware connector.

Create credentials:

```bash
sudo lbm-vdrc credential add vmware-admin --type esxi
```

Add:

```bash
sudo lbm-vdrc hypervisor add ESXI01 --type esxi --host https://10.10.10.20/sdk --credential vmware-admin
```

Test:

```bash
sudo lbm-vdrc hypervisor test ESXI01
sudo lbm-vdrc hypervisor vms ESXI01
```

Backups use OVF export to the selected LBM storage target.

## Microsoft Hyper-V

The Hyper-V connector uses PowerShell through Windows OpenSSH.

On the Windows host, OpenSSH Server must be installed, running, reachable, and permitted through Windows Firewall.

Create credentials:

```bash
sudo lbm-vdrc credential add hyperv-admin --type hyperv
```

Add:

```bash
sudo lbm-vdrc hypervisor add HV01 --type hyperv --host 10.10.10.30 --credential hyperv-admin
```

Test:

```bash
sudo lbm-vdrc hypervisor test HV01
sudo lbm-vdrc hypervisor vms HV01
```

### Recommended authentication

For scheduled jobs, prefer SSH public keys. Password automation requires `sshpass`, which exists only as a fallback.

### Backup workflow

LBM-VDRC requests `Export-VM` on the Hyper-V host, then transfers the export to the selected controller storage target over SCP.

## TLS verification

Certificate verification should remain enabled in production. `--insecure` exists for controlled lab/self-signed-certificate scenarios but should not become the normal production configuration.

Designed & Developed by **antonios.mortos@outlook.com**
