from pathlib import Path
from .core import require_root,run,safe_name
SYSTEMD=Path("/etc/systemd/system")
def install_job_timer(job,oncalendar):
    require_root();safe=safe_name(job);svc=SYSTEMD/f"lbm-vdrc-job-{safe}.service";timer=SYSTEMD/f"lbm-vdrc-job-{safe}.timer"
    svc.write_text(f'''[Unit]
Description=LBM-VDRC job {job}
After=network-online.target remote-fs.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/lbm-vdrc job run {job}
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
TimeoutStartSec=infinity
''',encoding="utf-8")
    timer.write_text(f'''[Unit]
Description=LBM-VDRC schedule for {job}

[Timer]
OnCalendar={oncalendar}
Persistent=true
RandomizedDelaySec=120
Unit=lbm-vdrc-job-{safe}.service

[Install]
WantedBy=timers.target
''',encoding="utf-8")
    run(["systemctl","daemon-reload"]);run(["systemctl","enable","--now",timer.name]);return {"service":svc.name,"timer":timer.name}
def remove_job_timer(job):
    require_root();safe=safe_name(job);timer=f"lbm-vdrc-job-{safe}.timer";svc=f"lbm-vdrc-job-{safe}.service";run(["systemctl","disable","--now",timer],check=False)
    for p in (SYSTEMD/timer,SYSTEMD/svc):
        try:p.unlink()
        except FileNotFoundError:pass
    run(["systemctl","daemon-reload"])
