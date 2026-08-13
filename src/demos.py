"""
GAEX demonstrations, 8 paths, matching the approved specification.
Run: python -m src.demos
"""

import sys
import os
import dataclasses
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.case import Case, CaseState
from src.transition_map import build_engine
from src.observer import ExecutionEvidenceObserver
from src.evidence import verify_integrity, evaluate_completeness

TRIGGER = datetime(2026, 1, 1, tzinfo=timezone.utc)
DEADLINE = TRIGGER + timedelta(hours=48)


def demo_01_happy_path():
    print("=== DEMO 1: Happy Path ===")
    case, engine, observer = Case(), build_engine(), ExecutionEvidenceObserver()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    observer.request_transition(engine, case, CaseState.VALIDATED)
    observer.request_transition(engine, case, CaseState.DEADLINE_ACTIVE)
    observer.request_transition(engine, case, CaseState.EXECUTION_COMPLETE, context={"outcome": "PASS"})
    observer.request_transition(engine, case, CaseState.TRANSPARENCY_CHECK)
    result = observer.request_transition(
        engine, case, CaseState.CASE_CLOSED,
        context={"provenance": {"present": True, "valid": True}, "disclosure": {"present": True, "adequate": True}},
    )
    print(f"  Final state: {case.state}, closure: {result.authorization_result}")
    return case.state == CaseState.CASE_CLOSED


def demo_02_deny_by_default_denial():
    print("=== DEMO 2: Deny-by-Default Denial ===")
    case, engine, observer = Case(), build_engine(), ExecutionEvidenceObserver()
    result = observer.request_transition(engine, case, CaseState.CASE_CLOSED)  # skips everything
    print(f"  Result: {result.authorization_result}, reason: {result.reason}")
    return result.authorization_result == "DENIED"


def demo_03_human_authority_detour():
    print("=== DEMO 3: Human-Authority Detour ===")
    case, engine, observer = Case(), build_engine(), ExecutionEvidenceObserver()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    observer.request_transition(engine, case, CaseState.REVIEW_REQUIRED, context={"ambiguous": True})
    denied = observer.request_transition(
        engine, case, CaseState.VALIDATED,
        context={"reviewer_id": "reviewer-untrusted", "authorized_reviewers": {"reviewer-alpha"}},
    )
    print(f"  Unauthorized attempt: {denied.authorization_result}")
    authorized = observer.request_transition(
        engine, case, CaseState.VALIDATED,
        context={"reviewer_id": "reviewer-alpha", "authorized_reviewers": {"reviewer-alpha"}},
    )
    print(f"  Authorized attempt: {authorized.authorization_result}")
    return denied.authorization_result == "DENIED" and authorized.authorization_result == "AUTHORIZED"


def demo_04_deadline_path():
    print("=== DEMO 4: Deadline Path (on-time vs breach) ===")
    case_a, engine_a, observer_a = Case(), build_engine(), ExecutionEvidenceObserver()
    observer_a.request_transition(engine_a, case_a, CaseState.INTAKE_RECEIVED)
    observer_a.request_transition(engine_a, case_a, CaseState.VALIDATED)
    observer_a.request_transition(engine_a, case_a, CaseState.DEADLINE_ACTIVE)
    on_time = observer_a.request_transition(engine_a, case_a, CaseState.EXECUTION_COMPLETE, context={"outcome": "PASS"})
    print(f"  On-time path: {on_time.authorization_result}, state: {case_a.state}")

    case_b, engine_b, observer_b = Case(), build_engine(), ExecutionEvidenceObserver()
    observer_b.request_transition(engine_b, case_b, CaseState.INTAKE_RECEIVED)
    observer_b.request_transition(engine_b, case_b, CaseState.VALIDATED)
    observer_b.request_transition(engine_b, case_b, CaseState.DEADLINE_ACTIVE)
    breach = observer_b.request_transition(
        engine_b, case_b, CaseState.DEADLINE_EXCEEDED,
        context={"current_time": TRIGGER + timedelta(hours=55), "deadline": DEADLINE},
    )
    print(f"  Breach path: {breach.authorization_result}, state: {case_b.state}")
    return case_a.state == CaseState.EXECUTION_COMPLETE and case_b.state == CaseState.DEADLINE_EXCEEDED


