import platform,shutil
from .core import PATHS,ensure_dirs,load_json
COMMANDS=[("mount","Core mount utility",True),("findmnt","Mount verification",True),("systemctl","Job scheduler",True),("ssh","Remote access",True),("scp","Hyper-V transfer",False),("sshpass","Password-only Proxmox cold-copy wizard",False),("mount.nfs","NFS support",False),("mount.cifs","SMB/CIFS support",False),("iscsiadm","iSCSI support",False),("govc","VMware connector",False),("qemu-img","Disk conversion",False)]
def report():
    ensure_dirs();rows=[]
    for cmd,desc,req in COMMANDS:rows.append({"name":cmd,"description":desc,"required":req,"ok":bool(shutil.which(cmd)),"path":shutil.which(cmd) or ""})
    return {"platform":platform.platform(),"python":platform.python_version(),"commands":rows,"hypervisors":len(load_json(PATHS["hypervisors"],{})),"storage_targets":len(load_json(PATHS["storage"],{})),"jobs":len(load_json(PATHS["jobs"],{}))}
