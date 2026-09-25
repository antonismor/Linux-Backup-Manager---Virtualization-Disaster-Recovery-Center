import unittest

from lbm_vdrc.migrations.proxmox_copy import (
    _bridges_from_config,
    _parse_storages,
    _parse_vms,
)


class ProxmoxCopyTests(unittest.TestCase):
    def test_parse_vms_filters_lxc_and_templates(self):
        rows = [
            {"type": "qemu", "vmid": 120, "name": "ERP01", "status": "stopped", "maxcpu": 8, "maxmem": 17179869184, "maxdisk": 107374182400},
            {"type": "lxc", "vmid": 121, "name": "CT01", "status": "stopped"},
            {"type": "qemu", "vmid": 9000, "name": "TEMPLATE", "status": "stopped", "template": 1},
        ]
        vms = _parse_vms(rows)
        self.assertEqual(len(vms), 1)
        self.assertEqual(vms[0]["vmid"], 120)
        self.assertEqual(vms[0]["name"], "ERP01")
        self.assertEqual(vms[0]["status"], "stopped")

    def test_parse_storages_keeps_active_image_storage(self):
        cfg = [
            {"storage": "local-lvm", "type": "lvmthin", "content": "images,rootdir"},
            {"storage": "backup", "type": "dir", "content": "backup,iso"},
            {"storage": "offline", "type": "dir", "content": "images"},
        ]
        status = [
            {"storage": "local-lvm", "active": 1, "total": 1000, "used": 100, "avail": 900},
            {"storage": "backup", "active": 1, "total": 1000, "used": 200, "avail": 800},
            {"storage": "offline", "active": 0, "total": 1000, "used": 0, "avail": 1000},
        ]
        rows = _parse_storages(cfg, status)
        self.assertEqual([x["storage"] for x in rows], ["local-lvm"])
        self.assertEqual(rows[0]["avail"], 900)

    def test_bridge_extraction(self):
        cfg = """\
net0: virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,firewall=1
net1: virtio=11:22:33:44:55:66,bridge=vmbr103,tag=103
"""
        self.assertEqual(_bridges_from_config(cfg), ["vmbr0", "vmbr103"])


if __name__ == "__main__":
    unittest.main()
