from __future__ import annotations
import json, os, logging, subprocess, shlex, tempfile, re, shutil
from pathlib import Path
from typing import Any

APP_NAME = "LINUX BACKUP MANAGER - VIRTUALIZATION & DISASTER RECOVERY CENTER"
AUTHOR = "Designed & Developed by antonios.mortos@outlook.com"
ETC = Path(os.getenv("LBMVDRC_ETC", "/etc/lbm-vdrc"))
STATE = Path(os.getenv("LBMVDRC_STATE", "/var/lib/lbm-vdrc"))
LOGDIR = Path(os.getenv("LBMVDRC_LOG", "/var/log/lbm-vdrc"))
RUNDIR = Path(os.getenv("LBMVDRC_RUN", "/run/lbm-vdrc"))
MOUNT_ROOT = Path(os.getenv("LBMVDRC_MOUNTS", "/mnt/lbm-vdrc"))
PATHS = {
    "hypervisors": ETC / "hypervisors.json",
    "storage": ETC / "storage.json",
    "jobs": ETC / "jobs.json",
    "settings": ETC / "settings.json",
    "secrets": ETC / "secrets.json",
    "history": STATE / "history.jsonl",
}

def ensure_dirs():
    for p in (ETC, STATE, LOGDIR, RUNDIR, MOUNT_ROOT):
        p.mkdir(parents=True, exist_ok=True)
    for p, mode in ((ETC,0o700),(STATE,0o700),(RUNDIR,0o700)):
        try: os.chmod(p, mode)
        except PermissionError: pass
    if not PATHS["secrets"].exists():
        save_json(PATHS["secrets"], {})
        try: os.chmod(PATHS["secrets"], 0o600)
        except PermissionError: pass

def load_json(path: Path, default: Any):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError): return default

def save_json(path: Path, data: Any, mode: int=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name+".", dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=2,ensure_ascii=False); f.write("
")
        os.chmod(tmp, mode); os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def require_root():
    if os.geteuid()!=0: raise PermissionError("This operation requires root. Re-run with sudo.")

def command_exists(name): return shutil.which(name) is not None

def run(cmd, *, check=True, capture=True, env=None, input_text=None, timeout=None):
    if isinstance(cmd,str): cmd=shlex.split(cmd)
    cp=subprocess.run(cmd,text=True,capture_output=capture,env=env,input=input_text,timeout=timeout)
    if check and cp.returncode!=0:
        raise RuntimeError(f"Command failed ({cp.returncode}): {' '.join(cmd)}
{(cp.stderr or cp.stdout or '').strip()}")
    return cp

def now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def history(event):
    ensure_dirs(); event={"time":now_iso(),**event}
    with PATHS["history"].open("a",encoding="utf-8") as f: f.write(json.dumps(event,ensure_ascii=False)+"
")

def safe_name(value):
    value=re.sub(r"[^A-Za-z0-9._-]+","-",value.strip())
    return value.strip("-")[:64]

def logger():
    ensure_dirs(); log=logging.getLogger("lbm-vdrc")
    if not log.handlers:
        log.setLevel(logging.INFO)
        h=logging.FileHandler(LOGDIR/"lbm-vdrc.log")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s")); log.addHandler(h)
    return log
