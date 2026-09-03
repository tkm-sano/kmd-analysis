# Research Map Portal

`PYTHONPATH=05_src ./.conda/bin/python research_portal/serve.py` を実行し、`http://127.0.0.1:8876/`を開く。

PortalはConceptual Research MapとImplementation / Analysis Mapを主画面とし、研究の問いからcurrent stage、artifact traceability、Stage 1–11までを有向グラフで示す。stage構成の人間向け入口は[`RESEARCH_OVERVIEW.md`](../RESEARCH_OVERVIEW.md)であり、グラフtaxonomyは`reproducibility/config/research_portal/research_map_v1.yml`で同じ構成を表す。current network stateは`reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`を唯一のauthority入口として、accepted runのacceptance artifactとprovenance accountingから生成する。研究値をブラウザへハードコードしない。strict v17はHistorical、Hierarchical HybridはSupersededとして詳細領域から参照する。
