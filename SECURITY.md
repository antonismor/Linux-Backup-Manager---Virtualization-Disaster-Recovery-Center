# Security Policy

LBM-VDRC is an administrative tool that can run as root, mount storage, use hypervisor credentials, and start backup jobs. Treat the controller as privileged infrastructure.

## Reporting a vulnerability

Please report security issues privately to:

**antonios.mortos@outlook.com**

Include the affected version, Linux distribution, connector/storage type, reproduction steps, and expected impact. Remove passwords, tokens, private keys, customer data, and other secrets from logs before sending them.

## Credential storage

Version 1.0.0 stores unattended credentials in:

```text
/etc/lbm-vdrc/secrets.json
```

The file is mode `0600` and `/etc/lbm-vdrc` is mode `0700`.

This is a root-only local secret store, not a hardware-backed vault. Environments with stronger requirements should integrate a dedicated secret manager, systemd credentials, TPM-backed secrets, or an enterprise vault.

## Recommendations

- Prefer Proxmox API tokens to reusable passwords.
- Prefer SSH keys for Hyper-V automation.
- Use dedicated backup accounts and least privilege where practical.
- Keep TLS certificate verification enabled in production.
- Do not pass passwords on the command line unless you understand process-list and shell-history exposure.
- Restrict interactive root access to the LBM-VDRC controller.
- Keep at least one recovery copy outside the administrative blast radius of the virtualization hosts.
- Use immutable/offline storage where supported.
- Test restore procedures in an isolated environment.
- Do not enable experimental migration cutover logic on production workloads before lab validation.

## Backup target security

A mounted backup target can be altered by any sufficiently privileged process on the controller. For ransomware resilience, consider storage-side snapshots, immutable object retention, offline copies, or credentials that cannot delete older recovery points.

## iSCSI safety

LBM-VDRC does not format iSCSI LUNs. Never mount a normal, non-cluster-aware filesystem read/write from multiple hosts at the same time.

---

Designed & Developed by **antonios.mortos@outlook.com**
