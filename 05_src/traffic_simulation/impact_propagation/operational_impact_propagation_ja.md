# 配送計画から配送可能人口相当までの運用波及

この図は、生成された配送計画の違いが、技術システム、運用資源の使用、人口に基づく社会的代理指標という三つの層を通じて、配送完了量および配送可能人口相当へどのように波及するかを示す。

ここで示すのは、本研究のモデル内における処理・判定・集計の関係であり、実社会における因果効果を実証するものではない。中間層は運用資源と経済との接点を示すが、金銭価値へ換算しない。最終層の配送可能人口相当は、実際に配送を受けた人数ではない。排出量、顧客満足度、社会厚生および地域公平性は、現在の評価範囲に含めない。

```mermaid
flowchart LR
    subgraph input["共通の実験条件"]
        road["検証済み道路網"]
        traffic["交通需要・信号・混雑条件"]
        demand["人口に基づく<br/>合成配送需要"]
        vehicle["車両・積載量・電池・<br/>充電条件"]
        time["出発時刻・配送時間枠"]
        random["事前登録した乱数条件"]
    end

    subgraph technical["技術システム"]
        assignment["車両への配送割当て"]
        order["顧客の訪問順序"]
        feasibility["計画段階の<br/>制約充足判定"]
        route["共通規則で生成した<br/>道路経路"]
        driving["同一交通環境での<br/>車両走行"]
    end

    subgraph resource["運用資源の使用<br/>経済との接点・金銭換算なし"]
        distance["実現した走行距離"]
        duration["実現した車両旅行時間"]
        delay["交通・信号による遅延"]
        electricity["電力消費と<br/>電池残量"]
        charging["充電回数"]
    end

    subgraph social["配送成立と人口に基づく社会的代理指標<br/>実際の受取人数ではない"]
        deadline["配送期限を満たしたか"]
        capacity["積載量制約を満たしたか"]
        battery["電池・充電条件を<br/>満たしたか"]
        return_condition["帰着・終端条件を<br/>満たしたか"]
        completed["すべての条件を満たした<br/>配送完了量"]
        completion_rate["配送完了率"]
        population_result["配送可能人口相当"]
    end

    road --> route
    traffic --> driving
    demand --> assignment
    vehicle --> assignment
    vehicle --> feasibility
    time --> feasibility
    random --> driving

    assignment --> order
    order --> feasibility
    feasibility --> route
    route --> driving

    driving --> distance
    driving --> duration
    driving --> delay
    driving --> electricity
    driving --> charging

    duration --> deadline
    delay --> deadline
    assignment --> capacity
    electricity --> battery
    charging --> battery
    driving --> return_condition

    deadline --> completed
    capacity --> completed
    battery --> completed
    return_condition --> completed

    completed --> completion_rate
    completed --> population_result
```

図の中心となる三層の波及関係は次のとおりである。

```text
技術システム
配送割当て・訪問順序・道路経路・車両走行
        ↓
運用資源の使用
走行距離・車両旅行時間・遅延・電力消費・充電
経済との接点を示すが金銭換算しない
        ↓
配送成立と人口に基づく社会的代理指標
条件判定・配送完了量・配送完了率・配送可能人口相当
実際の受取人数ではない
```

解品質および計算資源は、この運用波及経路へ含めず、別の評価系統として扱う。
