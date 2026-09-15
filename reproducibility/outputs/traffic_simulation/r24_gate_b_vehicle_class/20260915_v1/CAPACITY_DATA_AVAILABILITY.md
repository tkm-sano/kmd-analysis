# Vehicle-side capacity data availability

Gate C remains open. This file reports vehicle-side evidence only and does not define demand units or `Q`.

- `MASS_WELL_SUPPORTED_ON_VEHICLE_SIDE`: manufacturer payload values are available for coherent primary-class variants. Minicab EV 2-seat and e Every 2-seat each publish 350 kg; Honda publishes seat/configuration-dependent 350/300/150 kg values.
- `VOLUME_PARTIALLY_SUPPORTED_BY_DIMENSIONS_NOT_USABLE_VOLUME`: internal cargo dimensions are published for Minicab EV and Honda variants, and a floor length is available for e Every. No reviewed source supplies a directly comparable certified usable cargo-volume value in m³ across all primary references. Exterior dimensions are not cargo volume, and rectangular multiplication is not adopted as usable volume.
- `PARCEL_COUNT_NOT_MANUFACTURER_SPECIFIED`: no manufacturer publishes parcel-count capacity. Any standardized load-unit or parcel-count capacity needs demand/package evidence and loading rules in Gate C.

Light-duty truck payload values are also strong but upfit-dependent: Dutro Z EV 950 kg completed vehicle, ELFmio EV 1,050 kg capability, ELF EV NJR 2,000 kg capability, and Yamato eCanter 2,000 kg completed operator body. These values do not define the primary-class capacity.

`Q=2,000 kg` remains solely the `managed_urban_ev_delivery_v1` fixed model assumption and historical eCanter-based fixture value. It may remain a labeled legacy/comparison scenario. It is not inherited by the kei primary and is not frozen here.

