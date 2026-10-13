import unittest
from pathlib import Path
import ast


class GattDiagnosticTests(unittest.TestCase):
    def test_diagnostic_script_is_syntactically_valid(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "diagnose_muse_gatt.py"
        ast.parse(script.read_text(encoding="utf-8"))

    def test_driver_timeout_configuration(self):
        from eeg_athenalyze.muse_athena import AthenaSettings
        self.assertEqual(AthenaSettings().discovery_timeout_seconds, 15)
        with self.assertRaises(ValueError):
            AthenaSettings(discovery_timeout_seconds=0)
