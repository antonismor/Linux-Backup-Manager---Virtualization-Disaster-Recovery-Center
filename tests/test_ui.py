import contextlib
import io
import os
import unittest
from unittest.mock import patch

from lbm_vdrc.ui import Screen, ANSI_RE, pad, vlen


class UITests(unittest.TestCase):
    def test_ansi_does_not_change_visible_width(self):
        colored = "\033[38;5;46m● ONLINE\033[0m"
        self.assertEqual(vlen(colored), len("● ONLINE"))
        self.assertEqual(vlen(pad(colored, 20)), 20)

    def test_all_frame_lines_have_identical_width(self):
        output = io.StringIO()
        with patch("lbm_vdrc.ui.shutil.get_terminal_size", return_value=os.terminal_size((120, 40))):
            with contextlib.redirect_stdout(output):
                s = Screen()
                s.header("Backup • Restore • Convert • Migrate • Disaster Recovery")
                s.section("CONNECTED HYPERVISORS")
                s.section_row("  1   PVE01   Proxmox VE 9.x   10.10.10.10   12   ● ONLINE")
                s.section_row("  2   ESXI01  VMware ESXi 8    10.10.10.20    8   ● ONLINE")
                s.section_end()
                s.footer()
        lines = [ANSI_RE.sub("", line) for line in output.getvalue().splitlines()]
        self.assertTrue(lines)
        self.assertEqual({len(line) for line in lines}, {120})

    def test_small_terminal_never_renders_wider_than_terminal(self):
        with patch("lbm_vdrc.ui.shutil.get_terminal_size", return_value=os.terminal_size((78, 24))):
            self.assertEqual(Screen().width, 78)


if __name__ == "__main__":
    unittest.main()
