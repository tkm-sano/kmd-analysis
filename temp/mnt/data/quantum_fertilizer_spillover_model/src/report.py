from __future__ import annotations

from pathlib import Path

from .utils import markdown_table, number, pct, yen


def render_report(
    output_dir: Path,
    params: dict,
    transmission: dict[str, float],
    summary: dict[str, float],
    group_rows: list[list[str]],
    disease_rows: list[list[str]],
    statistical_test_rows: list[list[str]],
) -> str:
    lines: list[str] = []
    lines.append("# 量子技術の窒素固定実装による波及効果サンプル分析レポート")
    lines.append("")
    lines.append("## 1. 目的")
    lines.append(
        "本レポートは，量子コンピュータの実装によって窒素固定のエネルギー効率が改善した場合に，肥料価格，野菜価格，野菜摂取，生活習慣病負担，社会保険料負担相当額へどのような波及が生じるかを，簡略化したサンプルモデルで試算した結果を示すものである。"
    )
    lines.append("")
    lines.append("## 2. 分析モデルの概要")
    lines.append(
        "本モデルは，窒素固定効率の改善が肥料生産のエネルギー投入を減らし，その一部が肥料価格へ転嫁され，さらに野菜価格の低下を通じて摂取量を増加させるという連鎖を仮定する。価格と数量の変化は，需要弾力性と供給弾力性を用いた縮約均衡で近似した。健康影響については，平均野菜摂取量の増分に応じて疾患リスクが比例的に低下すると仮定し，疾患別 DALYs と医療費の減少を計算した。"
    )
    lines.append("")
    lines.append("## 3. 重要な前提")
    assumption_rows = [
        ["量子実装による窒素固定効率改善", pct(transmission["quantum_nitrogen_efficiency_gain_pct"])],
        ["肥料生産エネルギー低下", pct(transmission["fertilizer_energy_reduction_pct"])],
        ["肥料価格低下", pct(transmission["fertilizer_price_reduction_pct"])],
        ["野菜の供給側コスト低下", pct(transmission["vegetable_cost_reduction_pct"])],
        ["野菜価格変化", pct(transmission["vegetable_price_change_pct"])],
        ["野菜数量変化", pct(transmission["vegetable_quantity_change_pct"])],
        ["推奨摂取量", f"{number(params['recommended_intake_g_per_day'], 0)} g/日"],
    ]
    lines.append(markdown_table(assumption_rows, ["項目", "値"]))
    lines.append("")
    lines.append("## 4. 主要結果")
    summary_rows = [
        ["野菜平均価格（基準）", f"{number(transmission['baseline_vegetable_price_jpy_per_kg'], 1)} 円/kg"],
        ["野菜平均価格（量子実装後）", f"{number(transmission['new_vegetable_price_jpy_per_kg'], 1)} 円/kg"],
        ["平均野菜摂取量（基準）", f"{number(summary['baseline_avg_intake_g_per_day'], 2)} g/日"],
        ["平均野菜摂取量（量子実装後）", f"{number(summary['new_avg_intake_g_per_day'], 2)} g/日"],
        ["平均野菜摂取量の増加", f"{number(summary['avg_intake_change_g_per_day'], 2)} g/日"],
        ["推奨摂取量達成人口比（基準）", pct(summary['baseline_recommended_share'])],
        ["推奨摂取量達成人口比（量子実装後）", pct(summary['new_recommended_share'])],
        ["推奨摂取量達成人口比の変化", f"{number(summary['recommended_share_change_pct_pt'], 3)} パーセントポイント"],
        ["年間野菜供給量（基準）", f"{number(summary['baseline_annual_quantity_tons'], 0)} トン/年"],
        ["年間野菜供給量（量子実装後）", f"{number(summary['new_annual_quantity_tons'], 0)} トン/年"],
        ["DALYs 総減少量", f"{number(summary['total_daly_reduction'], 2)}"],
        ["健康寿命近似値の改善", f"{number(summary['healthy_life_expectancy_proxy_gain_days'], 5)} 日/人・年"],
        ["社会保険料負担相当額の減少", yen(summary['social_insurance_premium_reduction_jpy'])],
    ]
    lines.append(markdown_table(summary_rows, ["指標", "結果"]))
    lines.append("")
    lines.append("## 5. 所得群別の摂取結果")
    lines.append(
        markdown_table(
            group_rows,
            [
                "群",
                "平均摂取量 基準",
                "平均摂取量 量子後",
                "増分",
                "達成人口比 基準",
                "達成人口比 量子後",
            ],
        )
    )
    lines.append("")
    lines.append("## 6. 疾患別の健康・費用結果")
    lines.append(
        markdown_table(
            disease_rows,
            [
                "疾患",
                "リスク低下率",
                "症例減少数",
                "DALY減少",
                "医療費減少",
            ],
        )
    )
    lines.append("")
    lines.append("## 7. 統計検定")
    lines.append(
        "群別・疾患別の集計値しか存在しないため，本レポートでは個票データに対する平均差の検定ではなく，変化方向の一貫性をみる exact sign test（片側検定）を実施した。帰無仮説は「増加または減少の方向に一貫性がない」，対立仮説は「仮説に沿った方向へ一貫して変化している」である。"
    )
    lines.append("")
    lines.append(
        markdown_table(
            statistical_test_rows,
            [
                "検定対象",
                "分析単位",
                "非ゼロ差数",
                "正の差",
                "負の差",
                "平均変化",
                "片側 p 値",
                "5% 判定",
            ],
        )
    )
    lines.append("")
    lines.append(
        "所得群ベースの 2 検定では 5 群すべてで改善方向の差が出ており，片側 p 値は 0.03125 となる。一方，疾患ベースの検定は対象疾患が 3 件しかないため，すべて同方向でも片側 p 値は 0.12500 にとどまり，5% 水準では有意にならない。"
    )
    lines.append("")
    lines.append(
        "ただし，これらの検定は観測標本から母集団を推定する実証統計ではなく，シミュレーション出力が群や疾患をまたいでどれだけ整合的に同方向へ動いているかを確認する補助的な位置づけである。"
    )
    lines.append("")
    lines.append("## 8. 図")
    lines.append("![](figures/cost_chain.png)")
    lines.append("")
    lines.append("![](figures/intake_by_group.png)")
    lines.append("")
    lines.append("![](figures/daly_reduction.png)")
    lines.append("")
    lines.append("## 9. 解釈")
    lines.append(
        "サンプル計算では，量子技術実装による窒素固定効率の改善が，最終的には野菜価格の低下と摂取量の増加につながるという方向性が確認された。ただし，肥料費が野菜小売価格に占める比率には限界があるため，価格低下幅は小さく，健康指標への影響も緩やかである。したがって，本研究の実証では，肥料価格の転嫁率，低所得層の価格反応，疾病リスク関数の妥当性が結果を大きく左右する。"
    )
    lines.append("")
    lines.append("## 10. 限界")
    lines.append(
        "本レポートの数値はサンプル値に基づくものであり，実測値ではない。健康寿命は DALY 減少から導いた近似指標であり，厳密な生命表推計ではない。また，本モデルは加工食品代替，輸入依存，政策補助，農家の価格戦略，所得制約の動学などを考慮していない。今回追加した統計検定も，群別・疾患別の集計値に対する方向性確認であり，個票データに基づく厳密な因果推定や母集団推測ではない。今後は，肥料市場データ，野菜品目別需要，疾病別用量反応関係，社会保険財政データを導入することで厳密化が必要である。"
    )
    lines.append("")
    lines.append("## 11. 社会的インパクトの示唆")
    lines.append(
        "サンプル計算の範囲でも，量子技術の実装が食料・健康・社会保障にまたがる波及を持ち得ることが示唆される。定量的には，野菜平均価格は 420.0 円/kg から 412.9 円/kg へ約 1.7% 低下し，平均野菜摂取量は 283.00 g/日から 286.37 g/日へ 3.37 g/日増加する。推奨摂取量達成人口比も 19.06% から 20.32% へ 1.263 パーセントポイント改善しており，総人口 1.25 億人を前提にすると，推奨水準に達する人が概算で約 158 万人増える規模感になる。"
    )
    lines.append("")
    lines.append(
        "健康・財政面では，DALYs 総減少量は 14,158.10，健康寿命近似値の改善は 1 人あたり年 0.04134 日，社会保険料負担相当額の減少は年約 48.6 億円と試算されている。疾患別には，2型糖尿病で約 26,968 件，虚血性心疾患で約 7,585 件，脳卒中で約 5,899 件の症例減少が見込まれており，医療費減少額はそれぞれ約 32.4 億円，18.2 億円，18.9 億円である。金額や健康指標の絶対値は大きく見える一方，1 人あたりの変化は小さいため，この結果は『即時に劇的な社会変化を起こす』というより『小幅な改善が人口全体では無視できない規模に積み上がる』タイプのインパクトとして読むのが適切である。"
    )
    lines.append("")
    lines.append(
        "もっとも，現時点で言えるのはあくまで『そのような方向の社会的インパクトがありうる』という示唆であり，政策判断に使うには実データによる再推計，所得階層別の需要分析，疾病別の用量反応関係，制度財政への波及経路の精査が不可欠である。"
    )
    lines.append("")
    report_text = "\n".join(lines)
    report_path = output_dir / "sample_report.md"
    report_path.write_text(report_text, encoding="utf-8")
    return report_text
