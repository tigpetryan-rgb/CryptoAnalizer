from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class Assignment:
    assignment_id: str
    target_chat: str
    requested_capabilities: tuple[str, ...]
    expected_state_revision: str
    dispatch_revision: str
    queue_status: str = "READY"


def validate_preclaim(assignment: Assignment, observed_state_revision: str, allowed: Iterable[str], mutually_exclusive: Iterable[Iterable[str]] = ()) -> tuple[bool, str]:
    requested = set(assignment.requested_capabilities)
    if assignment.queue_status != "READY":
        return False, "ALREADY_COMPLETED_OR_NOT_READY"
    if not requested:
        return False, "EMPTY_CAPABILITIES"
    if assignment.expected_state_revision != observed_state_revision:
        return False, "STALE_REVISION"
    if not requested.issubset(set(allowed)):
        return False, "UNAUTHORIZED_CAPABILITY"
    for pair in mutually_exclusive:
        if set(pair).issubset(requested):
            return False, "MUTUALLY_EXCLUSIVE_CAPABILITIES"
    return True, "OK"


def validate_output_envelope(
    *,
    expected_cycle_id: str,
    expected_assignment_id: str,
    expected_state_revision: str,
    expected_dispatch_revision: str,
    output_cycle_id: str,
    output_assignment_id: str,
    output_state_revision: str,
    output_dispatch_revision: str,
) -> tuple[bool, str]:
    """Require helpers to copy the authoritative execution envelope literally.

    Helpers never derive a next/previous revision. Any one-field mismatch is a
    fail-closed protocol conflict and the output cannot be completed or used
    downstream.
    """
    if output_cycle_id != expected_cycle_id:
        return False, "OUTPUT_CYCLE_MISMATCH"
    if output_assignment_id != expected_assignment_id:
        return False, "OUTPUT_ASSIGNMENT_MISMATCH"
    if output_state_revision != expected_state_revision:
        return False, "OUTPUT_STATE_REVISION_MISMATCH"
    if output_dispatch_revision != expected_dispatch_revision:
        return False, "OUTPUT_DISPATCH_REVISION_MISMATCH"
    return True, "OK"


def validate_refresh_inputs(*, assignment_is_refresh: bool, baseline_stale: bool, fresh_current_data_available: bool) -> tuple[bool, str]:
    """Validate input freshness without rejecting the stale baseline that a refresh is meant to replace."""
    if not fresh_current_data_available:
        return False, "FRESH_CURRENT_DATA_UNAVAILABLE"
    if baseline_stale and not assignment_is_refresh:
        return False, "STALE_INPUT"
    return True, "OK"


def validate_duplicate_replay(assignment: Assignment, receipt_exists: bool) -> tuple[bool, str]:
    if assignment.queue_status == "DONE" and receipt_exists:
        return False, "DUPLICATE_ALREADY_COMPLETED"
    return True, "OK"


def choose_recovery_action(queue_status: str, receipt_exists: bool, reports_exist: bool, lease_expired: bool, due_elapsed: bool = False) -> str:
    if queue_status == "DONE" and receipt_exists:
        return "CANCEL_RETRY_ALREADY_COMPLETED"
    if queue_status == "READY":
        if receipt_exists or reports_exist:
            return "RECONCILE_READY_SIDE_EFFECTS"
        if due_elapsed:
            return "RECOVER_SAME_ASSIGNMENT"
        return "WAIT_READY"
    if queue_status == "CLAIMED" and not lease_expired:
        return "RESUME_WAIT_FOR_ACTIVE_LEASE"
    if queue_status == "CLAIMED" and lease_expired and receipt_exists and reports_exist:
        return "RESUME_FINALIZE_DONE"
    if queue_status == "CLAIMED" and lease_expired and not receipt_exists:
        return "REQUEUE"
    return "ESCALATE_TO_DEADLETTER"


def validate_thesis_lineage(*, w03_thesis_id: Optional[str], thesis_status: Optional[str], w06_thesis_id: Optional[str] = None, w07_thesis_id: Optional[str] = None) -> tuple[bool, str]:
    if not w03_thesis_id:
        return False, "MISSING_THESIS_ID"
    if str(thesis_status or "").upper() in {"VOID", "INVALIDATED", "NO_SETUP"}:
        return False, "NON_ACTIONABLE_THESIS"
    if w06_thesis_id is not None and w06_thesis_id != w03_thesis_id:
        return False, "W06_THESIS_MISMATCH"
    if w07_thesis_id is not None and w07_thesis_id != w03_thesis_id:
        return False, "W07_THESIS_MISMATCH"
    return True, "OK"


def validate_scope(scope_matches: bool) -> tuple[bool, str]:
    return (True, "OK") if scope_matches else (False, "OUT_OF_SCOPE")


def no_work_hourly_wake(has_due_work: bool) -> dict:
    if has_due_work:
        return {"execute": True, "state_change": None, "notify": None}
    return {"execute": False, "state_change": False, "notify": False}


def final_trade_gate(*, w06_verdict: Optional[str], w07_verdict: Optional[str], risk_pct: float, max_risk_pct: float, rr: float, min_rr: float, fresh_data: bool) -> tuple[bool, str]:
    if w06_verdict not in {"APPROVE", "MODIFY"}:
        return False, "W06_GATE"
    if w07_verdict == "FAIL" or w07_verdict is None:
        return False, "W07_GATE"
    if risk_pct > max_risk_pct:
        return False, "RISK_CAP"
    if rr < min_rr:
        return False, "RR_GATE"
    if not fresh_data:
        return False, "STALE_DATA"
    return True, "PASS"


def automation_gate(manual_validation_complete: bool, explicit_user_approval: bool, physical_task_count: int) -> tuple[bool, str]:
    if not manual_validation_complete:
        return False, "MANUAL_VALIDATION_INCOMPLETE"
    if not explicit_user_approval:
        return False, "USER_APPROVAL_REQUIRED"
    if physical_task_count > 5:
        return False, "TASK_LIMIT_EXCEEDED"
    return True, "PASS"
