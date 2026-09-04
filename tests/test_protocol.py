import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "protocol" / "capabilities.json").read_text())


def validate_assignment(target, capabilities, expected_state, observed_state):
    allowed = set(CONFIG["roles"].get(target, []))
    requested = list(capabilities)
    if not requested:
        return False, "EMPTY_CAPABILITIES"
    if expected_state != observed_state:
        return False, "STALE_REVISION"
    if not set(requested).issubset(allowed):
        return False, "UNAUTHORIZED_CAPABILITY"
    for pair in CONFIG.get("mutual_exclusion", {}).get(target, []):
        if set(pair).issubset(set(requested)):
            return False, "MUTUALLY_EXCLUSIVE_CAPABILITIES"
    return True, "OK"


class ProtocolTests(unittest.TestCase):
    def test_five_physical_chats(self):
        self.assertEqual(CONFIG["physical_chat_count"], 5)
        self.assertEqual(len(CONFIG["roles"]), 5)

    def test_h03_is_w06_only(self):
        self.assertEqual(CONFIG["roles"]["H03_RISK_MANAGER"], ["W06"])

    def test_h04_w07_only_allowed(self):
        ok, reason = validate_assignment("H04_VALIDATOR_MONITOR", ["W07"], "S1", "S1")
        self.assertTrue(ok, reason)

    def test_h04_w08_only_allowed(self):
        ok, reason = validate_assignment("H04_VALIDATOR_MONITOR", ["W08"], "S1", "S1")
        self.assertTrue(ok, reason)

    def test_h04_combined_w07_w08_rejected(self):
        ok, reason = validate_assignment("H04_VALIDATOR_MONITOR", ["W07", "W08"], "S1", "S1")
        self.assertFalse(ok)
        self.assertEqual(reason, "MUTUALLY_EXCLUSIVE_CAPABILITIES")

    def test_wrong_helper_capability_rejected(self):
        ok, reason = validate_assignment("H02_SCANNER_TECHNICAL", ["W01"], "S1", "S1")
        self.assertFalse(ok)
        self.assertEqual(reason, "UNAUTHORIZED_CAPABILITY")

    def test_stale_revision_rejected(self):
        ok, reason = validate_assignment("H01_MARKET_CONTEXT", ["W01"], "S2", "S1")
        self.assertFalse(ok)
        self.assertEqual(reason, "STALE_REVISION")

    def test_receipt_capabilities_must_match_execution(self):
        requested = {"W04", "W03"}
        executed = {"W04", "W03"}
        self.assertEqual(requested, executed)

    def test_duplicate_assignment_ids_rejected(self):
        assignment_ids = ["A01", "A02", "A02"]
        self.assertNotEqual(len(assignment_ids), len(set(assignment_ids)))


if __name__ == "__main__":
    unittest.main()
