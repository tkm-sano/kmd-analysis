# Predicate Generator Synthetic Fixture

This relation-closed OSM fixture exercises the governed predicate derivation
rules without representing Ota Ward production data.

- Way `101` contains bridge, grade-separation, directional lane, turn-lane,
  bus-lane, directional speed, conditional speed, vehicle-specific speed, and
  advisory speed semantics.
- Way `102` contains tunnel, reversible-flow, tidal-flow, conflicting lane,
  variable speed, and multiple speed semantics.
- Way `103` has no `highway` tag and enters the population only through an
  explicit `topology_support` role decision.
- Way `104` represents an explicitly excluded highway way.

Tests construct a temporary source registry with repository-relative,
SHA-256-verified role, external-predicate, and override sources. The fixture is
declared as `synthetic_fixture`; it cannot be treated as accepted real data.
