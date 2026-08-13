"""
GAEX transition map: 14 entries, matching the approved specification
exactly. Everything not listed here is denied by absence.
"""

from .case import CaseState as S
from .controls import CONTROLS
from .engine import GAEXEngine

TRANSITION_MAP = [
    {"source": S.CASE_OPENED, "target": S.INTAKE_RECEIVED,
     "control": "INTAKE-GATE", "acceptable_outcomes": ["PASS"]},

    {"source": S.INTAKE_RECEIVED, "target": S.VALIDATED,
     "control": "VALIDATION-GATE", "acceptable_outcomes": ["PASS"]},

    {"source": S.INTAKE_RECEIVED, "target": S.REVIEW_REQUIRED,
     "control": "VALIDATION-GATE", "acceptable_outcomes": ["AMBIGUOUS"]},

    {"source": S.REVIEW_REQUIRED, "target": S.VALIDATED,
     "control": "REVIEW-AUTHORITY-GATE", "acceptable_outcomes": ["AUTHORIZED"]},

    {"source": S.VALIDATED, "target": S.DEADLINE_ACTIVE,
     "control": "DEADLINE-GATE-START", "acceptable_outcomes": ["PASS"]},

    {"source": S.DEADLINE_ACTIVE, "target": S.EXECUTION_COMPLETE,
     "control": "EXECUTION-GATE", "acceptable_outcomes": ["PASS"]},

    {"source": S.DEADLINE_ACTIVE, "target": S.DEADLINE_EXCEEDED,
     "control": "DEADLINE-GATE-CHECK", "acceptable_outcomes": ["BREACH"]},

    {"source": S.DEADLINE_ACTIVE, "target": S.FAILURE_LOGGED,
     "control": "EXECUTION-GATE", "acceptable_outcomes": ["FAIL"]},

    {"source": S.DEADLINE_EXCEEDED, "target": S.LATE_EXECUTION_COMPLETE,
     "control": "EXECUTION-GATE", "acceptable_outcomes": ["PASS-LATE"]},

    {"source": S.FAILURE_LOGGED, "target": S.EXECUTION_COMPLETE,
     "control": "FAILURE-DISPOSITION-GATE", "acceptable_outcomes": ["RESOLVED"]},

    {"source": S.EXECUTION_COMPLETE, "target": S.TRANSPARENCY_CHECK,
     "control": "TRANSPARENCY-GATE-START", "acceptable_outcomes": ["PASS"]},

    {"source": S.LATE_EXECUTION_COMPLETE, "target": S.TRANSPARENCY_CHECK,
     "control": "TRANSPARENCY-GATE-START", "acceptable_outcomes": ["PASS"]},

    {"source": S.TRANSPARENCY_CHECK, "target": S.CASE_CLOSED,
     "control": "CLOSURE-GATE", "acceptable_outcomes": ["CLOSE"]},

    {"source": S.TRANSPARENCY_CHECK, "target": S.TRANSPARENCY_INCOMPLETE,
     "control": "CLOSURE-GATE", "acceptable_outcomes": ["INCOMPLETE"]},
]


def build_engine() -> GAEXEngine:
    return GAEXEngine(TRANSITION_MAP, CONTROLS)
