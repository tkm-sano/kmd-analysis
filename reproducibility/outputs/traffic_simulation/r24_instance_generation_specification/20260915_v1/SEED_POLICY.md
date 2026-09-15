# Seed Policy

## Protocol and derivation

`PROTOCOL_ID = R24-INSTANCE-GEN-20260915-v1`

For a primary base instance, form this exact UTF-8 ASCII string with no newline:

`R24-INSTANCE-GEN-20260915-v1|suite=RND|n=<decimal n>|rep=<two-digit r>`

For a structural base instance:

`R24-INSTANCE-GEN-20260915-v1|suite=STR|structure=<CLUSTERED|DISPERSED|MIXED>|n=<decimal n>|rep=<two-digit r>`

Compute `seed_digest = SHA256(seed_material)`. Define `seed_uint64` as the unsigned big-endian integer represented by digest bytes 0–7. Persist the material, full digest, integer, and derivation rule.

## Selection score

For candidate ID `c`, compute:

`selection_score(c) = SHA256(seed_digest_hex + "|customer=" + c)`

using lowercase 64-character `seed_digest_hex`, exact delimiter text, UTF-8 encoding, and no newline. Compare full 32-byte digests as unsigned big-endian values; break an impossible/equal digest tie by bytewise customer ID.

This is the only randomization mechanism. It is algorithm- and library-independent; no PRNG, global RNG state, wall-clock value, manual seed list, rejection sampling, or seed search is permitted. The generation run must emit every planned primary and structural seed record in the suite manifest, including records whose instances later fail validation. Anchor aliases have no new seed and inherit the source primary seed fields.
