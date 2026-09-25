from __future__ import annotations
import argparse,json,getpass,sys
from types import SimpleNamespace
from . import __version__
from .core import *
from .ui import Screen,menu,status,table_row,GREEN,RED,YELLOW,RESET
from .secrets import SecretStore
from .storage import *
from .hypervisors import configs as hv_configs,get as get_hv
from .jobs import all_jobs,save_job,run_job
from .scheduler import install_job_timer,remove_job_timer
from .doctor import report as doctor_report
from .migrations import (
    test_proxmox_host,
    list_qemu_vms,
    list_image_storages,
    choose_target_vmid,
    cold_copy_vm,
)

def fmt_bytes(n):
    try:n=float(n)
    except:return str(n)
    u=["B","KB","MB","GB","TB"];i=0
    while n>=1024 and i<len(u)-1:n/=1024;i+=1
    return f"{n:.1f} {u[i]}"
def prompt(label,default=""):
    x=input(f"{label} [{default}]: ").strip();return x or default
def yesno(label,default=True):
    x=input(f"{label} {'[Y/n]' if default else '[y/N]'}: ").strip().lower();return default if not x else x.startswith('y')

def dashboard_lines():
    cfgs=hv_configs();lines=[table_row(["#","HOST","PLATFORM","ADDRESS","VMs","STATE"],[3,15,23,18,6,14]),"  "+"─"*94];i=1
    for name,cfg in cfgs.items():
        try:vms=str(len(get_hv(name).list_vms()));st="ONLINE"
        except Exception:vms="?";st="OFFLINE"
        platform={"proxmox":"Proxmox VE","pve":"Proxmox VE","esxi":"VMware ESXi","vmware":"VMware ESXi","vcenter":"VMware vCenter","hyperv":"Microsoft Hyper-V","hyper-v":"Microsoft Hyper-V"}.get(cfg.get("type","").lower(),cfg.get("type",""))
        lines.append(table_row([i,name,platform,cfg.get("host",""),vms,status(st)],[3,15,23,18,6,14]));i+=1
    if not cfgs:lines.append("  No hypervisors configured. Add one with: lbm-vdrc hypervisor add NAME")
    return lines
MAIN=["Hypervisor Hosts","Virtual Machines","Backup VM","Restore VM","VM Migration","Disk Conversion","Network Mapping","Storage Mapping","Scheduled Jobs","Migration History","Backup History","Email Reports","Credential Vault","Doctor / Diagnostics","Settings","Exit"]

def show_text(title,lines):
    s=Screen();s.clear();s.header(title);s.section(title)
    for line in lines:s.section_row(line)
    s.section_end();s.footer();input("\nPress ENTER to continue...")
def tui():
    while True:
        idx=menu(MAIN,subtitle="Backup • Restore • Convert • Migrate • Disaster Recovery",dashboard_lines=dashboard_lines())
        if idx is None or MAIN[idx]=="Exit":print(RESET);return
        c=MAIN[idx]
        try:
            if c=="Hypervisor Hosts":tui_hv()
            elif c=="Virtual Machines":tui_vms()
            elif c=="Storage Mapping":tui_storage()
            elif c=="Scheduled Jobs":tui_jobs()
            elif c=="Credential Vault":tui_credentials()
            elif c=="Doctor / Diagnostics":tui_doctor()
            elif c=="Backup VM":tui_backup_wizard()
            elif c=="VM Migration":tui_migration_wizard()
            elif c in ("Backup History","Migration History"):tui_history(c)
            elif c=="Email Reports":tui_email()
            elif c=="Settings":tui_settings()
            else:show_text(c,["Module reserved for a later validated backend release."])
        except Exception as e:show_text("ERROR",str(e).splitlines())
