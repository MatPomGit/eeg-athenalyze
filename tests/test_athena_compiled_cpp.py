"""Compile and execute the isolated native C++ 14-bit test oracle.

This exercises actual machine code compiled from an adapted excerpt; NOT the
BrainFlow library, BlueMuse DLL, physical headset or firmware.
"""
import math
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.athena_packet_reference import (
    codes_to_uv, decode_eeg_tag_payload,
)

_SOURCE = Path(__file__).parent / "native" / "athena_cpp_oracle.cpp"
_RAILS = "004000f0ff018001a0ffffffab00004000f0ff018001a0ffffffab00"
_CHANNELS = "640032c0124006654032d0124406668032e012480667c032f0124c06"
_REVERSED = "90014b800c900191414b900c940192814ba00c980193c14bb00c9c01"
_ALTERNATING = "00c0ff0f00fcff00c0ff0f00fcff00c0ff0f00fcff00c0ff0f00fcff"


class CompiledCppOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = next((shutil.which(name) for name in ("g++", "clang++")
                             if shutil.which(name)), None)
        if cls.compiler is None:
            raise unittest.SkipTest("No C++ compiler; native adapted-oracle test skipped")
        cls.temp = tempfile.TemporaryDirectory(prefix="athena-cpp-")
        cls.bin_path = Path(cls.temp.name) / (
            "athena_oracle.exe" if __import__("os").name == "nt" else "athena_oracle")
        proc = subprocess.run(
            [cls.compiler, "-std=c++17", "-O2", "-Wall", "-Wextra",
             str(_SOURCE), "-o", str(cls.bin_path)],
            capture_output=True, text=True, timeout=45, check=False)
        if proc.returncode:
            cls.temp.cleanup()
            raise AssertionError("Failed to compile C++ fixture oracle: " + proc.stderr)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def test_raw_codes_and_microvolts_match(self):
        for hex_data in (_RAILS, _CHANNELS, _REVERSED, _ALTERNATING):
            payload = bytes.fromhex(hex_data)
            for tag in (0x11, 0x12):
                with self.subTest(hex=hex_data[:10], tag=tag):
                    proc = subprocess.run([str(self.bin_path), f"{tag:02x}", hex_data],
                                          capture_output=True, text=True,
                                          timeout=10, check=True)
                    lines = proc.stdout.strip().splitlines()
                    expected = decode_eeg_tag_payload(tag, payload)
                    self.assertEqual(len(lines), len(expected))
                    for line, codes in zip(lines, expected):
                        actual = [v.split(":") for v in line.split()]
                        self.assertEqual(tuple(int(v[0]) for v in actual), codes)
                        self.assertEqual(len(actual), len(codes))
                        for (_, uv), reference in zip(actual, codes_to_uv(codes)):
                            self.assertTrue(math.isfinite(float(uv)))
                            self.assertAlmostEqual(float(uv), reference, places=10)

    def test_malformed_hex_and_unknown_tags_fail(self):
        for tag, hex_data in (("77", _RAILS), ("11", "ff"), ("12", "xx" * 28)):
            with self.subTest(tag=tag, hex=hex_data[:4]):
                proc = subprocess.run([str(self.bin_path), tag, hex_data],
                                      capture_output=True, text=True,
                                      timeout=10, check=False)
                self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
