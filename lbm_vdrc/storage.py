from __future__ import annotations
import os,time
from pathlib import Path
from .core import PATHS,MOUNT_ROOT,load_json,save_json,run,require_root,safe_name
from .secrets import SecretStore

def all_targets(): return load_json(PATHS["storage"],{})
def save_target(name,cfg):
    d=all_targets(); d[name]=cfg; save_json(PATHS["storage"],d)
def delete_target(name):
    d=all_targets(); d.pop(name,None); save_json(PATHS["storage"],d)
def mountpoint(name): return MOUNT_ROOT/safe_name(name)
def mounted(path): return run(["findmnt","-rn",str(path)],check=False).returncode==0

def mount_target(name):
    require_root(); cfg=all_targets().get(name)
    if not cfg: raise KeyError(f"Unknown storage target: {name}")
    kind=cfg["type"].lower(); mp=mountpoint(name); mp.mkdir(parents=True,exist_ok=True)
    if kind=="local":
        p=Path(cfg["path"]); p.mkdir(parents=True,exist_ok=True); return p
    if mounted(mp): return mp
    if kind=="nfs":
        run(["mount","-t","nfs","-o",cfg.get("options","rw,hard,timeo=600,retrans=2,_netdev"),f'{cfg["host"]}:{cfg["export"]}',str(mp)])
        return mp
    if kind in ("smb","cifs","samba"):
        sec=SecretStore().get(cfg["credential"]); cred=Path("/run/lbm-vdrc")/f"cifs-{safe_name(name)}.cred"
        lines=[f'username={sec.get("username","")}',f'password={sec.get("password","")}']
        if sec.get("domain"):lines.append(f'domain={sec["domain"]}')
        cred.write_text("
".join(lines)+"
",encoding="utf-8"); os.chmod(cred,0o600)
        share=cfg["share"] if cfg["share"].startswith("//") else "//"+cfg["share"].lstrip("/")
        opts=f'credentials={cred},vers={cfg.get("vers","3.1.1")},iocharset=utf8,_netdev,{cfg.get("options","rw")}'
        try: run(["mount","-t","cifs",share,str(mp),"-o",opts])
        finally:
            try:cred.unlink()
            except FileNotFoundError:pass
        return mp
    if kind=="iscsi":
        sec=SecretStore().get(cfg.get("credential","")) if cfg.get("credential") else {}
        portal,iqn=cfg["portal"],cfg["iqn"]
        run(["iscsiadm","-m","discovery","-t","sendtargets","-p",portal],check=False)
        if sec.get("username"):
            base=["iscsiadm","-m","node","-T",iqn,"-p",portal]
            run(base+["--op=update","-n","node.session.auth.authmethod","-v","CHAP"])
            run(base+["--op=update","-n","node.session.auth.username","-v",sec["username"]])
            run(base+["--op=update","-n","node.session.auth.password","-v",sec["password"]])
        run(["iscsiadm","-m","node","-T",iqn,"-p",portal,"--login"],check=False); time.sleep(2)
        dev=f'UUID={cfg["uuid"]}' if cfg.get("uuid") else cfg.get("device")
        if not dev:raise RuntimeError("iSCSI target requires filesystem UUID or device path.")
        run(["mount","-t",cfg.get("fstype","auto"),"-o",cfg.get("options","rw,_netdev"),dev,str(mp)])
        return mp
    raise ValueError(f"Unsupported storage type: {kind}")

def unmount_target(name):
    require_root(); cfg=all_targets().get(name)
    if not cfg:return
    mp=mountpoint(name)
    if mounted(mp):run(["umount",str(mp)])
    if cfg["type"].lower()=="iscsi":run(["iscsiadm","-m","node","-T",cfg["iqn"],"-p",cfg["portal"],"--logout"],check=False)

def test_target(name):
    mp=mount_target(name); p=mp/f".lbm-vdrc-test-{os.getpid()}"; p.write_text("ok",encoding="utf-8"); p.unlink()
    st=os.statvfs(mp); return {"mountpoint":str(mp),"free_bytes":st.f_bavail*st.f_frsize}
