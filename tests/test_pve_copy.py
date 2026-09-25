import unittest

from lbm_vdrc.migrations.proxmox_copy import (
    _bridges_from_config,
    _hardware_warnings,
    _parse_storages,
    _parse_vms,
    _validate_endpoint,
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

    def test_endpoint_validation_rejects_option_injection(self):
        _validate_endpoint("10.11.103.10", "root")
        _validate_endpoint("pve02.example.local", "backup-admin")
        with self.assertRaises(ValueError):
            _validate_endpoint("-oProxyCommand=evil", "root")
        with self.assertRaises(ValueError):
            _validate_endpoint("pve01", "-root")

    def test_hardware_warnings(self):
        cfg = """\
bios: ovmf
efidisk0: local-lvm:vm-120-disk-0,efitype=4m
tpmstate0: local-lvm:vm-120-disk-1,version=v2.0
hostpci0: 0000:01:00
"""
        warnings = _hardware_warnings(cfg)
        self.assertTrue(any("PCI/GPU" in x for x in warnings))
        self.assertTrue(any("vTPM" in x for x in warnings))
        self.assertTrue(any("EFI" in x for x in warnings))

    def test_bridge_extraction(self):
        cfg = """\
net0: virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,firewall=1
net1: virtio=11:22:33:44:55:66,bridge=vmbr103,tag=103
"""
        self.assertEqual(_bridges_from_config(cfg), ["vmbr0", "vmbr103"])


if __name__ == "__main__":
    unittest.main()
