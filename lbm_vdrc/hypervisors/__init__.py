from .proxmox import Proxmox
from .esxi import ESXi
from .hyperv import HyperV
from ..core import PATHS,load_json
from ..secrets import SecretStore

def configs():return load_json(PATHS["hypervisors"],{})
def get(name):
    cfg=configs().get(name)
    if not cfg:raise KeyError(f"Unknown hypervisor: {name}")
    sec=SecretStore().get(cfg.get("credential",""));kind=cfg["type"].lower()
    if kind in ("proxmox","pve"):return Proxmox(name,cfg,sec)
    if kind in ("esxi","vmware","vcenter"):return ESXi(name,cfg,sec)
    if kind in ("hyperv","hyper-v"):return HyperV(name,cfg,sec)
    raise ValueError(f"Unsupported hypervisor type: {kind}")
