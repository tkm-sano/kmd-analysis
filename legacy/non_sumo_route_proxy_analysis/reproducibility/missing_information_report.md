# Missing Information Report

This report never substitutes plausible values for absent evidence.

## MI-001 — historical Open Charge Map snapshot identity
- **Status:** MISSING
- **Needed:** exact research-time API request/response and query parameters
- **Evidence checked:** local 2026-07-05 snapshot (137 connection records), downloader, slide 17
- **Impact:** current snapshot is auditable but strict historical API reproduction is not guaranteed
- **Affected results:** charger screening, access, assisted range, duration
- **Resolution:** archive the raw response, request URL, timestamp, and checksum

## MI-002 — vehicle-source URL verification
- **Status:** MISSING
- **Needed:** immutable manufacturer pages/PDFs for every one of the 10 rows
- **Evidence checked:** vehicle snapshot, source registry, slide 22 (“Source URLs to be verified”)
- **Impact:** 81.2 km and 2,000 kg are reproducible as scenario inputs, but source-chain verification is incomplete
- **Affected results:** payload, range, charging duration
- **Resolution:** archive official specifications and record page/section

## MI-003 — circuit-width slide values
- **Status:** REFERENCE_ONLY
- **Needed:** paper page/equation and exact instance substitution yielding 128, 256, 6,080, and 14,528
- **Evidence checked:** local Leonidas and Onah PDFs/text and evidence tables
- **Impact:** slide comparison cannot be certified as reproduced
- **Affected results:** circuit-width figure and resource interpretation
- **Resolution:** provide extraction worksheet with formula, instance, modality, and page

## MI-004 — operational observations and classical optimum
- **Status:** MISSING
- **Needed:** observed orders/routes and a specified classical EVRP baseline
- **Impact:** model-conditional rates cannot be interpreted as operational failure or optimized feasibility
- **Resolution:** obtain governed operational data and preregister the optimization formulation
