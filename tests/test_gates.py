import unittest

from protocol.validator import automation_gate, final_trade_gate


class GateTests(unittest.TestCase):
    def test_validator_fail_blocks_decision(self):
        ok, reason = final_trade_gate(w06_verdict="MODIFY", w07_verdict="FAIL", risk_pct=0.5, max_risk_pct=0.5, rr=2.5, min_rr=2.0, fresh_data=True)
        self.assertFalse(ok)
        self.assertEqual(reason, "W07_GATE")

    def test_risk_cap_blocks_decision(self):
        ok, reason = final_trade_gate(w06_verdict="MODIFY", w07_verdict="PASS", risk_pct=1.0, max_risk_pct=0.5, rr=2.5, min_rr=2.0, fresh_data=True)
        self.assertFalse(ok)
        self.assertEqual(reason, "RISK_CAP")

    def test_automation_needs_completed_validation(self):
        ok, reason = automation_gate(False, True, 5)
        self.assertFalse(ok)
        self.assertEqual(reason, "MANUAL_VALIDATION_INCOMPLETE")

    def test_automation_needs_explicit_approval(self):
        ok, reason = automation_gate(True, False, 5)
        self.assertFalse(ok)
        self.assertEqual(reason, "USER_APPROVAL_REQUIRED")

    def test_automation_is_limited_to_five_tasks(self):
        ok, reason = automation_gate(True, True, 6)
        self.assertFalse(ok)
        self.assertEqual(reason, "TASK_LIMIT_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
