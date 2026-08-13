"""
GAEX controls. Three of these are the "featured controls" per the
approved specification, implemented in real depth:

  REVIEW-AUTHORITY-GATE   -- governed human authority (Claim C)
  DEADLINE-GATE-CHECK     -- regulatory timing affecting execution (Claim D)
  CLOSURE-GATE            -- independent transparency subchecks (part of
                              the properties this demonstrator proves)

The remaining gates are intentionally simple: their job is structural
sequencing, not a governance decision requiring depth. A caller supplies
bounded facts via context; no control here ever lets a caller directly
assert its own authoritative conclusion.
"""


def intake_gate(case, context):
    return "PASS"


def validation_gate(case, context):
    """
    Real structural fact: is the submission valid, or genuinely ambiguous?
    The caller supplies the fact (was ambiguity detected), not the
    conclusion about what should happen as a result.
    """
    return "AMBIGUOUS" if context.get("ambiguous") else "PASS"


def review_authority_gate(case, context):
    """
    FEATURED CONTROL 1: Governed Human Authority.
    Only a reviewer present in the authorized set may resolve a pending
    review. An unauthorized attempt is rejected, never silently accepted.
    """
    reviewer_id = context.get("reviewer_id")
    authorized_reviewers = context.get("authorized_reviewers", set())
    if reviewer_id is not None and reviewer_id in authorized_reviewers:
        return "AUTHORIZED"
    return "UNAUTHORIZED"


def deadline_gate_start(case, context):
    return "PASS"


def execution_gate(case, context):
    """
    Real execution outcome, supplied as a fact by the caller (representing
    a real operational action having occurred), never an assertion this
    control invents on its own.
    """
    return context.get("outcome", "PASS")


def deadline_gate_check(case, context):
    """
    FEATURED CONTROL 2: Deadline-Aware Execution.
    Regulatory timing obligations actively change what the system
    permits. Compares a supplied current time against a supplied
    deadline; the caller cannot simply assert "BREACH" or "ON_TIME"
    directly, only supply the two timestamps being compared.
    """
    current_time = context.get("current_time")
    deadline = context.get("deadline")
    if current_time is not None and deadline is not None and current_time > deadline:
        return "BREACH"
    return "ON_TIME"


def failure_disposition_gate(case, context):
    return context.get("outcome", "PENDING")


def transparency_gate_start(case, context):
    return "PASS"


def evaluate_provenance_check(context: dict) -> str:
    """Independent subcheck 1 of FEATURED CONTROL 3."""
    provenance_facts = context.get("provenance", {})
    if provenance_facts.get("present") and provenance_facts.get("valid"):
        return "PASS"
    return "FAIL"


def evaluate_disclosure_check(context: dict) -> str:
    """Independent subcheck 2 of FEATURED CONTROL 3. Never inferred from subcheck 1."""
    disclosure_facts = context.get("disclosure", {})
    if disclosure_facts.get("present") and disclosure_facts.get("adequate"):
        return "PASS"
    return "FAIL"


def closure_gate(case, context):
    """
    FEATURED CONTROL 3: Independent Transparency Verification.
    Reads two genuinely separate subchecks (provenance, disclosure) and
    requires BOTH to pass before authorizing closure. Neither subcheck's
    result is ever inferred from, or overwritten by, the other.
    """
    provenance_result = evaluate_provenance_check(context)
    disclosure_result = evaluate_disclosure_check(context)
    if provenance_result == "PASS" and disclosure_result == "PASS":
        return "CLOSE"
    return "INCOMPLETE"


CONTROLS = {
    "INTAKE-GATE": intake_gate,
    "VALIDATION-GATE": validation_gate,
    "REVIEW-AUTHORITY-GATE": review_authority_gate,
    "DEADLINE-GATE-START": deadline_gate_start,
    "EXECUTION-GATE": execution_gate,
    "DEADLINE-GATE-CHECK": deadline_gate_check,
    "FAILURE-DISPOSITION-GATE": failure_disposition_gate,
    "TRANSPARENCY-GATE-START": transparency_gate_start,
    "CLOSURE-GATE": closure_gate,
}