def tui_hv():
    while True:
        cfgs=hv_configs(); lines=[]
        for n,c in cfgs.items():
            try:st="ONLINE" if get_hv(n).test().get("ok") else "OFFLINE"
            except Exception:st="OFFLINE"
            lines.append(table_row([n,c.get("type",""),c.get("host",""),status(st)],[18,22,30,16]))
        actions=["Add Hypervisor","Test Hypervisor","View Inventory","Back"]
        idx=menu(actions,title="HYPERVISOR HOSTS",subtitle=f"Configured hosts: {len(cfgs)}",dashboard_lines=lines or ["  No hypervisors configured."])
        if idx is None or actions[idx]=="Back":return
        if actions[idx]=="Add Hypervisor":
            name=prompt("Hypervisor profile name","PVE01")
            hv_add(SimpleNamespace(name=name,type=None,host=None,credential=None,insecure=False))
        elif actions[idx]=="Test Hypervisor":
            names=list(cfgs)
            if not names: show_text("TEST HYPERVISOR",["No hypervisors configured."]); continue
            j=menu(names+["Back"],title="SELECT HYPERVISOR")
            if j is None or j>=len(names): continue
            show_text("CONNECTION TEST",json.dumps(get_hv(names[j]).test(),indent=2,default=str).splitlines())
        elif actions[idx]=="View Inventory":
            tui_vms()

def tui_vms():
    names=list(hv_configs())
    if not names:return show_text("VIRTUAL MACHINES",["No hypervisors configured."])
    idx=menu(names+["Back"],title="SELECT HYPERVISOR")
    if idx is None or idx>=len(names):return
    n=names[idx];vms=get_hv(n).list_vms();lines=[table_row(["ID","NAME","STATE","CPU","MEMORY","NODE"],[8,28,15,7,14,16]),"  "+"─"*94]
    for v in vms:lines.append(table_row([v.id,v.name,status(v.state),v.cpu,fmt_bytes(v.memory),v.node],[8,28,15,7,14,16]))
    show_text(f"VIRTUAL MACHINES - {n}",lines)

def tui_storage():
    while True:
        targets=all_targets()
        lines=[table_row(["NAME","TYPE","LOCATION"],[20,12,60]),"  "+"─"*96]
        for n,c in targets.items():
            loc=c.get("path") or c.get("share") or ((c.get("host","")+":"+c.get("export","")) if c.get("host") else c.get("portal",""))
            lines.append(table_row([n,c.get("type",""),loc],[20,12,60]))
        actions=["Add Storage Target","Test Storage Target","Mount Storage Target","Unmount Storage Target","Back"]
        idx=menu(actions,title="STORAGE MAPPING",subtitle=f"Configured targets: {len(targets)}",dashboard_lines=lines)
        if idx is None or actions[idx]=="Back":return
        if actions[idx]=="Add Storage Target":
            name=prompt("Storage profile name","backup-nfs")
            storage_add(SimpleNamespace(name=name,type=None))
        else:
            names=list(targets)
            if not names: show_text("STORAGE",["No storage targets configured."]); continue
            j=menu(names+["Back"],title="SELECT STORAGE TARGET")
            if j is None or j>=len(names):continue
            name=names[j]
            if actions[idx]=="Test Storage Target":show_text("STORAGE TEST",json.dumps(test_target(name),indent=2).splitlines())
            elif actions[idx]=="Mount Storage Target":show_text("STORAGE MOUNT",[str(mount_target(name))])
            elif actions[idx]=="Unmount Storage Target":unmount_target(name);show_text("STORAGE UNMOUNT",[f"Unmounted: {name}"])

