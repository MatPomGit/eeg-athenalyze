"""Contract checks only: simulated outputs are NOT native decoder evidence."""
import copy
import unittest

from eeg_athenalyze.athena_native_parity import fixture_manifest, validate_native_result


class NativeParityContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest = fixture_manifest()
        self.output = {
            "schema_version": 1,
            "decoder": "BlueMuse",
            "source_commit": "a" * 40,
            "vectors": [
                {"id": f["id"], "payload_sha256": f["payload_sha256"],
                 "codes": f["expected_codes"], "uv": f["expected_uv"]}
                for f in self.manifest["vectors"]
            ],
        }

    def test_fixture_determinism_and_layout(self):
        self.assertEqual(self.manifest, fixture_manifest())
        self.assertEqual(len(self.manifest["vectors"]), 6)
        self.assertEqual({len(bytes.fromhex(v["payload_hex"])) for v in
                          self.manifest["vectors"]}, {28})
        self.assertEqual({v["tag"] for v in self.manifest["vectors"]}, {17, 18})

    def test_simulated_matching_contract_does_not_certify_hardware(self):
        result = validate_native_result(self.manifest, self.output)
        self.assertTrue(result["passed"])
        self.assertFalse(result["hardware_validated"])

    def test_wrong_code_and_digest_fail(self):
        for field, value in (("codes", [[0]]), ("payload_sha256", "0" * 64)):
            with self.subTest(field=field):
                out = copy.deepcopy(self.output)
                out["vectors"][0][field] = value
                self.assertFalse(validate_native_result(self.manifest, out)["passed"])

    def test_missing_duplicate_unknown_and_unpinned_fail(self):
        missing = copy.deepcopy(self.output)
        missing["vectors"].pop()
        self.assertFalse(validate_native_result(self.manifest, missing)["passed"])
        duplicate = copy.deepcopy(self.output)
        duplicate["vectors"].append(duplicate["vectors"][0])
        with self.assertRaises(ValueError):
            validate_native_result(self.manifest, duplicate)
        unknown = copy.deepcopy(self.output)
        unknown["vectors"][0]["id"] = "unregistered"
        with self.assertRaises(ValueError):
            validate_native_result(self.manifest, unknown)
        unpinned = copy.deepcopy(self.output)
        unpinned["source_commit"] = "main"
        with self.assertRaises(ValueError):
            validate_native_result(self.manifest, unpinned)

    def test_nan_and_wrong_shape_fail(self):
        for value in (float("nan"), float("inf"), 100):
            with self.subTest(value=str(value)):
                out = copy.deepcopy(self.output)
                out["vectors"][0]["uv"][0][0] = value
                self.assertFalse(validate_native_result(self.manifest, out)["passed"])
        out = copy.deepcopy(self.output)
        out["vectors"][0]["uv"] = []
        self.assertFalse(validate_native_result(self.manifest, out)["passed"])


if __name__ == "__main__":
    unittest.main()
