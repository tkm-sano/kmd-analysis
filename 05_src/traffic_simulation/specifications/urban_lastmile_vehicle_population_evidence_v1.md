# Urban last-mile vehicle population evidence v1

> この文書はcanonical YAMLから自動生成する。表の手動編集は禁止する。

本研究は、大田区および近郊の配送拠点から、大田区内を中心とする最終需要地点への都市内ラストマイル配送を対象とする。vehicle populationは実験用scalar vehicle profileではない。現行`managed_urban_ev_delivery_v1`は変更しない。

## Table A — Last-mile vehicle universe

| ID | Modality | Universe | SUMO four-wheel |
|---|---|---:|---:|
| M0 | walking_and_hand_cart | True | False |
| M1 | bicycle_and_e_assist_cargo_bike | True | False |
| M2 | motorcycle_and_e_motorcycle | True | False |
| M3 | micro_delivery_mobility | True | False |
| M4 | four_wheel_goods_vehicle | True | True |
| M5 | autonomous_delivery_robot | True | False |
| M6 | drone | True | False |

## Table B — Four-wheel vehicle strata

| ID | Definition | Treatment | Included | Evidence | Exclusion reason |
|---|---|---|---:|---|---|
| F1 | 軽貨物バン・軽貨物車 | core | True | complete / BEV available | — |
| F2 | コンパクト商用バン | core_evidence_gap | True | incomplete / BEV unresolved | — |
| F3 | 大型商用バン | core_evidence_gap | True | incomplete / BEV unresolved | — |
| F4 | 小型配送トラック | core | True | partial / BEV available | — |
| F5 | 2t積載級 | core_sensitivity | True | partial / BEV available | — |
| F6 | 約3t積載級 | sensitivity | True | partial / BEV available | — |
| F7 | 中大型・幹線寄り | boundary | False | incomplete / BEV unresolved | 原則として都市内ラストマイル四輪母集団から除外 |

## Table C — Real vehicle evidence records

| ID | Stratum | Manufacturer | Model | Body | Powertrain | L | W | H | GVW | Payload | Battery | Range | Sources | Deployment evidence |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| F1-HONDA-NVAN-E-COMMON-2025 | F1 | Honda | N-VAN e: | van | battery_electric | 3.395 | 1.475 | 1.96 | — | — | 29.6 | 245 | SOURCE-HONDA-NVAN-E-PAYLOAD, SOURCE-HONDA-NVAN-E-TYPE | DEP-YAMATO-NVAN-E-PILOT |
| F1-MITSUBISHI-MINICAB-EV-2S-2025 | F1 | Mitsubishi Motors | Minicab EV | van | battery_electric | 3.395 | 1.475 | 1.915 | 1560 | 350 | 20.0 | 180 | SOURCE-MITSUBISHI-MINICAB-EV | — |
| F1-SUZUKI-E-EVERY-2S-2026 | F1 | Suzuki | e Every | van | battery_electric | 3.395 | 1.475 | 1.89 | — | 350 | 36.6 | 257 | SOURCE-SUZUKI-E-EVERY, SOURCE-SUZUKI-E-EVERY-EV | DEP-SAGAWA-LIGHT-EV-LASTMILE |
| F4-HINO-DUTRO-Z-EV-2026 | F4 | Hino | Dutro Z EV | walk_through_truck | battery_electric | 4.69 | 1.695 | 2.285 | 3440 | 950 | 46.7 | 184 | SOURCE-HINO-DUTRO-Z-EV | — |
| F4-ISUZU-ELFMIO-EV-CAPABILITY | F4 | Isuzu | ELFmio EV | cab_over_truck | battery_electric | — | 1.695 | — | — | 1050 | 44 | 115 | SOURCE-ISUZU-ELF-EV | — |
| F5-ISUZU-ELF-EV-NJR-CAPABILITY | F5 | Isuzu | ELF EV | cab_over_truck | battery_electric | — | 1.695 | — | — | 2000 | 44 | 120 | SOURCE-ISUZU-ELF-EV | — |
| F5-YAMATO-ECANTER-2023 | F5 | Mitsubishi Fuso | eCanter | cab_over_truck | battery_electric | 5.39 | 1.91 | 3.12 | 5870 | 2000 | 41 | 116 | SOURCE-YAMATO-ECANTER | DEP-YAMATO-ECANTER-900 |
| F6-ISUZU-ELF-EV-NPR-CAPABILITY | F6 | Isuzu | ELF EV | cab_chassis | battery_electric | — | 1.995 | — | — | — | 110 | 250 | SOURCE-ISUZU-ELF-EV | — |

## Table D — Empirical envelopes

| Stratum | Independent families | Evidence | Length | Width | Height | GVW | Payload | Battery | Range |
|---|---:|---:|---|---|---|---|---|---|---|
| F1 | 3 | 3 records | 3.395 (n=3) | 1.475 (n=3) | 1.89–1.96 (n=3) | 1560 (n=1) | 350 (n=2) | 20.0–36.6 (n=3) | 180–257 (n=3) |
| F2 | 0 | 0 records | — | — | — | — | — | — | — |
| F3 | 0 | 0 records | — | — | — | — | — | — | — |
| F4 | 2 | 2 records | 4.69 (n=1) | 1.695 (n=2) | 2.285 (n=1) | 3440 (n=1) | 950–1050 (n=2) | 44–46.7 (n=2) | 115–184 (n=2) |
| F5 | 2 | 2 records | 5.39 (n=1) | 1.695–1.91 (n=2) | 3.12 (n=1) | 5870 (n=1) | 2000 (n=2) | 41–44 (n=2) | 116–120 (n=2) |
| F6 | 1 | 1 records | — | 1.995 (n=1) | — | — | — | 110 (n=1) | 250 (n=1) |
| F7 | 0 | 0 records | — | — | — | — | — | — | — |

`observed_empirical_envelope`は観測recordの範囲であり、確率分布、日本全体のP95、または独立一様分布ではない。F2/F3の欠損は推定で補完しない。
