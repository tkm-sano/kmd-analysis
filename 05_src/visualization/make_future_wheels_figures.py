from __future__ import annotations

import math
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from matplotlib import rcParams


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs/use_case_scenario/future_wheels_node_scoring.csv"
FIGURES = ROOT / "figures" / "06_future_wheels"
OUT_NETWORK = FIGURES / "future_wheels_network.png"
OUT_BAR = FIGURES / "future_wheels_expected_impact_bar_chart.png"
OUT_NETWORK_JA = FIGURES / "future_wheels_network_ja.png"
OUT_BAR_JA = FIGURES / "future_wheels_expected_impact_bar_chart_ja.png"
OUT_TOP = ROOT / "outputs/use_case_scenario/future_wheels_expected_impact_ranked.csv"

rcParams["font.family"] = "Hiragino Sans"
rcParams["axes.unicode_minus"] = False

AXIS_COLORS = {
    "operational_complexity": "#2F6F73",
    "quantum_relevance": "#8E4B7A",
    "delay": "#B66A2C",
}

LAYER_STYLE = {
    "root": {"radius": 0, "size": 4700, "linewidth": 2.4},
    "first_order": {"radius": 1, "size": 3300, "linewidth": 1.8},
    "second_order": {"radius": 2, "size": 2800, "linewidth": 1.4},
    "outcome": {"radius": 2, "size": 2800, "linewidth": 1.4},
}

SHORT_LABELS = {
    "FW0": "Charging-aware EV\nlast-mile routing\nin Tokyo",
    "FW1": "Dense Tokyo demand\ncreates many customer\nnode candidates",
    "FW1A": "Customer nodes must be\nscenario-defined",
    "FW1B": "Quantum VRP evidence\nis mostly smaller than\nEVRP-scale instances",
    "FW2": "Charging stations\nand SOC become core\nrouting constraints",
    "FW2A": "Geocoded chargers help,\nbut coverage is imperfect",
    "FW2B": "Battery/SOC parameters\nremain scenario-defined",
    "FW2C": "Quantum evidence lacks\ndirect charging/SOC\ncoverage",
    "FW3": "Time windows and\nservice reliability\nshape feasibility",
    "FW3A": "Tokyo delivery windows\nneed explicit assumptions",
    "FW3B": "Charging and time-window\nconstraints are rarely\ncombined in quantum evidence",
    "FW4": "Traffic uncertainty\naffects travel-cost\nfeasibility",
    "FW4A": "Static traffic proxies\nsupport stress scenarios",
    "FW4B": "Dynamic dispatch is an\noptional extension",
    "FW5": "Fleet, capacity, and\ndepot choices must be\ncontrolled",
    "FW5A": "Do not infer fleet size\nfrom national EV stock",
    "FW5B": "Depot location needs\nsynthetic or facility data",
    "FW6": "Social requirement coverage\nand quantum validation\nmust be evaluated separately",
}

SHORT_LABELS_JA = {
    "FW0": "東京の充電考慮型\nEVラストマイル配送\n(root)",
    "FW1": "東京の高密度需要が\n多数の顧客ノード候補を\n生む",
    "FW1A": "顧客ノードは\nシナリオで明示する\n必要がある",
    "FW1B": "量子VRPの証拠は\nEVRP規模より小さい\n事例が多い",
    "FW2": "充電ステーションと\nSOCが中核制約になる",
    "FW2A": "充電器位置は使えるが\n網羅性には限界がある",
    "FW2B": "電池容量・SOCは\nシナリオ設定が必要",
    "FW2C": "量子側証拠では\n充電/SOCの直接対応が\nまだ弱い",
    "FW3": "時間窓とサービス信頼性が\n実行可能性を左右する",
    "FW3A": "東京の配送時間窓は\n明示的な仮定が必要",
    "FW3B": "充電制約と時間窓を\n同時に扱う量子証拠は\nまだ少ない",
    "FW4": "交通不確実性が\n移動コストと実行可能性に\n影響する",
    "FW4A": "静的交通データは\nストレス条件のproxyに\n使える",
    "FW4B": "動的dispatchは\n初期分析では拡張扱い",
    "FW5": "車両数・容量・デポは\nシナリオで制御する",
    "FW5A": "全国EV stockから\n配送車両数を推定しない",
    "FW5B": "デポ位置は合成設定か\n物流施設データが必要",
    "FW6": "社会側要件の充足と\n量子側検証の成熟度は\n別軸で評価する",
}

