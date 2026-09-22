"""Dependency-free release checks; complements Omarchy's own validator."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseChecks(unittest.TestCase):
    def test_service_replaces_stock_idle(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        self.assertEqual(manifest['omarchy']['clonedFrom'], 'omarchy.idle')
        self.assertEqual(manifest['kinds'], ['service'])
        self.assertTrue((ROOT / manifest['entryPoints']['service']).is_file())

    def test_no_machine_specific_paths(self):
        for name in ['Service.qml', 'IdleModel.js', 'gamepad_activity.py']:
            source = (ROOT / name).read_text()
            self.assertNotIn('/home/brussell', source)
            self.assertNotIn('brussell.idle', source)

    def test_preserves_upstream_license(self):
        self.assertIn('Copyright (c) David Heinemeier Hansson', (ROOT / 'LICENSE').read_text())


if __name__ == '__main__':
    unittest.main()
