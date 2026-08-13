"""
GAEX transition engine: deny-by-default, deliberately minimal.

Any (source_state, target_state) pair with no entry in the transition map
is denied automatically, with no explicit "denial rule" written for it.
The absence of a mapping IS the enforcement mechanism. This is the single
core property GAEX exists to prove.
"""

import uuid
from dataclasses import dataclass
from typing import Optional, Callable, Dict, List


@dataclass
class TransitionResult:
    transition_id: str
    source_state: str
    requested_target_state: str
    resulting_state: str
    authorization_result: str  # "AUTHORIZED" or "DENIED"
    reason: Optional[str]
    control_id: Optional[str]


class GAEXEngine:
    def __init__(self, transition_map: List[dict], controls: Dict[str, Callable]):
        self._map = {}
        for entry in transition_map:
            key = (entry["source"], entry["target"])
            self._map[key] = entry
        self._controls = controls

    def request_transition(self, case, target_state: str, context: dict = None) -> TransitionResult:
        context = context or {}
        source_state = case.state
        transition_id = str(uuid.uuid4())
        entry = self._map.get((source_state, target_state))

        if entry is None:
            # No authorizing control exists for this transition. Denied by
            # absence, not by an explicit rule written for this specific case.
            return TransitionResult(
                transition_id=transition_id, source_state=source_state,
                requested_target_state=target_state, resulting_state=source_state,
                authorization_result="DENIED", reason="NO_AUTHORIZING_CONTROL", control_id=None,
            )

        control_id = entry["control"]
        control_fn = self._controls[control_id]
        outcome = control_fn(case, context)

        if outcome in entry["acceptable_outcomes"]:
            case.state = target_state
            return TransitionResult(
                transition_id=transition_id, source_state=source_state,
                requested_target_state=target_state, resulting_state=target_state,
                authorization_result="AUTHORIZED", reason=None, control_id=control_id,
            )

        return TransitionResult(
            transition_id=transition_id, source_state=source_state,
            requested_target_state=target_state, resulting_state=source_state,
            authorization_result="DENIED", reason="CONTROL_OUTCOME_NOT_ACCEPTABLE", control_id=control_id,
        )
