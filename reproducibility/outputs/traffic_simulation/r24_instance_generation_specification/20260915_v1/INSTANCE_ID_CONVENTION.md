# Instance ID Convention

IDs are uppercase ASCII and zero-padded so lexical order is stable.

## Base IDs

- Primary: `R24-RND-N{nnn}-R{rr}`
- Structural: `R24-STR-{CLUSTERED|DISPERSED|MIXED}-N{nnn}-R{rr}`
- Anchor: `R24-ANCHOR-N{nnn}`

`nnn` is three-digit n (`N002`, `N020`); `rr` is two-digit repetition (`R01`–`R10`). Examples: `R24-RND-N004-R01`, `R24-STR-DISPERSED-N020-R03`, `R24-ANCHOR-N010`.

## Capacity-condition IDs

Append exactly one suffix to a base ID:

- `-RHO050`
- `-RHO070`
- `-RHO090`

The suffix represents target rho, not actual rho. Example: `R24-RND-N010-R07-RHO090`.

An anchor condition uses the anchor base prefix even though its data hash must reference the source primary condition. IDs are immutable across solvers and code versions. Regeneration with changed protocol, source, or selection requires a new specification/version namespace and cannot overwrite these IDs.