FULL_LABELS_JA = {
    "FW1": "東京の高密度需要が多数の顧客ノード候補を生む",
    "FW1A": "顧客ノード集合は明示的に定義する必要がある",
    "FW1B": "既存の量子VRP証拠はEVRP規模の顧客集合より小さい事例が多い",
    "FW2": "充電ステーションとSOC実行可能性が中核的な経路制約になる",
    "FW2A": "充電ステーションは位置情報化できるが網羅性には限界がある",
    "FW2B": "電池容量とSOCパラメータはシナリオで定義する必要がある",
    "FW2C": "既存の量子VRP証拠では充電ステーション/SOCの直接対応がまだ弱い",
    "FW3": "時間窓とサービス信頼性が経路の実行可能性を左右する",
    "FW3A": "東京の配送時間窓は明示的なシナリオ仮定が必要である",
    "FW3B": "EV充電制約と時間窓を同時に扱う量子側証拠はまだ少ない",
    "FW4": "交通と移動コストの不確実性が経路実行可能性に影響する",
    "FW4A": "静的交通proxyは移動コストのストレス条件に使える",
    "FW4B": "動的dispatchは初期分析の中心ではなく拡張扱いである",
    "FW5": "車両数・積載容量・デポ選択はシナリオで制御する必要がある",
    "FW5A": "車両数は全国EV stockから推定すべきではない",
    "FW5B": "デポ位置は合成配置または物流施設データが必要である",
    "FW6": "社会側要件の充足と量子側検証の成熟度は別軸で評価すべきである",
}

BAR_LABELS_EN = {
    "FW1": "Demand scale: Tokyo density requires explicit customer-node scenarios",
    "FW1A": "Customer definition: public data are proxies, not observed delivery stops",
    "FW1B": "Problem-size gap: quantum VRP cases are mostly smaller than EVRP benchmarks",
    "FW2": "Charging/SOC constraints: EV routes depend on charging feasibility and battery state",
    "FW2A": "Charging data limit: geocoded chargers are useful but incomplete",
    "FW2B": "Battery assumption: battery capacity and SOC must be scenario-defined",
    "FW2C": "Quantum constraint gap: charging-station and SOC coverage is not yet direct",
    "FW3": "Service timing: time windows and reliability shape route feasibility",
    "FW3A": "Time-window assumption: Tokyo delivery windows require explicit scenario design",
    "FW3B": "Combined-constraint gap: charging and time windows are rarely evaluated together",
    "FW4": "Traffic uncertainty: congestion affects travel-cost and route feasibility",
    "FW4A": "Traffic proxy use: static traffic data can define stress scenarios",
    "FW4B": "Dynamic dispatch scope: realtime dispatch is an extension, not the first target",
    "FW5": "Fleet/depot design: vehicles, capacity, and depot choices must be controlled",
    "FW5A": "Fleet-size caution: national EV stock should not be converted into route vehicles",
    "FW5B": "Depot data gap: depot locations need synthetic placement or facility data",
    "FW6": "Evaluation principle: social requirements and quantum validation are separate axes",
}

BAR_LABELS_JA = {
    "FW1": "需要規模: 東京の高密度需要は顧客ノードの明示設定を必要にする",
    "FW1A": "顧客定義: 公開データはproxyであり実配送stopではない",
    "FW1B": "問題規模ギャップ: 量子VRP事例はEVRP benchmarkより小さいものが多い",
    "FW2": "充電/SOC制約: EV配送では充電可否と電池状態が中核制約になる",
    "FW2A": "充電データの限界: 充電器位置は使えるが網羅性に限界がある",
    "FW2B": "電池仮定: 電池容量とSOCはシナリオで明示する必要がある",
    "FW2C": "量子側制約ギャップ: 充電ステーション/SOCの直接対応がまだ弱い",
    "FW3": "サービス時間制約: 時間窓と信頼性が経路実行可能性を左右する",
    "FW3A": "時間窓の仮定: 東京の配送時間窓はシナリオ設計が必要である",
    "FW3B": "複合制約ギャップ: 充電制約と時間窓を同時に扱う評価が少ない",
    "FW4": "交通不確実性: 混雑が移動コストと経路実行可能性に影響する",
    "FW4A": "交通proxy利用: 静的交通データはストレス条件の設定に使える",
    "FW4B": "動的dispatch範囲: リアルタイムdispatchは初期分析では拡張扱い",
    "FW5": "車両/デポ設計: 車両数・容量・デポ選択は制御変数である",
    "FW5A": "車両数の注意: 全国EV stockを配送車両数へ変換しない",
    "FW5B": "デポデータ不足: デポ位置は合成配置か施設データが必要である",
    "FW6": "評価原則: 社会側要件と量子側検証は別軸で評価する",
}


def wrap_label(label: str, width: int = 38) -> str:
    return "\n".join(textwrap.wrap(label, width=width, break_long_words=False))


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT)
    df["parent_node_id"] = df["parent_node_id"].fillna("")
    df["impact_axis"] = df["impact_axis"].fillna("root")
    return df


