from dataclasses import dataclass,asdict
@dataclass
class VM:
    id:str; name:str; state:str; cpu:int|str=0; memory:int|str=0; disk:int|str=0; node:str=""; extra:dict|None=None
    def asdict(self):return asdict(self)
class Hypervisor:
    def __init__(self,name,cfg,secrets):self.name,self.cfg,self.secrets=name,cfg,secrets
    def test(self):raise NotImplementedError
    def list_vms(self):raise NotImplementedError
