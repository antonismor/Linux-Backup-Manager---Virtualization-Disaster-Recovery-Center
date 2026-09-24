from __future__ import annotations
import json
from .base import Hypervisor,VM
from ..core import run,command_exists
class HyperV(Hypervisor):
    def _ssh(self):
        sec=self.secrets;user=sec.get("username",self.cfg.get("username","Administrator"));p=[]
        if sec.get("password"):
            if not command_exists("sshpass"):raise RuntimeError("sshpass required for password SSH; SSH keys are preferred.")
            p=["sshpass","-p",sec["password"]]
        return p+["ssh","-o","StrictHostKeyChecking=accept-new",f'{user}@{self.cfg["host"]}']
    def powershell(self,script):return run(self._ssh()+["powershell.exe","-NoProfile","-NonInteractive","-Command",script])
    def test(self):return {"ok":True,"powershell":self.powershell("$PSVersionTable.PSVersion.ToString()").stdout.strip()}
    def list_vms(self):
        ps="Get-VM | Select-Object Id,Name,State,ProcessorCount,MemoryAssigned,ComputerName | ConvertTo-Json -Compress"
        txt=self.powershell(ps).stdout.strip()
        if not txt:return []
        data=json.loads(txt);data=[data] if isinstance(data,dict) else data;out=[]
        for x in data:out.append(VM(str(x.get("Id","")),x.get("Name",""),str(x.get("State","unknown")).upper(),x.get("ProcessorCount",0),int(x.get("MemoryAssigned",0) or 0),0,x.get("ComputerName",self.cfg["host"]),x))
        return out
