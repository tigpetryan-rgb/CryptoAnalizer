import unittest

from protocol.validator import Assignment, choose_recovery_action, no_work_hourly_wake, validate_duplicate_replay, validate_preclaim, validate_scope


class StepJKTests(unittest.TestCase):
    def test_stale_revision_rejected(self):
        a = Assignment("A08", "H01_MARKET_CONTEXT", ("W01",), "S000020", "D000008")
        ok, reason = validate_preclaim(a, "S000021", {"W01", "W02", "W05"})
        self.assertFalse(ok)
        self.assertEqual(reason, "STALE_REVISION")

    def test_duplicate_completed_replay_rejected(self):
        a = Assignment("A09", "H01_MARKET_CONTEXT", ("W01",), "S000023", "D000009", queue_status="DONE")
        ok, reason = validate_duplicate_replay(a, receipt_exists=True)
        self.assertFalse(ok)
        self.assertEqual(reason, "DUPLICATE_ALREADY_COMPLETED")

    def test_done_assignment_not_claimable(self):
        a = Assignment("A09", "H01_MARKET_CONTEXT", ("W01",), "S000023", "D000009", queue_status="DONE")
        ok, reason = validate_preclaim(a, "S000023", {"W01", "W02", "W05"})
        self.assertFalse(ok)
        self.assertEqual(reason, "ALREADY_COMPLETED_OR_NOT_READY")

    def test_out_of_scope_rejected(self):
        ok, reason = validate_scope(False)
        self.assertFalse(ok)
        self.assertEqual(reason, "OUT_OF_SCOPE")

    def test_stale_claim_without_receipt_requeues(self):
        self.assertEqual(choose_recovery_action("CLAIMED", False, False, True), "REQUEUE")

    def test_stale_claim_with_outputs_finalizes(self):
        self.assertEqual(choose_recovery_action("CLAIMED", True, True, True), "RESUME_FINALIZE_DONE")

    def test_active_lease_not_retried(self):
        self.assertEqual(choose_recovery_action("CLAIMED", False, False, False), "RESUME_WAIT_FOR_ACTIVE_LEASE")

    def test_no_work_hourly_wake_is_silent_noop(self):
        self.assertEqual(no_work_hourly_wake(False), {"execute": False, "state_change": False, "notify": False})


if __name__ == "__main__":
    unittest.main()
