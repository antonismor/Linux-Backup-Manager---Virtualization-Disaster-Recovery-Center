from __future__ import annotations
import json,os
from .base import Hypervisor,VM
from ..core import run,command_exists
class ESXi(Hypervisor):
    def _env(self):
        e=os.environ.copy();sec=self.secrets
        e["GOVC_URL"]=self.cfg["host"];e["GOVC_USERNAME"]=sec.get("username",self.cfg.get("username",""));e["GOVC_PASSWORD"]=sec.get("password","");e["GOVC_INSECURE"]="0" if self.cfg.get("verify_tls",True) else "1";return e
    def test(self):
        if not command_exists("govc"):return {"ok":False,"error":"govc is not installed"}
        return {"ok":True,"about":json.loads(run(["govc","about","-json"],env=self._env()).stdout)}
    def list_vms(self):
        if not command_exists("govc"):raise RuntimeError("govc is required for ESXi/vCenter inventory.")
        paths=[x.strip() for x in run(["govc","find","-type","m"],env=self._env()).stdout.splitlines() if x.strip()];out=[]
        for path in paths:
            d=json.loads(run(["govc","vm.info","-json",path],env=self._env()).stdout);vms=d.get("VirtualMachines") or d.get("virtualMachines") or []
            if not vms:continue
            x=vms[0];cfg=x.get("Config",x.get("config",{})) or {};rt=x.get("Runtime",x.get("runtime",{})) or {};hw=cfg.get("Hardware",cfg.get("hardware",{})) or {};name=cfg.get("Name",cfg.get("name",path.split("/")[-1]))
            out.append(VM(name,name,str(rt.get("PowerState",rt.get("powerState","unknown"))).upper(),hw.get("NumCPU",hw.get("numCPU",0)),(int(hw.get("MemoryMB",hw.get("memoryMB",0)) or 0)*1024*1024),0,self.cfg["host"],{"path":path}))
        return out
    def export_ovf(self,vm_path,destination):run(["govc","export.ovf","-vm",vm_path,str(destination)],env=self._env(),capture=False)
