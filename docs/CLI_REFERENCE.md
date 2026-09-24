# CLI Reference

## General

```bash
lbm-vdrc
lbm-vdrc tui
lbm-vdrc --version
lbm-vdrc doctor
```

## Credentials

```bash
lbm-vdrc credential add NAME [--type TYPE] [--username USER]
lbm-vdrc credential list
```

Avoid `--password` on shared systems because shell history/process inspection can expose it. Prefer the interactive password prompt.

## Hypervisors

```bash
lbm-vdrc hypervisor add NAME --type TYPE --host HOST --credential PROFILE
lbm-vdrc hypervisor list
lbm-vdrc hypervisor test NAME
lbm-vdrc hypervisor vms NAME
```

`TYPE` values:

```text
proxmox
esxi
hyperv
```

## Storage

```bash
lbm-vdrc storage add NAME --type TYPE
lbm-vdrc storage list
lbm-vdrc storage test NAME
lbm-vdrc storage mount NAME
lbm-vdrc storage unmount NAME
```

`TYPE` values:

```text
local
nfs
smb
iscsi
```

## Jobs

```bash
lbm-vdrc job add-backup [NAME]
lbm-vdrc job add-migration [NAME]
lbm-vdrc job list
lbm-vdrc job run NAME
lbm-vdrc job enable NAME --schedule 'OnCalendar expression'
lbm-vdrc job disable NAME
```

## Email

```bash
lbm-vdrc email configure
```

## Return codes

A successful command returns `0`. Fatal configuration, dependency, connectivity, mount, backup, or job errors return non-zero and are written to stderr and the application log where possible.

Designed & Developed by **antonios.mortos@outlook.com**
