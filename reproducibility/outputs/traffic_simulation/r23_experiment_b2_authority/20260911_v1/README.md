# R23 Experiment B2 Execution Authorization Decision

Classification: `EXPERIMENT_B2_REQUIRES_DESIGN_REVIEW`

This namespace contains a non-authorizing preflight and a proposed six-run scope. No B2 scientific run was executed.

The B1 Evidence Review is fixed at SHA-256 `8db16a3f66191c1de34b4f1cbaededdf9760cf0fb13f9e1d852b2c4e26cae767` and classified `EXPERIMENT_B1_EVIDENCE_ACCEPTED_WITH_LIMITATIONS`.

The technical preflight passes for the six formal instance/depth pairs, but the authorization gate is blocked because Experiment B design authority does not freeze Nelder-Mead `xatol`/`fatol` or optimizer-specific options. SciPy defaults were not inferred.

Required next task: design review to freeze these parameters, then regenerate authorization.
