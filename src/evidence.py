"""
GAEX evidence ledger. Append-only, SHA-256 hash-chained, tamper-evident.

SECURITY CLAIM BOUNDARY: append-only at the application level,
hash-chained, and tamper-evident (alteration is detectable). This is NOT
claimed to be tamper-proof, immutable storage, nonrepudiable, or legally
admissible.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    sequence_number: int
    case_id: str
    event_type: str
    decision: Optional[str]
    actor: str
    timestamp: str
    previous_hash: Optional[str]
    record_hash: str


_INTEGRITY_FIELDS = ["evidence_id", "sequence_number", "case_id", "event_type", "decision", "actor", "timestamp"]


def _canonical_bytes(fields: dict) -> bytes:
    return json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def compute_hash(fields: dict, previous_hash: Optional[str]) -> str:
    hasher = hashlib.sha256()
    hasher.update(_canonical_bytes(fields))
    if previous_hash:
        hasher.update(previous_hash.encode("utf-8"))
    return hasher.hexdigest()


class EvidenceLedger:
    def __init__(self):
        self._records: List[EvidenceRecord] = []

    def append(self, case_id: str, event_type: str, decision: Optional[str], actor: str = "SYSTEM") -> EvidenceRecord:
        sequence_number = len(self._records) + 1
        previous_hash = self._records[-1].record_hash if self._records else None
        fields = {
            "evidence_id": str(uuid.uuid4()), "sequence_number": sequence_number,
            "case_id": case_id, "event_type": event_type, "decision": decision,
            "actor": actor, "timestamp": now_iso(),
        }
        record_hash = compute_hash(fields, previous_hash)
        record = EvidenceRecord(**fields, previous_hash=previous_hash, record_hash=record_hash)
        self._records.append(record)
        return record

    def all_records(self) -> List[EvidenceRecord]:
        return list(self._records)

    def records_for_case(self, case_id: str) -> List[EvidenceRecord]:
        return [r for r in self._records if r.case_id == case_id]


def verify_integrity(records: List[EvidenceRecord]) -> dict:
    expected_seq = 1
    previous_hash = None
    for record in records:
        if record.sequence_number != expected_seq:
            return {"result": "INTEGRITY_FAILURE", "reason": "SEQUENCE_GAP"}
        if record.previous_hash != previous_hash:
            return {"result": "INTEGRITY_FAILURE", "reason": "PREVIOUS_HASH_MISMATCH"}
        fields = {name: getattr(record, name) for name in _INTEGRITY_FIELDS}
        recomputed = compute_hash(fields, record.previous_hash)
        if recomputed != record.record_hash:
            return {"result": "INTEGRITY_FAILURE", "reason": "RECORD_HASH_MISMATCH"}
        previous_hash = record.record_hash
        expected_seq += 1
    return {"result": "INTEGRITY_VERIFIED", "reason": None}


def evaluate_completeness(records: List[EvidenceRecord], case_id: str, required_event_types: List[str]) -> dict:
    """
    Distinct from integrity. Integrity asks whether records are
    structurally sound. Completeness asks whether the required evidence
    categories for this case actually exist.
    """
    present = {r.event_type for r in records if r.case_id == case_id}
    missing = [event_type for event_type in required_event_types if event_type not in present]
    if missing:
        return {"result": "COMPLETENESS_FAILED", "missing": missing}
    return {"result": "COMPLETENESS_VERIFIED", "missing": []}
