# Clean-run authority

The three instances are read from `n5_instance_selection.json` and the directed routing matrix is read from the V18 `routing_arcs.csv`. The runner independently enumerates 120 permutations and derives the exact reference before calling the v4 implementation. The frozen source commit is the commit containing this runner and manifest; each run records start/end source hashes and output SHA.