def tui_jobs():
    while True:
        jobs=all_jobs()
        lines=[table_row(["NAME","TYPE","SOURCE","TARGET","SCHEDULE"],[22,12,18,18,28]),"  "+"─"*102]
        for n,c in jobs.items():lines.append(table_row([n,c.get("type"),c.get("source_hypervisor",""),c.get("storage",""),c.get("schedule","manual")],[22,12,18,18,28]))
        actions=["Create Backup Job","Create Migration Job","Run Job Now","Enable / Update Schedule","Disable Schedule","Back"]
        idx=menu(actions,title="SCHEDULED JOBS",subtitle=f"Configured jobs: {len(jobs)}",dashboard_lines=lines)
        if idx is None or actions[idx]=="Back":return
        act=actions[idx]
        if act=="Create Backup Job":tui_backup_wizard();continue
        if act=="Create Migration Job":tui_migration_wizard();continue
        names=list(jobs)
        if not names:show_text("JOBS",["No jobs configured."]);continue
        j=menu(names+["Back"],title="SELECT JOB")
        if j is None or j>=len(names):continue
        name=names[j]
        if act=="Run Job Now":show_text("JOB RESULT",json.dumps(run_job(name),indent=2,default=str).splitlines())
        elif act=="Enable / Update Schedule":
            sched=prompt("systemd OnCalendar",jobs[name].get("schedule","*-*-* 02:00:00"))
            show_text("SCHEDULE",json.dumps(install_job_timer(name,sched),indent=2).splitlines())
        elif act=="Disable Schedule":remove_job_timer(name);show_text("SCHEDULE",[f"Disabled: {name}"])

def tui_credentials():
    while True:
        names=list(SecretStore().all())
        actions=["Add Credential Profile","List Credential Profiles","Delete Credential Profile","Back"]
        idx=menu(actions,title="CREDENTIAL VAULT",subtitle=f"Stored profiles: {len(names)}",dashboard_lines=[f"  • {x}" for x in names] or ["  No credential profiles stored."])
        if idx is None or actions[idx]=="Back":return
        if actions[idx]=="Add Credential Profile":
            name=prompt("Credential profile name","backup-credential")
            credential_add(SimpleNamespace(name=name,type=None,username=None,password=None))
        elif actions[idx]=="List Credential Profiles":show_text("CREDENTIAL VAULT",[f"  • {x}" for x in names] or ["No credentials stored."])
        else:
            if not names:show_text("CREDENTIAL VAULT",["No credentials stored."]);continue
            j=menu(names+["Back"],title="DELETE CREDENTIAL")
            if j is None or j>=len(names):continue
            if yesno(f"Delete credential profile {names[j]}",False):SecretStore().delete(names[j])

def tui_backup_wizard():
    print(RESET)
    job_add_backup(SimpleNamespace(name=None))
    input("Press ENTER to return to the dashboard...")

def _migration_progress(step, total, title, detail=""):
    bar_width=28
    filled=max(1,min(bar_width,int((step/total)*bar_width)))
    bar="█"*filled+"░"*(bar_width-filled)
    suffix=f"  {DIM}{detail}{RESET}" if detail else ""
    print(f"{CYAN}[{step:02d}/{total:02d}]{RESET} {GREEN}{bar}{RESET} {BOLD}{title}{RESET}{suffix}",flush=True)

