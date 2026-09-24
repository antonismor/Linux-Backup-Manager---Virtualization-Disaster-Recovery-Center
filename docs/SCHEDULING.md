# Scheduling & Background Services

LBM-VDRC schedules recurring work with `systemd`. There is no permanently sleeping backup daemon.

## Why systemd timers

This design provides:

- native Linux service supervision;
- journal logs;
- clean boot integration;
- missed-run persistence;
- per-job enable/disable controls;
- no idle Python process consuming memory.

## Create a job and schedule it

```bash
sudo lbm-vdrc job add-backup nightly-erp
```

A daily 02:00 schedule:

```text
*-*-* 02:00:00
```

A timer is generated as:

```text
/etc/systemd/system/lbm-vdrc-job-nightly-erp.timer
```

and its service as:

```text
/etc/systemd/system/lbm-vdrc-job-nightly-erp.service
```

## Persistent execution

Timers use:

```ini
Persistent=true
RandomizedDelaySec=120
```

If a scheduled run is missed while the controller is powered off, `systemd` can run it after the controller returns.

## Change a schedule

```bash
sudo lbm-vdrc job enable nightly-erp --schedule '*-*-* 03:30:00'
```

## Disable

```bash
sudo lbm-vdrc job disable nightly-erp
```

## Run immediately

```bash
sudo lbm-vdrc job run nightly-erp
```

## Inspect all timers

```bash
systemctl list-timers 'lbm-vdrc-job-*' --all
```

## Inspect one service

```bash
systemctl status lbm-vdrc-job-nightly-erp.service
journalctl -u lbm-vdrc-job-nightly-erp.service
```

## Migration schedules

The scheduler accepts migration jobs as well. In version 1.0.0, migration jobs are safety-locked to planning/preflight, so a recurring migration timer repeats the planning/preflight workflow, **not an automatic destructive cutover**.

Designed & Developed by **antonios.mortos@outlook.com**
