# グループ受付 v2 の QAOA 局所サイズ予備

対象は n＝10・12・14。各規模で現在計画2箇所、可行な再割当後の計画2箇所を登録した。同じ親計画・便・中心から3サイズの区間を構成し、区間外の訪問順、受付時刻、車両と便を固定する。入口と出口はそれぞれの区間の直前・直後である。局所比較72 QAOA呼出しと、外側比較18方式実行・72枝を予定する。技術用の4同時呼出し／サイズは別記録とし、正式90ケースへの算入はゼロである。

技術検証は現行回路のp＝2、各学習1,000 shots、最終10,000 shots、最大24評価、始動1回、既存MPS精度基準を使用する。n＝14で最初の学習評価を保存してから再開し、学習・最終計数と全ての誤差証跡を照合する。64ビット範囲の測定値を仮定せず、登録IDと既存の用途別seedを照合する。技術FAILのサイズは後続を実行せず、その全予定IDに理由を残す。局所の厳密解はHeld–Karpと独立した逆向き漸化式で照合し、探索には渡さない。

初期値の承認は、初期値比較の完了および集計後に、研究者が明示したAまたはBと承認記録を登録する。旧正式登録の初期値Aおよび初期値比較の候補Bは、この新しい採用確認の代わりにならない。正式設定と正式登録を更新する処理は含まれない。

## hayate での操作

```bash
cd /home/takuma/kmd-analysis
py=/tmp/kmd-p1-pricing-20261118/bin/python
entry=$PWD/scripts/run_grouped_qaoa_size_pilot.py
out=$PWD/output/iterative_d3/qaoa_size_grouped_v2_20261124
"$py" -B "$entry" status --output "$out"
"$py" -B "$entry" preflight --output "$out"
```

研究者が採用したarmを承認記録とともに入力する。

```bash
read -r -p '研究者が承認したarm (A/B) ' approved_arm
read -r -p '承認記録の参照 ' approval_reference
"$py" -B "$entry" approve --output "$out" --arm "$approved_arm" --approval-ref "$approval_reference"
"$py" -B "$entry" launch --output "$out"
```

`launch` は標準入力を閉じ、新しいセッションで起動し、PID・起動時刻・実コマンド・ログパスを `LAUNCH.json` に保存する。hayateの既存協調リースを取得して計算する。リース使用中は `HOLD` を記録するため、既存実行の終了を確認後に同じ `launch` を使用する。前回の完了記録と入出力ハッシュ、途中のCOBYLA評価および外側枝チェックポイントを照合して未完了から再開する。破損が見つかれば当該ファイルを保全して停止する。

```bash
cat "$out/PROGRESS.json"
"$py" -B "$entry" status --output "$out"
"$py" -B "$entry" stop --output "$out"
```

`stop` は登録された生存中のcontrollerに停止要求を記録する。実行中の最大4件の組が終わった時点で停止し、次の組は投入しない。状態が `INTERRUPTED` になった後、同じ `launch` で再開する。強制中断時も共有リースは残存workerが終了するまで再取得できない。

正常終了は `RUN_COMPLETE.json` と `FINAL_VALIDATION.json`、省略・失敗・中断は `PROGRESS.json` と `logs/` の記録で確認する。局所結果と最終計画の表、図、採用提案は `FINAL_REPORT.md` から参照できる。既存の初期値比較がリースを使用中であれば、そちらを停止せず待つ。
