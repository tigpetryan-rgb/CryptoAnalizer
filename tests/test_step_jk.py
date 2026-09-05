import unittest

from protocol.validator import (
    Assignment,
    choose_recovery_action,
    no_work_hourly_wake,
    validate_duplicate_replay,
    validate_preclaim,
    validate_refresh_inputs,
    validate_scope,
    validate_thesis_lineage,
)


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

    def test_ready_before_due_waits(self):
        self.assertEqual(choose_recovery_action("READY", False, False, False, due_elapsed=False), "WAIT_READY")

    def test_overdue_ready_side_effect_free_recovers_same_assignment(self):
        self.assertEqual(choose_recovery_action("READY", False, False, False, due_elapsed=True), "RECOVER_SAME_ASSIGNMENT")

    def test_ready_with_side_effects_reconciles_instead_of_rerun(self):
        self.assertEqual(choose_recovery_action("READY", True, True, False, due_elapsed=True), "RECONCILE_READY_SIDE_EFFECTS")

    def test_refresh_assignment_accepts_intentionally_stale_baseline(self):
        ok, reason = validate_refresh_inputs(
            assignment_is_refresh=True,
            baseline_stale=True,
            fresh_current_data_available=True,
        )
        self.assertTrue(ok, reason)

    def test_non_refresh_rejects_stale_input(self):
        ok, reason = validate_refresh_inputs(
            assignment_is_refresh=False,
            baseline_stale=True,
            fresh_current_data_available=True,
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "STALE_INPUT")

    def test_refresh_requires_fresh_current_data(self):
        ok, reason = validate_refresh_inputs(
            assignment_is_refresh=True,
            baseline_stale=True,
            fresh_current_data_available=False,
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "FRESH_CURRENT_DATA_UNAVAILABLE")

    def test_thesis_lineage_matches_across_w03_w06_w07(self):
        ok, reason = validate_thesis_lineage(
            w03_thesis_id="T-NEAR-LONG-G2",
            thesis_status="ACTIVE",
            w06_thesis_id="T-NEAR-LONG-G2",
            w07_thesis_id="T-NEAR-LONG-G2",
        )
        self.assertTrue(ok, reason)

    def test_void_thesis_cannot_pass_lineage(self):
        ok, reason = validate_thesis_lineage(w03_thesis_id="T-NEAR-LONG-G1", thesis_status="VOID")
        self.assertFalse(ok)
        self.assertEqual(reason, "NON_ACTIONABLE_THESIS")

    def test_w06_thesis_mismatch_rejected(self):
        ok, reason = validate_thesis_lineage(
            w03_thesis_id="T-NEAR-LONG-G2",
            thesis_status="ACTIVE",
            w06_thesis_id="T-NEAR-LONG-G1",
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "W06_THESIS_MISMATCH")

    def test_no_work_hourly_wake_is_silent_noop(self):
        self.assertEqual(no_work_hourly_wake(False), {"execute": False, "state_change": False, "notify": False})


if __name__ == "__main__":
    unittest.main()
