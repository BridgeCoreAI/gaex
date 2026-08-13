# GAEX , Governing AI at Execution

**A public governance-engineering reference demonstrator by BridgeCore AI.**

## What this is

GAEX proves that selected obligations under the U.S. TAKE IT DOWN Act and EU AI Act Article 50 can be translated into executable, deny-by-default governance controls, not just policy documentation. It demonstrates real governance properties through real, runnable code and tests, not a description of them.

GAEX is a **separately engineered demonstrator**, not a redacted copy of BridgeCore AI's private canonical governance-engineering system. It uses a deliberately simpler, flat case model and its own vocabulary throughout.

## What this is NOT

- Not a production system
- Not legal advice
- Not a certification of statutory compliance with any law
- Not a claim of complete TAKE IT DOWN Act or EU AI Act coverage
- Not a claim of tamper-*proof* evidence (the evidence ledger is tamper-*evident*: alteration is detectable, not impossible)
- Not legally admissible evidence

All data, cases, and scenarios used in tests and demonstrations are synthetic and fictitious.

## What GAEX demonstrates

| Property | Where |
|---|---|
| Deny-by-default governance execution | `src/engine.py` |
| Governed human authority, unauthorized attempts rejected and evidenced | `src/controls.py` (`REVIEW-AUTHORITY-GATE`) |
| Regulatory timing affecting runtime execution | `src/controls.py` (`DEADLINE-GATE-CHECK`) |
| Independent verification of separate obligations, never collapsed into one result | `src/controls.py` (`CLOSURE-GATE`, provenance/disclosure subchecks) |
| Explicit governed outcomes for failures | `src/controls.py` (`FAILURE-DISPOSITION-GATE`) |
| Evidence generated only from real execution | `src/observer.py` |
| Tamper-evident, hash-chained evidence | `src/evidence.py` |
| Evidence integrity and completeness evaluated independently | `src/evidence.py` (`verify_integrity`, `evaluate_completeness`) |

## Running it

```bash
python -m pytest -q      # 16 tests
python -m src.demos      # 8 runnable demonstrations
```

## Architecture

A single, flat `Case` object with one `state` field, a deny-by-default transition engine that denies anything not explicitly mapped, nine control functions (three implemented in real depth as the "featured controls" above), and a small, standalone, SHA-256 hash-chained evidence ledger.

12 states, 14 transitions, 16 tests. Deliberately small: this repository exists to prove specific governance properties are real and testable, not to reproduce a full production system.

## Relationship to BridgeCore AI's private work

GAEX is derived from a private, five-stage governance-engineering proof of concept (the NCII Governance Workflow), which underwent extensive adversarial testing, including multiple rounds of independent review that found and corrected real governance defects. That private system remains BridgeCore AI's canonical implementation. GAEX exists to let the public verify, directly and independently, that the underlying governance-engineering methodology produces real, testable, deny-by-default systems, without exposing the private system's reusable implementation.

---

*Governance is not what is defined. It is what is enforced at execution.*
