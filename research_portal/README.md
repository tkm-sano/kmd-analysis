# Research Portal

`PYTHONPATH=05_src ./.conda/bin/python research_portal/serve.py` を実行し、`http://127.0.0.1:8876/`を開く。

画面のcurrent stateは、`reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`を唯一の入口として、accepted runのacceptance artifactとprovenance accountingからサーバー側で生成する。ブラウザ側に研究値をハードコードしない。strict v17はHistorical comparison、Hierarchical HybridはSupersededとして表示する。
