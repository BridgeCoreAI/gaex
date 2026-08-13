"""
GAEX public test suite. 16 tests, each mapped to a specific claim from
the approved Claims-to-Evidence Publication Map (private repo). Every
property gets both an allowed-path and an adversarial-path test where
that distinction is what substantiates the claim, per the state
non-mutation requirement approved during publication scope planning.
"""

import sys
import os
import dataclasses
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from src.case import Case, CaseState
from src.transition_map import build_engine
from src.observer import ExecutionEvidenceObserver
from src.evidence import verify_integrity, evaluate_completeness

TRIGGER = datetime(2026, 1, 1, tzinfo=timezone.utc)
DEADLINE = TRIGGER + timedelta(hours=48)


def make_rig():
    return Case(), build_engine(), ExecutionEvidenceObserver()


def advance_to_deadline_active(case, engine, observer):
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    observer.request_transition(engine, case, CaseState.VALIDATED)
    observer.request_transition(engine, case, CaseState.DEADLINE_ACTIVE)


# ---- Claim B: deny-by-default governance execution ----

def test_01_mapped_transition_succeeds():
    case, engine, observer = make_rig()
    result = observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    assert result.authorization_result == "AUTHORIZED"
    assert case.state == CaseState.INTAKE_RECEIVED


def test_02_unmapped_transition_denied_with_no_side_effects():
    case, engine, observer = make_rig()
    state_before = case.state
    result = observer.request_transition(engine, case, CaseState.CASE_CLOSED)  # skips everything
    assert result.authorization_result == "DENIED"
    assert result.reason == "NO_AUTHORIZING_CONTROL"
    assert case.state == state_before  # no mutation
    records = observer.ledger.records_for_case(case.case_id)
    assert all(r.event_type != "GOVERNANCE_TRANSITION" for r in records)  # no success evidence created
    assert any(r.event_type == "TRANSITION_DENIED" for r in records)  # denial itself is evidenced


# ---- Claim C: governed human authority ----

def test_03_authorized_reviewer_resolves_pending_review():
    case, engine, observer = make_rig()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    observer.request_transition(engine, case, CaseState.REVIEW_REQUIRED, context={"ambiguous": True})
    assert case.state == CaseState.REVIEW_REQUIRED

    result = observer.request_transition(
        engine, case, CaseState.VALIDATED,
        context={"reviewer_id": "reviewer-alpha", "authorized_reviewers": {"reviewer-alpha"}},
    )
    assert result.authorization_result == "AUTHORIZED"
    assert case.state == CaseState.VALIDATED


def test_04_unauthorized_reviewer_denied_with_no_side_effects():
    case, engine, observer = make_rig()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    observer.request_transition(engine, case, CaseState.REVIEW_REQUIRED, context={"ambiguous": True})
    state_before = case.state

    result = observer.request_transition(
        engine, case, CaseState.VALIDATED,
        context={"reviewer_id": "reviewer-untrusted", "authorized_reviewers": {"reviewer-alpha"}},
    )
    assert result.authorization_result == "DENIED"
    assert case.state == state_before  # review remains pending, no mutation
    records = observer.ledger.records_for_case(case.case_id)
    assert any(r.event_type == "TRANSITION_DENIED" for r in records)  # rejection is evidenced


# ---- Claim D: regulatory timing affects execution ----

def test_05_on_time_execution_permitted():
    case, engine, observer = make_rig()
    advance_to_deadline_active(case, engine, observer)
    result = observer.request_transition(engine, case, CaseState.EXECUTION_COMPLETE, context={"outcome": "PASS"})
    assert result.authorization_result == "AUTHORIZED"


def test_06_clock_past_deadline_changes_permitted_behavior():
    case, engine, observer = make_rig()
    advance_to_deadline_active(case, engine, observer)

    before_deadline = TRIGGER + timedelta(hours=10)
    before_result = observer.request_transition(
        engine, case, CaseState.DEADLINE_EXCEEDED, context={"current_time": before_deadline, "deadline": DEADLINE},
    )
    assert before_result.authorization_result == "DENIED"  # not breached yet

    after_deadline = TRIGGER + timedelta(hours=55)
    after_result = observer.request_transition(
        engine, case, CaseState.DEADLINE_EXCEEDED, context={"current_time": after_deadline, "deadline": DEADLINE},
    )
    assert after_result.authorization_result == "AUTHORIZED"
    assert case.state == CaseState.DEADLINE_EXCEEDED


def test_07_late_completion_preserves_the_earlier_breach_record():
    case, engine, observer = make_rig()
    advance_to_deadline_active(case, engine, observer)

    after_deadline = TRIGGER + timedelta(hours=55)
    observer.request_transition(
        engine, case, CaseState.DEADLINE_EXCEEDED, context={"current_time": after_deadline, "deadline": DEADLINE},
    )
    observer.request_transition(engine, case, CaseState.LATE_EXECUTION_COMPLETE, context={"outcome": "PASS-LATE"})

    records = observer.ledger.records_for_case(case.case_id)
    decisions = [r.decision for r in records]
    assert CaseState.DEADLINE_EXCEEDED in decisions  # breach still present
    assert CaseState.LATE_EXECUTION_COMPLETE in decisions  # late completion additionally present, neither erased


# ---- Claim E: governed failure/exception outcomes ----

