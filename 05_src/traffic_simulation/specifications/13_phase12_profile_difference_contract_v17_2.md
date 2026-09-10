# Phase 12 Structural / Formal Profile Difference Contract v1.2.0

This specification implements adopted decision `DEC-P12-FORMAL-ONLY-PROFILE-DIFFERENCE-002`.
It applies to Phase 12 population units and does not promote a failed run or
change Formal Network Acceptance.

Structural is a simulation-only candidate profile. Formal is the fail-closed
profile used by Formal attribute gates. Their populations are compared by the
declared identity axes; a simple subset invariant is not used.

For every unit, the contract records `common`, `structural_only`, `formal_only`,
`authorized_formal_only`, `unauthorized_formal_only`, and
`same_identity_inconsistent`. `formal_only` is the union of the two Formal-only
classifications. The required gates are:

```
unauthorized_formal_only == 0
same_identity_inconsistent == 0
```

An authorized Formal-only identity requires a registered adopted rule linked to
an adopted decision, complete provenance, source evidence, `formal_eligible=true`,
an allowed `value_origin`, Formal-policy-compliant `assumption_ids`, and valid
identity/lineage. Missing evidence is unauthorized; it is not inferred from a
matching count, Way ID, SUMO output, typemap, or Structural placeholder.

Permission-only divergence is unauthorized unless the corresponding Formal-only
lane identity is itself authorized and the permission record traces to that lane.
Thus the required chain is Formal-only permission → Formal-only lane → adopted
lane rule/decision. Same identity with inconsistent immutable lineage is a
separate failure class.

All difference records and aggregates are retained. No authorized difference is
copied into Structural or removed from accounting. This contract revision is a
mechanical implementation of the adopted decision; it does not add a research
assumption and does not reduce blocker populations.

The `structural_invalid` profile-difference gate evaluates only records
classified as `structural_only` by the Structural/Formal comparison. A
Structural record classified as `common` is outside this gate. The existence of
a valid `structural_only` record is not itself a failure; only a difference
record with missing or unregistered Structural provenance is invalid.
