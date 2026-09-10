# Optional Docker environments for the Tokyo traffic extension

Hayateのnative Conda環境が現在の正本実行環境である。ここにあるDocker構成は、Docker daemonを利用できる環境で追加クロスチェックを行うための副次環境であり、Hayate実行の必須条件ではない。

Python依存の正本は`reproducibility/environment/requirements-analysis.txt`である。Dockerfileもこのファイルを参照し、Docker配下に同じ依存一覧を重複保持しない。正本の構築・検証手順は`reproducibility/environment/README.md`を参照する。

これらのサービスは、`legacy/non_sumo_route_proxy_analysis/reproducibility/requirements-lock.txt`に記録された旧研究の凍結環境を置き換えない。

## Services

- `analysis`: Python 3.11 environment for road-network processing,
  time-dependent routing, calibration, and classical EVRP baselines.
- `sumo`: pinned Eclipse SUMO 1.24.0 environment for network conversion and
  microscopic traffic simulation.

Both services use `linux/amd64` as the secondary Docker cross-check platform. On Apple
Silicon Macs this runs through Docker Desktop's architecture emulation; on an
AMD64 Linux server it runs natively. The SUMO image is pinned by digest because
the upstream `v1_25_0` tag currently reports SUMO 1.24.0 at runtime.

The repository is mounted at `/workspace`. Raw third-party data and generated
outputs remain on the host and are not copied into container images.

## SUMO network-build execution boundary

The network-build workflow deliberately keeps Python analysis and SUMO
execution in separate services:

- `analysis` validates governed YAML, source-registry rows, study-area
  versions, and SHA-256 values; it generates a `.netccfg` and build manifest,
  then validates the resulting `.net.xml`.
- `sumo` executes `netconvert`, `sumo`, and `duarouter` inside the optional
  Docker boundary. Its digest-pinned image is the Docker cross-check SUMO
  environment; the canonical runtime is the Hayate native SUMO 1.24.0 install.

Both services exchange generated files through the shared `/workspace` bind
mount. Do not install a second SUMO copy in the `analysis` image, invoke the
Docker daemon from inside `analysis`, or type unrecorded `netconvert` options
directly at the command line. The generated `.netccfg` must come from the
Git-managed `reproducibility/config/traffic_simulation/sumo_network.yml`.

The planned user-facing entry point is:

```bash
docker/run_sumo_network_build.sh structural ota_ward osm_geofabrik_kanto_20260716
docker/run_sumo_network_build.sh formal ota_ward osm_geofabrik_kanto_20260716
```

It will run prepare in `analysis`, conversion in `sumo`, and validation in
`analysis`, stopping immediately if any phase fails. This entry point and the
SUMO network configuration are planned and are not implemented yet.

## Optional Docker checks

Start Docker Desktop (or another compatible Docker daemon) before running
these commands. `docker compose config` can validate the Compose file without
the daemon, but builds and container runs require it. These commands do not
replace the canonical Hayate native regression.

```bash
docker compose build analysis
docker compose run --rm analysis python --version
docker compose run --rm analysis python -m pytest -q legacy/non_sumo_route_proxy_analysis/reproducibility/tests/test_audit.py
docker compose run --rm sumo sumo --version
docker compose run --rm sumo netconvert --version
```

Do not write new traffic-simulation results into the existing synthetic EVRP
directories. Use the dedicated paths documented in
`05_src/traffic_simulation/README.md`.