def tui_pve_copy_wizard():
    require_root()
    if not command_exists("sshpass"):
        return show_text("PROXMOX → PROXMOX COLD COPY",[
            "sshpass is required for the password-only wizard.",
            "Debian/Ubuntu: sudo apt install -y openssh-client sshpass",
            "",
            "No configuration was changed."
        ])

    s=Screen();s.clear();s.header("Independent Proxmox hosts • Cold copy • Source preserved")
    s.section("SOURCE PROXMOX")
    s.section_row("Enter the source host details. Credentials are kept in memory only.")
    s.section_end();s.footer("● WAITING FOR SOURCE")
    print()
    src_host=prompt("Source Proxmox IP / hostname","")
    src_user=prompt("Source username","root")
    src_password=getpass.getpass("Source password: ")
    if not src_host or not src_user or not src_password:
        return show_text("CANCELLED",["Source host, username and password are required."])

    print(CYAN+"Connecting to source..."+RESET)
    src_info=test_proxmox_host(src_host,src_user,src_password)
    vms=list_qemu_vms(src_host,src_user,src_password)
    if not vms:
        return show_text("SOURCE INVENTORY",["No QEMU virtual machines were found on the source host."])

    vm_labels=[]
    for v in vms:
        state=str(v.get("status","unknown")).upper()
        vm_labels.append(
            f"{v['vmid']:>5}  {v['name']:<34}  {state:<9}  "
            f"CPU {v.get('cpu',0):>2}  RAM {fmt_bytes(v.get('memory',0)):>10}  "
            f"DISK {fmt_bytes(v.get('disk',0)):>10}"
        )
    idx=menu(
        vm_labels+["Back"],
        title="SELECT SOURCE VM",
        subtitle=f"{src_info['hostname']} • {src_info['version']}"
    )
    if idx is None or idx>=len(vms):return
    vm=vms[idx]
    if str(vm.get("status","")).lower()!="stopped":
        return show_text("SAFETY STOP",[
            f"VM {vm['vmid']} - {vm['name']} is {str(vm.get('status')).upper()}.",
            "",
            "This migration mode copies only a VM that is already powered off.",
            "The program did not shut down or modify the source VM."
        ])

    s=Screen();s.clear();s.header("Independent Proxmox hosts • Cold copy • Source preserved")
    s.section("DESTINATION PROXMOX")
    s.section_row("Enter the destination host details. Credentials are kept in memory only.")
    s.section_end();s.footer("● WAITING FOR DESTINATION")
    print()
    dst_host=prompt("Destination Proxmox IP / hostname","")
    dst_user=prompt("Destination username","root")
    dst_password=getpass.getpass("Destination password: ")
    if not dst_host or not dst_user or not dst_password:
        return show_text("CANCELLED",["Destination host, username and password are required."])

    print(CYAN+"Connecting to destination..."+RESET)
    dst_info=test_proxmox_host(dst_host,dst_user,dst_password)
    storages=list_image_storages(dst_host,dst_user,dst_password)
    if not storages:
        return show_text("DESTINATION STORAGE",[
            "No active destination storage supporting VM images was found."
        ])

    storage_labels=[
        f"{x['storage']:<24} {x.get('type',''):<12} "
        f"FREE {fmt_bytes(x.get('avail',0)):>10} / {fmt_bytes(x.get('total',0)):>10}"
        for x in storages
    ]
    st_idx=menu(
        storage_labels+["Back"],
        title="SELECT DESTINATION STORAGE",
        subtitle=f"{dst_info['hostname']} • {dst_info['version']}"
    )
    if st_idx is None or st_idx>=len(storages):return
    storage=storages[st_idx]

    proposed_vmid=choose_target_vmid(dst_host,dst_user,dst_password,int(vm["vmid"]))
    vmid_text=prompt("Destination VMID",str(proposed_vmid))
    try:target_vmid=int(vmid_text)
    except ValueError:return show_text("INVALID VMID",[f"Invalid VMID: {vmid_text}"])

    summary=[
        f"Source      : {src_info['hostname']} ({src_host})",
        f"Source VM   : {vm['vmid']} - {vm['name']} [{str(vm['status']).upper()}]",
        f"Destination : {dst_info['hostname']} ({dst_host})",
        f"Target VMID : {target_vmid}",
        f"Storage     : {storage['storage']} ({fmt_bytes(storage.get('avail',0))} free)",
        "",
        "Method      : vzdump → controller staging → SHA256 → destination → qmrestore",
        "Source VM   : PRESERVED and remains OFF",
        "Target VM   : RESTORED but NOT automatically started",
        "",
        "Passwords are not stored in configuration or migration history."
    ]
    s=Screen();s.clear();s.header("PROXMOX → PROXMOX COLD COPY")
    s.section("MIGRATION SUMMARY")
    for line in summary:s.section_row(line)
    s.section_end();s.footer("● READY TO COPY")
    print()
    if not yesno("Start cold copy now",False):
        return show_text("CANCELLED",["No migration action was performed."])

    source={"host":src_host,"username":src_user,"password":src_password}
    destination={"host":dst_host,"username":dst_user,"password":dst_password}
    print()
    try:
        result=cold_copy_vm(
            source=source,
            destination=destination,
            vm=vm,
            target_storage=storage["storage"],
            target_vmid=target_vmid,
            progress=_migration_progress,
        )
    finally:
        source["password"]=""
        destination["password"]=""
        src_password=""
        dst_password=""

    lines=[
        GREEN+"COPY COMPLETED SUCCESSFULLY"+RESET,
        "",
        f"Source VM      : {result['source']['host']} / {result['source']['vmid']} / STOPPED / PRESERVED",
        f"Destination VM : {result['destination']['host']} / {result['destination']['vmid']} / {result['destination']['vm_status'].upper()}",
        f"Target storage : {result['destination']['storage']}",
        f"SHA256         : {result['sha256']}",
        f"Controller copy: {result['controller_staging']}",
        "",
        "The destination VM was NOT started automatically."
    ]
    if result.get("missing_bridges"):
        lines += [
            "",
            YELLOW+"NETWORK WARNING"+RESET,
            "Missing destination bridge(s): "+", ".join(result["missing_bridges"]),
            "Map the VM network before starting the restored VM."
        ]
    show_text("PROXMOX → PROXMOX COLD COPY",lines)