def test_08_injected_failure_produces_explicit_outcome():
    case, engine, observer = make_rig()
    advance_to_deadline_active(case, engine, observer)
    result = observer.request_transition(engine, case, CaseState.FAILURE_LOGGED, context={"outcome": "FAIL"})
    assert result.authorization_result == "AUTHORIZED"
    assert case.state == CaseState.FAILURE_LOGGED


def test_09_disposition_resolves_failure_original_fact_preserved():
    case, engine, observer = make_rig()
    advance_to_deadline_active(case, engine, observer)
    observer.request_transition(engine, case, CaseState.FAILURE_LOGGED, context={"outcome": "FAIL"})
    result = observer.request_transition(engine, case, CaseState.EXECUTION_COMPLETE, context={"outcome": "RESOLVED"})
    assert result.authorization_result == "AUTHORIZED"

    records = observer.ledger.records_for_case(case.case_id)
    decisions = [r.decision for r in records]
    assert CaseState.FAILURE_LOGGED in decisions  # the original failure fact is still on record


# ---- Claim F: evidence generated from execution, never fabricated ----

def test_10_real_execution_produces_correlated_evidence():
    case, engine, observer = make_rig()
    result = observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    records = observer.ledger.records_for_case(case.case_id)
    assert len(records) == 1
    assert records[0].case_id == case.case_id  # correlated to the real case
    assert records[0].decision == result.resulting_state


def test_11_public_interface_cannot_fabricate_evidence_without_real_execution():
    case, engine, observer = make_rig()
    # The only public write path is request_transition(); there is no
    # method on the observer or ledger that accepts a caller-asserted
    # evidence record directly.
    public_methods = [m for m in dir(observer) if not m.startswith("_")]
    assert public_methods == ["ledger", "request_transition"]


# ---- Claim G: tamper-evident hash chaining ----

def test_12_untampered_ledger_verifies():
    case, engine, observer = make_rig()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    observer.request_transition(engine, case, CaseState.VALIDATED)
    result = verify_integrity(observer.ledger.all_records())
    assert result["result"] == "INTEGRITY_VERIFIED"


def test_13_tampering_is_detected():
    case, engine, observer = make_rig()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    real_records = observer.ledger.all_records()

    tampered = dataclasses.replace(real_records[0], decision="TAMPERED_VALUE")
    tampered_records = [tampered] + real_records[1:]

    result = verify_integrity(tampered_records)
    assert result["result"] == "INTEGRITY_FAILURE"
    assert result["reason"] == "RECORD_HASH_MISMATCH"
    # The real ledger itself is untouched.
    assert observer.ledger.all_records()[0].decision != "TAMPERED_VALUE"


# ---- Claim H: integrity and completeness independently evaluated ----

def test_14_complete_record_passes_both_checks():
    case, engine, observer = make_rig()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    observer.request_transition(engine, case, CaseState.VALIDATED)

    records = observer.ledger.records_for_case(case.case_id)
    integrity = verify_integrity(observer.ledger.all_records())
    completeness = evaluate_completeness(records, case.case_id, required_event_types=["GOVERNANCE_TRANSITION"])
    assert integrity["result"] == "INTEGRITY_VERIFIED"
    assert completeness["result"] == "COMPLETENESS_VERIFIED"


def test_15_incomplete_but_untampered_fails_completeness_only():
    case, engine, observer = make_rig()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    # Deliberately never advance further -- a required later event never happens.

    records = observer.ledger.records_for_case(case.case_id)
    integrity = verify_integrity(observer.ledger.all_records())
    completeness = evaluate_completeness(
        records, case.case_id, required_event_types=["GOVERNANCE_TRANSITION", "TRANSPARENCY_RESULT"]
    )
    assert integrity["result"] == "INTEGRITY_VERIFIED"  # what exists is structurally sound
    assert completeness["result"] == "COMPLETENESS_FAILED"
    assert "TRANSPARENCY_RESULT" in completeness["missing"]


# ---- Claim I: end-to-end traceability within the scoped demonstration path ----

def test_16_full_path_reconstructable_from_evidence_alone():
    case, engine, observer = make_rig()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    observer.request_transition(engine, case, CaseState.VALIDATED)
    observer.request_transition(engine, case, CaseState.DEADLINE_ACTIVE)
    observer.request_transition(engine, case, CaseState.EXECUTION_COMPLETE, context={"outcome": "PASS"})
    observer.request_transition(engine, case, CaseState.TRANSPARENCY_CHECK)
    observer.request_transition(
        engine, case, CaseState.CASE_CLOSED,
        context={
            "provenance": {"present": True, "valid": True},
            "disclosure": {"present": True, "adequate": True},
        },
    )

    records = observer.ledger.records_for_case(case.case_id)
    integrity = verify_integrity(observer.ledger.all_records())
    assert integrity["result"] == "INTEGRITY_VERIFIED"
    assert case.state == CaseState.CASE_CLOSED

    # The full path is reconstructable purely from the evidence records,
    # in order, without needing to inspect the live case object at all.
    reconstructed_states = [r.decision for r in records if r.event_type == "GOVERNANCE_TRANSITION"]
    assert reconstructed_states == [
        CaseState.INTAKE_RECEIVED, CaseState.VALIDATED, CaseState.DEADLINE_ACTIVE,
        CaseState.EXECUTION_COMPLETE, CaseState.TRANSPARENCY_CHECK, CaseState.CASE_CLOSED,
    ]
