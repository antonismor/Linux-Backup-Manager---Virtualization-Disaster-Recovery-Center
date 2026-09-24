from __future__ import annotations
import json,urllib.parse,time
from pathlib import Path
from .core import PATHS,load_json,save_json,safe_name,history,run,command_exists
from .storage import mount_target
from .hypervisors import get as get_hv
from .emailer import send

def all_jobs():return load_json(PATHS["jobs"],{})
def save_job(name,cfg):
    d=all_jobs();d[name]=cfg;save_json(PATHS["jobs"],d)
def _job_dir(target,job,stamp):
    d=Path(target)/"lbm-vdrc"/safe_name(job)/stamp;d.mkdir(parents=True,exist_ok=True);return d

def backup_job(name,cfg):
    hv=get_hv(cfg["source_hypervisor"]);target=mount_target(cfg["storage"]);stamp=time.strftime("%Y%m%d-%H%M%S");out=_job_dir(target,name,stamp);vm_name=cfg["vm"];typ=hv.cfg["type"].lower()
    if typ in ("esxi","vmware","vcenter"):
        v=next((v for v in hv.list_vms() if v.name==vm_name or v.id==vm_name),None)
        if not v:raise RuntimeError(f"VM not found: {vm_name}")
        hv.export_ovf((v.extra or {}).get("path",vm_name),out);return {"output":str(out),"method":"govc export.ovf"}
    if typ in ("hyperv","hyper-v"):
        remote=cfg.get("remote_temp",f'C:\\LBM-VDRC\\{safe_name(name)}\\{stamp}')
        hv.powershell(f'New-Item -ItemType Directory -Force -Path "{remote}" | Out-Null; Export-VM -Name "{vm_name}" -Path "{remote}"')
        sec=hv.secrets;user=sec.get("username",hv.cfg.get("username","Administrator"));prefix=[]
        if sec.get("password"):
            if not command_exists("sshpass"):raise RuntimeError("sshpass required for password transfer.")
            prefix=["sshpass","-p",sec["password"]]
        remote_scp=remote.replace("\\","/")
        run(prefix+["scp","-r",f'{user}@{hv.cfg["host"]}:{remote_scp}/.',str(out)],capture=False)
        if cfg.get("cleanup_remote",True):hv.powershell(f'Remove-Item -LiteralPath "{remote}" -Recurse -Force')
        return {"output":str(out),"method":"Export-VM + SCP"}
    if typ in ("proxmox","pve"):
        pve_storage=cfg.get("pve_storage")
        if not pve_storage:raise RuntimeError("Proxmox backup requires a configured PVE storage ID. Add the NFS/CIFS/iSCSI target to Proxmox, then reference that storage ID in this job.")
        v=next((v for v in hv.list_vms() if v.name==vm_name or v.id==vm_name),None)
        if not v:raise RuntimeError(f"VM not found: {vm_name}")
        data={"vmid":v.id,"storage":pve_storage,"mode":cfg.get("mode","snapshot"),"compress":cfg.get("compress","zstd")}
        upid=hv._request(f"/nodes/{v.node}/vzdump",method="POST",data=data)
        encoded=urllib.parse.quote(str(upid), safe="")
        while True:
            st=hv._request(f"/nodes/{v.node}/tasks/{encoded}/status")
            if st.get("status")=="stopped":
                if st.get("exitstatus")!="OK":raise RuntimeError(f"Proxmox vzdump failed: {st.get('exitstatus')}")
                break
            time.sleep(5)
        (out/"proxmox-backup-receipt.json").write_text(json.dumps({"vm":v.asdict(),"pve_storage":pve_storage,"upid":upid},indent=2),encoding="utf-8")
        return {"output":str(out),"method":"Proxmox vzdump API","pve_storage":pve_storage}
    raise RuntimeError("Unsupported hypervisor backup backend.")

def migration_plan(name,cfg):
    src=get_hv(cfg["source_hypervisor"]);dst=get_hv(cfg["destination_hypervisor"]);vm=next((v for v in src.list_vms() if v.name==cfg["vm"] or v.id==cfg["vm"]),None)
    if not vm:raise RuntimeError(f"Source VM not found: {cfg['vm']}")
    return {"job":name,"source":src.name,"destination":dst.name,"vm":vm.asdict(),"cold_migration":True,"preserve_source":True,"safety_backup":cfg.get("safety_backup",True),"target_storage":cfg.get("storage"),"status":"READY_FOR_LAB_VALIDATION"}

def migration_job(name,cfg):
    plan=migration_plan(name,cfg)
    if cfg.get("mode","plan")=="plan":return plan
    if not cfg.get("allow_experimental_execution",False):raise RuntimeError("Cross-hypervisor execution is safety-locked. Use migration planning/preflight until the source→destination adapter is lab validated.")
    raise RuntimeError("Automatic cutover is intentionally not enabled in the v1.0.0 production baseline.")

def run_job(name):
    cfg=all_jobs().get(name)
    if not cfg:raise KeyError(f"Unknown job: {name}")
    start=time.time();history({"event":"job_start","job":name,"type":cfg["type"]})
    try:
        result=backup_job(name,cfg) if cfg["type"]=="backup" else migration_job(name,cfg);duration=int(time.time()-start)
        history({"event":"job_success","job":name,"duration":duration,"result":result})
        try:send(f"[LBM-VDRC] SUCCESS - {name}",f"Job: {name}\nType: {cfg['type']}\nStatus: SUCCESS\nDuration: {duration}s\nResult: {json.dumps(result,indent=2)}\n")
        except Exception:pass
        return result
    except Exception as e:
        duration=int(time.time()-start);history({"event":"job_failed","job":name,"duration":duration,"error":str(e)})
        try:send(f"[LBM-VDRC] FAILED - {name}",f"Job: {name}\nType: {cfg.get('type')}\nStatus: FAILED\nDuration: {duration}s\nError: {e}\n")
        except Exception:pass
        raise