def tui_migration_wizard():
    actions=[
        "Proxmox → Proxmox Cold Copy (Independent Hosts)",
        "Generic Migration Plan / Preflight",
        "Back",
    ]
    idx=menu(actions,title="VM MIGRATION",subtitle="Safe migration workflows")
    if idx is None or actions[idx]=="Back":return
    if idx==0:return tui_pve_copy_wizard()
    print(RESET)
    job_add_migration(SimpleNamespace(name=None))
    input("Press ENTER to return to the dashboard...")

def tui_email():
    actions=["Configure SMTP","Show Email Status","Back"]
    idx=menu(actions,title="EMAIL REPORTS")
    if idx is None or actions[idx]=="Back":return
    if actions[idx]=="Configure SMTP":email_configure();input("Press ENTER to continue...")
    else:
        cfg=load_json(PATHS["settings"],{}).get("email",{})
        safe={k:v for k,v in cfg.items() if k!="password"}
        show_text("EMAIL STATUS",json.dumps(safe,indent=2).splitlines() if safe else ["Email is not configured."])

def tui_settings():
    show_text("SETTINGS",[
        f"Configuration : {ETC}",
        f"State         : {STATE}",
        f"Logs          : {LOGDIR}",
        f"Managed mounts: {MOUNT_ROOT}",
        "",
        "All recurring jobs are implemented as systemd timers, not a sleeping daemon."
    ])
def tui_doctor():
    d=doctor_report();lines=[f"Platform: {d['platform']}",f"Python:   {d['python']}",""]
    for x in d["commands"]:
        mark=(GREEN+"✓"+RESET) if x["ok"] else ((RED+"✗"+RESET) if x["required"] else (YELLOW+"!"+RESET));lines.append(f"  {mark} {x['name']:<14} {x['description']}")
    show_text("DOCTOR / DIAGNOSTICS",lines)
def tui_history(kind):
    rows=[];p=PATHS["history"]
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines()[-40:]:
            try:
                x=json.loads(line)
                if "Migration" in kind and "migration" not in str(x).lower():continue
                rows.append(f"{x.get('time','')}  {x.get('event',''):<14}  {x.get('job','')}")
            except:pass
    show_text(kind.upper(),rows or ["No matching history yet."])

def credential_add(args):
    require_root();typ=args.type or prompt("Credential type","generic");user=args.username or prompt("Username","");pw=args.password or getpass.getpass("Password / secret: ");d={"type":typ,"username":user,"password":pw}
    if typ=="proxmox" and yesno("Use API token instead of password",False):d["token_id"]=prompt("Token ID","lbm");d["token_secret"]=getpass.getpass("Token secret: ")
    if typ=="smb":d["domain"]=prompt("Domain","")
    SecretStore().set(args.name,d);print("Saved credential profile:",args.name)
