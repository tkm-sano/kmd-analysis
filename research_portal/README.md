# Research Visualization Portal

Run locally with `PYTHONPATH=05_src ./.conda/bin/python research_portal/serve.py`, then open `http://127.0.0.1:8876/`.

The default port is `8876`. Override it when needed, for example with
`PORT=9000 PYTHONPATH=05_src ./.conda/bin/python research_portal/serve.py`.

The server reads only `reproducibility/config/research_portal/registry.yml` and exposes its parsed contents at `/api/registry`; the browser does not crawl repository Evidence.

The EV delivery map supports a Registry-driven propagation mode. Open
`/?view=current&propagate=<map-node-id>` to highlight confirmed and unresolved
downstream relations while preserving the surrounding map context.
