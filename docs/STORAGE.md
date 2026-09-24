# Storage Guide

LBM-VDRC supports reusable storage profiles. Create credentials first, then add storage. Backup jobs reference the storage profile by name.

## Local

```bash
sudo lbm-vdrc storage add local-backup --type local
```

The selected path is created if necessary.

## NFS

Install support:

```bash
sudo apt install nfs-common
```

Add:

```bash
sudo lbm-vdrc storage add backup-nfs --type nfs
```

The wizard asks for:

- NFS host;
- export path;
- mount options.

Default mount options are conservative for backup traffic:

```text
rw,hard,timeo=600,retrans=2,_netdev
```

Test write access:

```bash
sudo lbm-vdrc storage test backup-nfs
```

## SMB / Samba / CIFS

Install support:

```bash
sudo apt install cifs-utils
```

Create credentials first:

```bash
sudo lbm-vdrc credential add nas-smb --type smb
```

Then add the target:

```bash
sudo lbm-vdrc storage add backup-smb --type smb
```

LBM-VDRC creates a temporary 0600 credentials file under `/run/lbm-vdrc`, uses it for the mount, then removes it.

The default SMB protocol version is `3.1.1`.

## iSCSI

Install support:

```bash
sudo apt install open-iscsi
sudo systemctl enable --now iscsid
```

If CHAP is required:

```bash
sudo lbm-vdrc credential add san-chap --type iscsi
```

Add the target:

```bash
sudo lbm-vdrc storage add backup-san --type iscsi
```

The wizard asks for portal, IQN, optional CHAP profile, filesystem UUID/device, filesystem type, and mount options.

### Important iSCSI safety rule

LBM-VDRC **does not create partitions or filesystems** on a LUN. This is intentional. The configured iSCSI LUN must already contain the filesystem that will be mounted as the backup target.

Prefer:

```text
UUID=<filesystem UUID>
```

over `/dev/sdX`, because Linux device enumeration can change after reboot.

Do not mount the same non-cluster-aware filesystem read/write on multiple hosts simultaneously.

## Mount locations

Managed targets are mounted below:

```text
/mnt/lbm-vdrc/<profile-name>
```

## Test, mount, unmount

```bash
sudo lbm-vdrc storage test NAME
sudo lbm-vdrc storage mount NAME
sudo lbm-vdrc storage unmount NAME
```

`storage test` performs a small write/delete test and reports available bytes.

Designed & Developed by **antonios.mortos@outlook.com**
