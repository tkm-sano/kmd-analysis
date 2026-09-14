# Validation architecture

Current `r23_validation_gate.py` rejects empty checks, unknown statuses, duplicate/extra/missing IDs, unexecuted checks, missing evidence and failed checks. `r23_evidence_gate.py` independently checks full manifests, exact references, route/probability consistency and hashes. Negative regression fixtures cover malformed probability inputs and incomplete metadata. No unconditional active PASS path was found in the inspected gates. Historical PASS strings remain archival evidence. Result: `SUPPORTED_WITH_LIMITATIONS`; a new full negative-fixture run was not performed.
