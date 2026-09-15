# Deferred physical-capacity scope

## Primary R24 boundary

R24 primary uses `METHODOLOGICAL_PARCEL_EQUIVALENT`. It makes no physical payload, cargo-volume, parcel-count capacity or utilization claim.

## Deferred scenarios

- mass demand and capacity `[kg]`
- volume demand and usable cargo capacity `[m^3]`
- joint mass-volume capacity
- vehicle payload utilization and operational load factor

The demand-side Japanese residential B2C parcel-mass authority remains `DEMAND_SIDE_MASS_AUTHORITY_INSUFFICIENT`; usable parcel/cargo volume is also not established. These scenarios require separately versioned demand and vehicle authority before use.

## Vehicle evidence boundary

The kei-class electric commercial van remains the R24 primary vehicle class for routing and future scenario compatibility. Variant-specific official payload evidence is approximately the 350 kg class, but:

- 350 kg is not a universal class constant;
- it is not converted to 350 parcel-equivalents;
- it does not set or validate methodological `Q=14`;
- methodological `rho` is not kg payload utilization.

The legacy `Q=2,000 kg` fixed research profile also remains reference-only and is not inherited.
