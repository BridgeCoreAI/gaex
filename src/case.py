"""
GAEX (Governing AI at Execution) -- Public Reference Demonstrator.

This is a SEPARATELY ENGINEERED demonstrator, not a redacted copy of any
private canonical system. Per the approved specification
(docs/PUBLIC-DEMONSTRATOR-SPECIFICATION.md, private repo), it uses a
single FLAT case model, deliberately non-isomorphic to any hierarchical
parent/branch architecture. No state name, control identifier, or
evidence event name here is drawn from any private canonical vocabulary.

This demonstrator translates selected obligations from the U.S. TAKE IT
DOWN Act and EU AI Act Article 50 into executable, deny-by-default
governance controls. It is a PoC using synthetic, fictitious data only.
It is NOT a production system, NOT legal advice, and NOT a certification
of statutory compliance.
"""

import uuid
from dataclasses import dataclass, field


class CaseState:
    CASE_OPENED = "CASE_OPENED"
    INTAKE_RECEIVED = "INTAKE_RECEIVED"
    VALIDATED = "VALIDATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    DEADLINE_ACTIVE = "DEADLINE_ACTIVE"
    DEADLINE_EXCEEDED = "DEADLINE_EXCEEDED"
    FAILURE_LOGGED = "FAILURE_LOGGED"
    EXECUTION_COMPLETE = "EXECUTION_COMPLETE"
    LATE_EXECUTION_COMPLETE = "LATE_EXECUTION_COMPLETE"
    TRANSPARENCY_CHECK = "TRANSPARENCY_CHECK"
    CASE_CLOSED = "CASE_CLOSED"
    TRANSPARENCY_INCOMPLETE = "TRANSPARENCY_INCOMPLETE"


@dataclass
class Case:
    """A single, flat governed case. No parent/child layering."""
    case_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: str = CaseState.CASE_OPENED