def demo_05_failure_disposition_path():
    print("=== DEMO 5: Failure/Disposition Path ===")
    case, engine, observer = Case(), build_engine(), ExecutionEvidenceObserver()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    observer.request_transition(engine, case, CaseState.VALIDATED)
    observer.request_transition(engine, case, CaseState.DEADLINE_ACTIVE)
    observer.request_transition(engine, case, CaseState.FAILURE_LOGGED, context={"outcome": "FAIL"})
    print(f"  After failure: {case.state}")
    resolved = observer.request_transition(engine, case, CaseState.EXECUTION_COMPLETE, context={"outcome": "RESOLVED"})
    print(f"  After disposition: {case.state}, result: {resolved.authorization_result}")
    return case.state == CaseState.EXECUTION_COMPLETE


def demo_06_execution_to_evidence():
    print("=== DEMO 6: Execution-to-Evidence ===")
    case, engine, observer = Case(), build_engine(), ExecutionEvidenceObserver()
    result = observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    records = observer.ledger.records_for_case(case.case_id)
    print(f"  Real transition result: {result.resulting_state}")
    print(f"  Evidence record decision: {records[0].decision}, case_id matches: {records[0].case_id == case.case_id}")
    return records[0].decision == result.resulting_state


def demo_07_hash_tamper_evidence():
    print("=== DEMO 7: Hash Tamper-Evidence ===")
    case, engine, observer = Case(), build_engine(), ExecutionEvidenceObserver()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    real_records = observer.ledger.all_records()
    real_result = verify_integrity(real_records)
    print(f"  Untampered: {real_result['result']}")

    tampered_first = dataclasses.replace(real_records[0], decision="TAMPERED")
    tampered_records = [tampered_first] + real_records[1:]
    tampered_result = verify_integrity(tampered_records)
    print(f"  Tampered copy: {tampered_result['result']}, reason: {tampered_result['reason']}")
    return real_result["result"] == "INTEGRITY_VERIFIED" and tampered_result["result"] == "INTEGRITY_FAILURE"


def demo_08_integrity_vs_completeness():
    print("=== DEMO 8: Integrity vs Completeness ===")
    case, engine, observer = Case(), build_engine(), ExecutionEvidenceObserver()
    observer.request_transition(engine, case, CaseState.INTAKE_RECEIVED)
    # Deliberately stop here -- never reach transparency evidence.

    records = observer.ledger.records_for_case(case.case_id)
    integrity = verify_integrity(observer.ledger.all_records())
    completeness = evaluate_completeness(
        records, case.case_id, required_event_types=["GOVERNANCE_TRANSITION", "TRANSPARENCY_RESULT"]
    )
    print(f"  Integrity: {integrity['result']}")
    print(f"  Completeness: {completeness['result']}, missing: {completeness['missing']}")
    return integrity["result"] == "INTEGRITY_VERIFIED" and completeness["result"] == "COMPLETENESS_FAILED"


def run_all_demos():
    demos = [
        demo_01_happy_path, demo_02_deny_by_default_denial, demo_03_human_authority_detour,
        demo_04_deadline_path, demo_05_failure_disposition_path, demo_06_execution_to_evidence,
        demo_07_hash_tamper_evidence, demo_08_integrity_vs_completeness,
    ]
    results = {}
    for demo in demos:
        passed = demo()
        results[demo.__name__] = passed
        print(f"  {'PASS' if passed else 'FAIL'}\n")

    print("=== SUMMARY ===")
    for name, passed in results.items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    print(f"\nALL DEMOS PASSED: {all(results.values())}")
    return results


if __name__ == "__main__":
    run_all_demos()
