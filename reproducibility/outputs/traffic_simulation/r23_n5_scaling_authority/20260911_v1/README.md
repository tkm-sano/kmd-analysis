# R23 N5 Scaling Authorization

判定: `R23_N5_SCALING_NOT_AUTHORIZED_RESOURCE_LIMIT`。n=5 QAOA scientific executionは実行していない。

Routing Baselineのn=10 fixtureをcandidate populationとし、complete directed reachabilityを確認した上で、seed 2301のSHA256組合せrankから3 instanceを決定的に選定した。各instanceについて120 routeを古典列挙し、unique optimum、second-best、cost distributionを記録した。

n=5 λは既存λ=3.0を流用せず、`λ > (n+1)/2` に基づく最小自然数 `λ=4.0` を新規authority化した。validationは分析的係数、one-hot構造、known valid/invalid、targeted local、seed 2501の4096 bitstrings、exact route enumerationでPASSした。

静的resourceはavailable RAM 1.4 TiBでraw 0.5 GiBを収容可能だが、現環境ではQiskit/Aer/SciPyが未導入でfrozen runtimeとも不一致。actual Aer peak memoryとexact CPU Aer feasibilityが未検証のため、実行認可を出さない。次は `R24_CAPACITY_EXTENSION_DESIGN`。
