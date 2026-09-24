# Troubleshooting

## Start with Doctor

```bash
sudo lbm-vdrc doctor
```

## UI wraps or looks broken

Check terminal dimensions:

```bash
tput cols
tput lines
echo "$TERM"
```

A 100-column or wider terminal is recommended. The renderer clips values rather than intentionally extending past the detected width.

## Proxmox test fails

Check:

- host/IP and port 8006 reachability;
- API token/user syntax;
- token permissions;
- certificate validation;
- firewall rules.

Run:

```bash
sudo lbm-vdrc hypervisor test PVE01
```

## VMware inventory fails

Confirm `govc`:

```bash
command -v govc
govc version
```

Then:

```bash
sudo lbm-vdrc hypervisor test ESXI01
```

## Hyper-V inventory fails

From Linux, first verify SSH independently:

```bash
ssh Administrator@HYPERV_HOST
```

Then verify PowerShell is available through that SSH session.

For scheduled operation, prefer key authentication.

## NFS mount fails

```bash
showmount -e NFS_SERVER
sudo lbm-vdrc storage test backup-nfs
```

Confirm export permissions and firewall rules.

## SMB mount fails

```bash
command -v mount.cifs
sudo lbm-vdrc storage test backup-smb
```

Confirm username/domain, SMB protocol version, share permissions, and filesystem permissions.

## iSCSI login fails

```bash
sudo iscsiadm -m discovery -t sendtargets -p PORTAL
sudo iscsiadm -m session
```

Confirm IQN, CHAP credentials, initiator ACLs, and TCP/3260 reachability.

## Scheduled job did not run

```bash
systemctl list-timers 'lbm-vdrc-job-*' --all
systemctl status lbm-vdrc-job-JOB.timer
systemctl status lbm-vdrc-job-JOB.service
journalctl -u lbm-vdrc-job-JOB.service
```

## Application log

```bash
sudo tail -f /var/log/lbm-vdrc/lbm-vdrc.log
```

## History

```bash
sudo tail -n 50 /var/lib/lbm-vdrc/history.jsonl
```

Designed & Developed by **antonios.mortos@outlook.com**