def hv_add(args):
    require_root();d=load_json(PATHS["hypervisors"],{});typ=args.type or prompt("Type (proxmox/esxi/hyperv)","proxmox");host=args.host or prompt("Host / IP","");cred=args.credential or prompt("Credential profile","");cfg={"type":typ,"host":host,"credential":cred,"verify_tls":not args.insecure}
    if typ=="proxmox":cfg["port"]=int(prompt("API port","8006"))
    d[args.name]=cfg;save_json(PATHS["hypervisors"],d);print("Saved hypervisor:",args.name)
def storage_add(args):
    require_root();typ=args.type or prompt("Type (local/nfs/smb/iscsi)","nfs");cfg={"type":typ}
    if typ=="local":cfg["path"]=prompt("Path","/backup")
    elif typ=="nfs":cfg.update(host=prompt("NFS host",""),export=prompt("NFS export","/export/backups"),options=prompt("Mount options","rw,hard,timeo=600,retrans=2,_netdev"))
    elif typ=="smb":cfg.update(share=prompt("SMB share","//server/backups"),credential=prompt("Credential profile",""),vers=prompt("SMB version","3.1.1"),options=prompt("Extra options","rw"))
    elif typ=="iscsi":
        cfg.update(portal=prompt("iSCSI portal","10.0.0.10:3260"),iqn=prompt("Target IQN",""),credential=prompt("CHAP credential profile (optional)",""));cfg["uuid"]=prompt("Filesystem UUID (preferred)","")
        if not cfg["uuid"]:cfg["device"]=prompt("Device path","/dev/sdb1")
        cfg["fstype"]=prompt("Filesystem type","auto");cfg["options"]=prompt("Mount options","rw,_netdev")
    else:raise ValueError("Unsupported storage type")
    save_target(args.name,cfg);print("Saved storage target:",args.name)
def job_add_backup(args):
    require_root();name=args.name or prompt("Job name","vm-backup");cfg={"type":"backup","source_hypervisor":prompt("Source hypervisor",""),"vm":prompt("VM name or ID",""),"storage":prompt("LBM storage target",""),"schedule":prompt("systemd OnCalendar schedule","*-*-* 02:00:00")}
    if hv_configs().get(cfg["source_hypervisor"],{}).get("type","").lower() in ("proxmox","pve"):
        cfg.update(pve_storage=prompt("Proxmox storage ID for vzdump",""),mode=prompt("vzdump mode","snapshot"),compress=prompt("Compression","zstd"))
    save_job(name,cfg)
    if yesno("Install/enable systemd timer now",True):print(json.dumps(install_job_timer(name,cfg["schedule"]),indent=2))
    print("Saved backup job:",name)
def job_add_migration(args):
    require_root();name=args.name or prompt("Job name","vm-migration");cfg={"type":"migration","source_hypervisor":prompt("Source hypervisor",""),"destination_hypervisor":prompt("Destination hypervisor",""),"vm":prompt("VM name or ID",""),"storage":prompt("Staging storage target",""),"mode":"plan","safety_backup":True,"schedule":prompt("systemd OnCalendar schedule or manual","manual"),"allow_experimental_execution":False};save_job(name,cfg)
    if cfg["schedule"]!="manual" and yesno("Recurring migrations can create repeated copies. Install timer anyway",False):print(json.dumps(install_job_timer(name,cfg["schedule"]),indent=2))
    print("Saved safety-locked migration job:",name)
def email_configure():
    require_root();s=load_json(PATHS["settings"],{});s["email"]={"enabled":True,"host":prompt("SMTP server",""),"port":int(prompt("SMTP port","587")),"security":prompt("Security (starttls/ssl/none)","starttls"),"from":prompt("From address",""),"to":prompt("Recipient address",""),"credential":prompt("SMTP credential profile","")};save_json(PATHS["settings"],s);print("Email reporting configured.")

