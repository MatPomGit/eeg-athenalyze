"""Simulated reports exercise the pair validator, never native code."""
import copy
import unittest

from eeg_athenalyze.athena_native_parity import fixture_manifest
from eeg_athenalyze.athena_native_pair import compare_paired_reports


def example_report(manifest, decoder):
    return {
        "schema_version": 1, "decoder": decoder, "source_commit": "a" * 40,
        "vectors": [
            {"id": v["id"], "payload_sha256": v["payload_sha256"],
             "codes": v["expected_codes"], "uv": v["expected_uv"]}
            for v in manifest["vectors"]
        ],
    }


class PairedNativeReportContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest = fixture_manifest()
        self.blue = example_report(self.manifest, "BlueMuse")
        self.brain = example_report(self.manifest, "BrainFlow")

    def test_pair_contract_is_not_hardware_or_binary_attestation(self):
        result = compare_paired_reports(self.manifest, self.blue, self.brain)
        self.assertTrue(result["passed"])
        self.assertFalse(result["native_execution_attested"])
        self.assertFalse(result["hardware_validated"])

    def test_one_vendor_repeated_cannot_pass(self):
        with self.assertRaises(ValueError):
            compare_paired_reports(self.manifest, self.blue, self.blue)

    def test_missing_native_vector_fails(self):
        out = copy.deepcopy(self.brain)
        out["vectors"].pop()
        self.assertFalse(compare_paired_reports(self.manifest, self.blue, out)["passed"])

    def test_mutated_codes_and_uv_fail(self):
        out = copy.deepcopy(self.brain)
        out["vectors"][0]["codes"][0][0] = 7
        self.assertFalse(compare_paired_reports(self.manifest, self.blue, out)["passed"])
        out = copy.deepcopy(self.brain)
        out["vectors"][0]["uv"][0][0] += 0.01
        self.assertFalse(compare_paired_reports(self.manifest, self.blue, out)["passed"])

    def test_tolerance_invalid_fails_closed(self):
        for value in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=str(value)), self.assertRaises(ValueError):
                compare_paired_reports(
                    self.manifest, self.blue, self.brain, tolerance_uv=value)


if __name__ == "__main__":
    unittest.main()