def assign_positions(df: pd.DataFrame) -> dict[str, tuple[float, float]]:
    positions: dict[str, tuple[float, float]] = {"FW0": (0.0, 0.0)}
    first_order = ["FW1", "FW2", "FW3", "FW4", "FW5", "FW6"]
    first_angles = {
        "FW1": 135,
        "FW2": 70,
        "FW3": 5,
        "FW4": -55,
        "FW5": -125,
        "FW6": 180,
    }
    children_by_parent = {
        parent: df[df["parent_node_id"].eq(parent)]["node_id"].tolist()
        for parent in first_order
    }
    for node_id in first_order:
        angle = math.radians(first_angles[node_id])
        radius = 3.25 if node_id != "FW6" else 3.05
        positions[node_id] = (radius * math.cos(angle), radius * math.sin(angle))
        children = [child for child in children_by_parent[node_id] if child not in first_order]
        if not children:
            continue
        if len(children) == 1:
            offsets = [0]
        elif len(children) == 2:
            offsets = [-13, 13]
        elif node_id == "FW2":
            offsets = [-35, 0, 35]
        else:
            offsets = [-18, 0, 18]
        for child, offset in zip(children, offsets):
            child_angle = math.radians(first_angles[node_id] + offset)
            child_radius = 5.35 if node_id == "FW2" else (5.95 if node_id != "FW6" else 5.45)
            positions[child] = (child_radius * math.cos(child_angle), child_radius * math.sin(child_angle))
    return positions


