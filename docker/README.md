# Docker environments for the Tokyo traffic extension

These services extend the repository without replacing the frozen research
environment described in `reproducibility/requirements-lock.txt`.

## Services

- `analysis`: Python 3.11 environment for road-network processing,
  time-dependent routing, calibration, and classical EVRP baselines.
- `sumo`: pinned Eclipse SUMO 1.24.0 environment for network conversion and
  microscopic traffic simulation.

Both services use `linux/amd64` as the canonical research platform. On Apple
Silicon Macs this runs through Docker Desktop's architecture emulation; on an
AMD64 Linux server it runs natively. The SUMO image is pinned by digest because
the upstream `v1_25_0` tag currently reports SUMO 1.24.0 at runtime.

The repository is mounted at `/workspace`. Raw third-party data and generated
outputs remain on the host and are not copied into container images.

## Initial checks

Start Docker Desktop (or another compatible Docker daemon) before running
these commands. `docker compose config` can validate the Compose file without
the daemon, but builds and container runs require it.

```bash
docker compose build analysis
docker compose run --rm analysis python --version
docker compose run --rm analysis pytest -q reproducibility/tests/test_audit.py
docker compose run --rm sumo sumo --version
docker compose run --rm sumo netconvert --version
```

Do not write new traffic-simulation results into the existing synthetic EVRP
directories. Use the dedicated paths documented in
`05_src/traffic_simulation/README.md`.
