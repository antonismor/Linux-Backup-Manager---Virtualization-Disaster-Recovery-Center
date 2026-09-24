import unittest
from lbm_vdrc.core import safe_name


class CoreTests(unittest.TestCase):
    def test_safe_name(self):
        self.assertEqual(safe_name("Nightly ERP Backup"), "Nightly-ERP-Backup")
        self.assertEqual(safe_name("../unsafe///name"), "..-unsafe-name")
        self.assertLessEqual(len(safe_name("a" * 100)), 64)


if __name__ == "__main__":
    unittest.main()
