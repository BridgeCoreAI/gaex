"""
GAEX execution-to-evidence observer. Calls the real engine first, then
records the real result. No method here can set state or assert a
governance conclusion on its own; evidence only ever describes something
that genuinely already happened.
"""

from .evidence import EvidenceLedger


class ExecutionEvidenceObserver:
    def __init__(self, ledger: EvidenceLedger = None):
        self.ledger = ledger or EvidenceLedger()

    def request_transition(self, engine, case, target_state: str, context: dict = None):
        result = engine.request_transition(case, target_state, context or {})
        event_type = "TRANSITION_DENIED" if result.authorization_result == "DENIED" else "GOVERNANCE_TRANSITION"
        decision = result.reason if result.authorization_result == "DENIED" else result.resulting_state
        self.ledger.append(case.case_id, event_type, decision, actor="SYSTEM")
        return result
