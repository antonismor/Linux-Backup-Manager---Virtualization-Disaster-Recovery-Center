from __future__ import annotations
import ssl,json,urllib.request,urllib.parse
from .base import Hypervisor,VM
class Proxmox(Hypervisor):
    def _ctx(self):
        c=ssl.create_default_context()
        if not self.cfg.get("verify_tls",True):c.check_hostname=False;c.verify_mode=ssl.CERT_NONE
        return c
    def _auth(self,method):
        sec=self.secrets; headers={}
        if sec.get("token_id") and sec.get("token_secret"):
            user=sec.get("username",self.cfg.get("username","root@pam"))
            headers["Authorization"]=f'PVEAPIToken={user}!{sec["token_id"]}={sec["token_secret"]}'; return headers
        login=urllib.parse.urlencode({"username":sec.get("username",self.cfg.get("username","")),"password":sec.get("password","")}).encode()
        host=self.cfg["host"];port=int(self.cfg.get("port",8006))
        req=urllib.request.Request(f"https://{host}:{port}/api2/json/access/ticket",data=login,method="POST")
        with urllib.request.urlopen(req,context=self._ctx(),timeout=15) as r:a=json.loads(r.read())["data"]
        headers["Cookie"]="PVEAuthCookie="+a["ticket"]
        if method!="GET":headers["CSRFPreventionToken"]=a["CSRFPreventionToken"]
        return headers
    def _request(self,path,method="GET",data=None):
        host=self.cfg["host"];port=int(self.cfg.get("port",8006));url=f"https://{host}:{port}/api2/json{path}"
        body=urllib.parse.urlencode(data).encode() if data else None
        req=urllib.request.Request(url,data=body,headers=self._auth(method),method=method)
        with urllib.request.urlopen(req,context=self._ctx(),timeout=30) as r:return json.loads(r.read()).get("data")
    def test(self):return {"ok":True,"version":self._request("/version")}
    def list_vms(self):
        out=[]
        for x in self._request("/cluster/resources?type=vm") or []:
            out.append(VM(str(x.get("vmid","")),x.get("name") or f'vm-{x.get("vmid")}',str(x.get("status","unknown")).upper(),x.get("maxcpu",0),x.get("maxmem",0),x.get("maxdisk",0),x.get("node",""),x))
        return out