def draw_future_wheels_network(df: pd.DataFrame, language: str = "en") -> None:
    is_ja = language == "ja"
    out_path = OUT_NETWORK_JA if is_ja else OUT_NETWORK
    positions = assign_positions(df)
    fig, ax = plt.subplots(figsize=(18, 12), dpi=220)
    ax.set_facecolor("#F8F7F3")
    fig.patch.set_facecolor("#F8F7F3")
    ax.axis("off")

    by_id = df.set_index("node_id")
    for row in df[df["parent_node_id"].ne("")].to_dict("records"):
        parent = row["parent_node_id"]
        child = row["node_id"]
        if parent not in positions or child not in positions:
            continue
        x1, y1 = positions[parent]
        x2, y2 = positions[child]
        color = AXIS_COLORS.get(row["impact_axis"], "#777777")
        probability = row["conditional_probability"]
        width = 1.0 + 2.0 * float(probability)
        arrow = FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=width,
            color=color,
            alpha=0.58,
            shrinkA=28,
            shrinkB=30,
            connectionstyle="arc3,rad=0.05",
        )
        ax.add_patch(arrow)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(
            mx,
            my,
            f"p={probability:.1f}",
            ha="center",
            va="center",
            fontsize=8.5,
            color="#3F3F3F",
            bbox=dict(boxstyle="round,pad=0.18", fc="#F8F7F3", ec="none", alpha=0.9),
        )

    for row in df.to_dict("records"):
        node_id = row["node_id"]
        x, y = positions[node_id]
        layer = row["node_layer"]
        axis = row["impact_axis"]
        color = "#2E2E2E" if layer == "root" else AXIS_COLORS.get(axis, "#777777")
        face = "#FFFFFF" if layer != "root" else "#F1EFE6"
        edge = color
        size = LAYER_STYLE[layer]["size"]
        lw = LAYER_STYLE[layer]["linewidth"]
        ax.scatter(
            [x],
            [y],
            s=size,
            c=face,
            edgecolors=edge,
            linewidths=lw,
            zorder=3,
        )
        label = (SHORT_LABELS_JA if is_ja else SHORT_LABELS).get(node_id, wrap_label(row["node_label"], 25))
        if layer == "root":
            if not is_ja:
                label = label + "\n(root)"
        else:
            label = label + f"\nEI={row['expected_impact']:.2f}"
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=8.8 if layer != "root" else 10,
            color="#222222",
            linespacing=1.12,
            zorder=4,
        )

    ax.text(
        -6.6,
        6.35,
        "Future Wheels: 東京の充電考慮型EVラストマイル配送" if is_ja else "Future Wheels: Charging-aware EV last-mile routing in Tokyo",
        fontsize=19,
        fontweight="bold",
        color="#202020",
        ha="left",
    )
    ax.text(
        -6.6,
        5.95,
        "線幅とpは枝採用の妥当性スコア由来の条件付き確率を示す。ノード値は期待インパクト（EI = 累積確率 x impact value）。"
        if is_ja
        else "Line width and p labels show rule-based conditional probability. Node value shows expected impact (EI = cumulative probability x impact value).",
        fontsize=10.5,
        color="#555555",
        ha="left",
    )

    legend_items = [
        Line2D([0], [0], color=AXIS_COLORS["operational_complexity"], lw=4, label="運用複雑性" if is_ja else "Operational complexity"),
        Line2D([0], [0], color=AXIS_COLORS["quantum_relevance"], lw=4, label="量子側との関係" if is_ja else "Quantum relevance"),
        Line2D([0], [0], color=AXIS_COLORS["delay"], lw=4, label="遅延・信頼性" if is_ja else "Delay / reliability"),
    ]
    ax.legend(
        handles=legend_items,
        loc="lower left",
        bbox_to_anchor=(0.02, 0.02),
        frameon=False,
        fontsize=10,
    )
    ax.set_xlim(-7.0, 7.0)
    ax.set_ylim(-6.2, 6.9)
    plt.tight_layout(pad=0.5)
    fig.savefig(out_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def draw_expected_impact_bar_chart(df: pd.DataFrame, language: str = "en") -> None:
    is_ja = language == "ja"
    out_path = OUT_BAR_JA if is_ja else OUT_BAR
    scored = df[df["node_layer"].ne("root")].copy()
    scored = scored.sort_values("expected_impact", ascending=True)
    if is_ja:
        scored["bar_label"] = scored.apply(
            lambda row: f"{row['node_id']}  {wrap_label(BAR_LABELS_JA[row['node_id']], 34)}", axis=1
        )
    else:
        scored["bar_label"] = scored.apply(
            lambda row: f"{row['node_id']}  {wrap_label(BAR_LABELS_EN[row['node_id']], 56)}", axis=1
        )
    scored["bar_label_explanatory_en"] = scored["node_id"].map(BAR_LABELS_EN)
    scored["bar_label_explanatory_ja"] = scored["node_id"].map(BAR_LABELS_JA)
    if not is_ja:
        scored.to_csv(OUT_TOP, index=False)

    fig, ax = plt.subplots(figsize=(13.5, 10.5), dpi=220)
    fig.patch.set_facecolor("#FBFAF7")
    ax.set_facecolor("#FBFAF7")
    colors = [AXIS_COLORS.get(axis, "#777777") for axis in scored["impact_axis"]]
    bars = ax.barh(scored["bar_label"], scored["expected_impact"], color=colors, height=0.72)
    fig.text(
        0.08,
        0.975,
        "Future Wheelsノード別の期待インパクト" if is_ja else "Expected Impact by Future Wheels Node",
        fontsize=17 if is_ja else 18,
        fontweight="bold",
        color="#202020",
        ha="left",
        va="top",
    )
    fig.text(
        0.08,
        0.928 if is_ja else 0.944,
        "期待インパクト = rootからの累積確率 x impact value。スコアはルールベースで根拠確認可能な値であり、観測された社会的確率ではない。"
        if is_ja
        else "Expected impact = cumulative probability from the root x impact value. Scores are rule-based and evidence-auditable, not observed social probabilities.",
        fontsize=10.5,
        color="#555555",
        ha="left",
        va="bottom",
    )
    ax.set_xlabel("期待インパクト" if is_ja else "Expected impact", fontsize=11)
    ax.set_ylabel("")
    ax.grid(axis="x", color="#D8D3CA", linewidth=0.8, alpha=0.9)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#AFA79C")
    ax.tick_params(axis="y", labelsize=8.5, length=0)
    ax.tick_params(axis="x", labelsize=10)
    ax.set_xlim(0, max(4.4, scored["expected_impact"].max() + 0.35))

    for bar, value in zip(bars, scored["expected_impact"]):
        ax.text(
            value + 0.05,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2f}",
            va="center",
            ha="left",
            fontsize=9,
            color="#333333",
        )

    legend_items = [
        Line2D([0], [0], color=AXIS_COLORS["operational_complexity"], lw=6, label="運用複雑性" if is_ja else "Operational complexity"),
        Line2D([0], [0], color=AXIS_COLORS["quantum_relevance"], lw=6, label="量子側との関係" if is_ja else "Quantum relevance"),
        Line2D([0], [0], color=AXIS_COLORS["delay"], lw=6, label="遅延・信頼性" if is_ja else "Delay / reliability"),
    ]
    ax.legend(handles=legend_items, loc="lower right", frameon=False, fontsize=10)
    plt.tight_layout(rect=(0, 0, 1, 0.875 if is_ja else 0.91))
    fig.savefig(out_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    df = load_data()
    draw_future_wheels_network(df, "en")
    draw_expected_impact_bar_chart(df, "en")
    draw_future_wheels_network(df, "ja")
    draw_expected_impact_bar_chart(df, "ja")
    print(OUT_NETWORK.relative_to(ROOT))
    print(OUT_BAR.relative_to(ROOT))
    print(OUT_NETWORK_JA.relative_to(ROOT))
    print(OUT_BAR_JA.relative_to(ROOT))
    print(OUT_TOP.relative_to(ROOT))


if __name__ == "__main__":
    main()
