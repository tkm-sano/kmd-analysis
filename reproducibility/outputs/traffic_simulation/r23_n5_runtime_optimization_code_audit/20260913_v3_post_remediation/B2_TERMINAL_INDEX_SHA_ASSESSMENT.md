# B2 terminal-index SHA assessment

Six B2 n=4 Nelder-Mead terminal JSON entries disagree with the SHA recorded in `20260911_v2/terminal_records.json`: B2-SHA-01 through B2-SHA-06. Each is a whole derived terminal artifact; expected and actual values are preserved verbatim in the prior inventory and were not rewritten. The recorded reconstruction identifies only `/scientific_result/exact_optimum_found` changing from false to true; raw probabilities, routes, optimizer traces and source authority reconstruct identically.

Classification: `DERIVED_ARTIFACT_MISMATCH`, severity `MODERATE`. Scientific result integrity is not shown numerically changed (`B2 scientific integrity 6/6` remains separately supported), but artifact-level reproducibility and provenance are broken. Required remediation is a new independently sealed index/artifact pair or an explicit immutable supersession record; do not alter historical hashes.
