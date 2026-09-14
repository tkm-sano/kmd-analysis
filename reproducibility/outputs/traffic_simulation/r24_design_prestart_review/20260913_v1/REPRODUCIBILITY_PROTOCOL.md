# R24 reproducibility protocol

Freeze protocol version, source SHA, input SHA, environment manifest, run manifest, customer sample, demand vector, Q, K, encoding, penalties, p, optimizer, initialization, stopping rule, and resource budget before execution. Emit `RUN_START` and `RUN_END`. Generate the exact reference independently of the QUBO builder. Validators fail closed; invalid states are discarded without repair or renormalization. No silent rerun, favorable-run selection, or post-hoc scenario change is allowed.

Optimizer success is recorded separately from route recovery. Scientific results and benchmark results are separate schemas. Any approved change creates a new protocol version and a new input manifest; the old protocol remains immutable.