def parser():
    p=argparse.ArgumentParser(prog="lbm-vdrc",description=APP_NAME);p.add_argument("--version",action="version",version=f"%(prog)s {__version__}");sub=p.add_subparsers(dest="cmd")
    s=sub.add_parser("credential");ss=s.add_subparsers(dest="action");a=ss.add_parser("add");a.add_argument("name");a.add_argument("--type");a.add_argument("--username");a.add_argument("--password");ss.add_parser("list")
    s=sub.add_parser("hypervisor");ss=s.add_subparsers(dest="action");a=ss.add_parser("add");a.add_argument("name");a.add_argument("--type");a.add_argument("--host");a.add_argument("--credential");a.add_argument("--insecure",action="store_true");ss.add_parser("list");a=ss.add_parser("test");a.add_argument("name");a=ss.add_parser("vms");a.add_argument("name")
    s=sub.add_parser("storage");ss=s.add_subparsers(dest="action");a=ss.add_parser("add");a.add_argument("name");a.add_argument("--type");ss.add_parser("list");a=ss.add_parser("test");a.add_argument("name");a=ss.add_parser("mount");a.add_argument("name");a=ss.add_parser("unmount");a.add_argument("name")
    s=sub.add_parser("job");ss=s.add_subparsers(dest="action");a=ss.add_parser("add-backup");a.add_argument("name",nargs="?");a=ss.add_parser("add-migration");a.add_argument("name",nargs="?");ss.add_parser("list");a=ss.add_parser("run");a.add_argument("name");a=ss.add_parser("enable");a.add_argument("name");a.add_argument("--schedule");a=ss.add_parser("disable");a.add_argument("name")
    s=sub.add_parser("email");ss=s.add_subparsers(dest="action");ss.add_parser("configure");sub.add_parser("doctor");sub.add_parser("pve-copy",help="Interactive Proxmox to Proxmox cold-copy wizard");sub.add_parser("tui");return p

def main(argv=None):
    p=parser();a=p.parse_args(argv);ensure_dirs()
    if not a.cmd or a.cmd=="tui":return tui()
    if a.cmd=="credential":
        if a.action=="add":return credential_add(a)
        if a.action=="list":print("\n".join(SecretStore().all()));return
    if a.cmd=="hypervisor":
        if a.action=="add":return hv_add(a)
        if a.action=="list":print(json.dumps(hv_configs(),indent=2));return
        if a.action=="test":print(json.dumps(get_hv(a.name).test(),indent=2,default=str));return
        if a.action=="vms":print(json.dumps([v.asdict() for v in get_hv(a.name).list_vms()],indent=2,default=str));return
    if a.cmd=="storage":
        if a.action=="add":return storage_add(a)
        if a.action=="list":print(json.dumps(all_targets(),indent=2));return
        if a.action=="test":print(json.dumps(test_target(a.name),indent=2));return
        if a.action=="mount":print(mount_target(a.name));return
        if a.action=="unmount":return unmount_target(a.name)
    if a.cmd=="job":
        if a.action=="add-backup":return job_add_backup(a)
        if a.action=="add-migration":return job_add_migration(a)
        if a.action=="list":print(json.dumps(all_jobs(),indent=2));return
        if a.action=="run":print(json.dumps(run_job(a.name),indent=2,default=str));return
        if a.action=="enable":
            cfg=all_jobs().get(a.name) or {};sched=a.schedule or cfg.get("schedule")
            if not sched or sched=="manual":raise RuntimeError("No schedule defined")
            print(json.dumps(install_job_timer(a.name,sched),indent=2));return
        if a.action=="disable":return remove_job_timer(a.name)
    if a.cmd=="email" and a.action=="configure":return email_configure()
    if a.cmd=="doctor":print(json.dumps(doctor_report(),indent=2));return
    if a.cmd=="pve-copy":return tui_pve_copy_wizard()
    p.print_help()
if __name__=="__main__":
    try:main()
    except KeyboardInterrupt:print("\nCancelled.",file=sys.stderr);sys.exit(130)
    except Exception as e:logger().exception("Fatal error");print(f"ERROR: {e}",file=sys.stderr);sys.exit(1)
