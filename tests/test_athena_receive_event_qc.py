"""Deterministic offline classification; synthetic packets only."""
import json
import tempfile
import unittest
from pathlib import Path
from eeg_athenalyze.athena_receive_event_qc import summarize_receive_events
from eeg_athenalyze.ble_notification_qc import SENSOR_SUFFIXES

def packet(index):
    return bytes([42])+index.to_bytes(2,"little")+bytes(6)+bytes([0x11,0])+bytes(3)+bytes(28)

def row(uuid, t, payload):
    return {"characteristic":uuid,"receive_monotonic_seconds":t,"payload_hex":payload.hex()}

class ReceiveEventTests(unittest.TestCase):
    def analyze(self, records, threshold=.2):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"raw.jsonl"
            path.write_text("".join(json.dumps(r)+"\n" for r in records))
            return summarize_receive_events(path,gap_threshold_seconds=threshold)

    def test_host_gap_coincides_with_index_jump(self):
        uuid=SENSOR_SUFFIXES[0]
        report=self.analyze([row(uuid,1.0,packet(10)),row(uuid,1.01,packet(11)),
                             row(uuid,1.9,packet(14))])
        e=report["event_counts"]
        self.assertEqual(e["successive_index"],1)
        self.assertEqual(e["index_jump_candidate"],1)
        self.assertEqual(e["host_receive_gap"],1)
        self.assertEqual(e["host_gap_with_index_jump"],1)
        self.assertIsNone(report["packet_loss_estimate"])

    def test_multiprimary_callback_no_false_host_gap(self):
        uuid=SENSOR_SUFFIXES[0]
        report=self.analyze([row(uuid,1.0,packet(20)+packet(21)),
                             row(uuid,1.01,packet(21))])
        e=report["event_counts"]
        self.assertEqual(e["successive_index"],1)
        self.assertEqual(e["repeated_index"],1)
        self.assertNotIn("host_receive_gap",e)

    def test_no_cross_characteristic_transitions(self):
        a,b=SENSOR_SUFFIXES
        report=self.analyze([row(a,1.0,packet(100)),row(b,1.4,packet(1000)),
                             row(a,1.41,packet(101)),row(b,1.42,packet(1001))])
        self.assertEqual(report["event_counts"]["successive_index"],2)
        self.assertEqual(report["event_counts"]["host_receive_gap"],2)
        self.assertNotIn("index_jump_candidate",report["event_counts"])

    def test_invalid_notification_is_diagnostic_not_loss(self):
        uuid=SENSOR_SUFFIXES[0]
        report=self.analyze([row(uuid,1.0,b"\x01"),row(uuid,1.1,packet(4))])
        self.assertEqual(report["event_counts"]["malformed_notification"],1)
        self.assertNotIn("index_jump_candidate",report["event_counts"])

    def test_malformed_monotonic_and_threshold_rejected(self):
        uuid=SENSOR_SUFFIXES[0]
        with self.assertRaisesRegex(ValueError,"Nonmonotonic"):
            self.analyze([row(uuid,2.0,packet(1)),row(uuid,1.0,packet(2))])
        with self.assertRaises(ValueError):
            self.analyze([row(uuid,1.0,packet(1))],threshold=float("nan"))

if __name__ == "__main__":
    unittest.main()
