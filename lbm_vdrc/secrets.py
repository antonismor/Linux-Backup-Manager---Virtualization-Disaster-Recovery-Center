from __future__ import annotations
import getpass, os
from .core import PATHS, load_json, save_json, ensure_dirs

class SecretStore:
    def __init__(self):
        ensure_dirs(); self.path=PATHS["secrets"]
    def all(self): return load_json(self.path,{})
    def get(self,name): return self.all().get(name,{})
    def set(self,name,fields):
        data=self.all(); data[name]=fields; save_json(self.path,data,0o600)
        try: os.chmod(self.path,0o600)
        except PermissionError: pass
    def delete(self,name):
        data=self.all(); data.pop(name,None); save_json(self.path,data,0o600)
