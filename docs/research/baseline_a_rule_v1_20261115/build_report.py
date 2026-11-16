"""Build human review tables from all registered attempts, including failure."""
from collections import defaultdict
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def save(name,value):
    with (HERE/name).open('x') as stream:
        if isinstance(value,str):
            stream.write(value)
        else:
            json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def clock(second):
    return f'{second//3600:02}:{second//60%60:02}:{second%60:02}'


def main():
    rows = json.loads((HERE/'ALL_ATTEMPTS.json').read_text())
    main_rows = [r for r in rows if 'checks01' in r['run_id']]
    auxiliary = []
    for row in rows:
        run = ROOT/row['output']/row['run_id']
        accepted = row['T_program'] is not None
        plan = json.loads((run/('plan.json' if accepted else 'rejected_plan.json')).read_text())
        events = json.loads((run/'events.json').read_text())
        raw = json.loads((run/'validation.json').read_text())['independent']
        vehicle_ids = list(dict.fromkeys(t['vehicle_id'] for t in plan['trips']))
        # Stored input order, not event traversal order, defines vehicle indices.
        config = json.loads((ROOT/row['output']/'REGISTRATION.json').read_text())['config']
        input_path = ROOT/config['inputs']['input_root']/row['scale']/'input.json'
        vehicles = json.loads(input_path.read_text())['vehicles']
        by_berth = defaultdict(list)
        for e in events:
            by_berth[e['berth_id']].append({'vehicle_id':e['vehicle_id'],'trip_no':e['trip_no'],
                'start_s':e['load_start_s'],'end_s':e['load_end_s']})
        auxiliary.append({'run_id':row['run_id'],'status':row['status'],
            'accepted_metrics':accepted,'active_vehicles':len(vehicle_ids),'nonempty_trips':len(events),
            'vehicles':[{'vehicle_index':i,'vehicle_id':v['vehicle_id'],
                'active':raw['final_return_s'][i] is not None,'first_ready_s':v['first_ready_s'],
                'final_return_s':raw['final_return_s'][i],'L_s':raw['L_s'][i],
                'O_s':max(0,raw['final_return_s'][i]-v['return_deadline_s']) if raw['final_return_s'][i] is not None else 0}
                for i,v in enumerate(vehicles)],
            'berth_utilization':{b:sorted(x,key=lambda e:e['start_s']) for b,x in sorted(by_berth.items())}})
    save('AUXILIARY_METRICS.json',auxiliary)
    table = ['|規模/再実行|D km|W 分|W_first 分|W_reload 分|T_program 秒|状態|',
             '|---|---:|---:|---:|---:|---:|---|']
    for r in main_rows:
        table.append(f"|{r['scale']}/r{r['repeat_id']}|{r['D']:.4f}|{r['W']:.4f}|{r['W_first']:.4f}|{r['W_reload']:.4f}|{r['T_program']:.6f}|{r['status']}|")
    returns = ['|規模|最終帰着|車両別Lの範囲 分|O 秒|走査/候補/採用|停止|',
               '|---|---|---:|---:|---|---|']
    for r in main_rows[:3]:
        s=r['search']
        returns.append(f"|{r['scale']}|{clock(max(r['final_return_s']))}|{min(r['L_s'])/60:.3f}〜{max(r['L_s'])/60:.3f}|{r['O_s']}|{s['scans']}/{s['candidate_evaluations']}/{s['accepted_moves']}|{s['stop_reason']}|")
    b2 = next(r for r in rows if r['scale']=='S2' and r['berths']==2)
    b4 = next(r for r in rows if r['scale']=='S2' and r['berths']==4)
    b8 = next(r for r in rows if r['scale']=='S2' and r['berths']==8)
    sensitivity = ['|S2バース|D km|W 分|W_first 分|W_reload 分|T_program 秒|T_attempt 秒|状態|',
                   '|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in [b2,b4,b8]:
        values=[f'{r[k]:.4f}' if r.get(k) is not None else 'null' for k in ['D','W','W_first','W_reload','T_program','T_attempt']]
        sensitivity.append('|'+str(r['berths'])+'|'+'|'.join(values)+'|'+r['status']+'|')
    failed=b2['diagnostic_rejected_only']
    save('FINAL_REPORT_JA.md',f'''# A_rule_v1 最終報告（2026-11-15）

## 1. 何を表す方式か

「A：業務構造を参考にした規則型代理ベースライン」である。公開資料で確認された区域別配送・帰所再積込を参考に、共通入力から担当範囲、訪問順、便構成、積込順を研究上の明示規則で決める。対象事業者の実配車アルゴリズムや観測一日の配送実績を再現した方式ではない。

## 2. 旧A2からの変更と保持

角度順・0度・同数分割、有向道路距離NN→容量60分割、最大2便、FCFS、共通運行条件と凍結Route入力を保持した。旧地点proxyによる先行負荷調整を、候補ごとの割当・NN・便構成・全体スケジュール再計算と(O,H)辞書式先着改善へ変更した。対応する円環境界の端点のみを移し、最大V回採用する。「割当・訪問順・便構成の反復的な共同決定」である。

旧A2・A-area-v3・Cook・B/C/D・共通コードは編集していない。旧判定や数値も保全した。新しいCLI/生成器/規則検証/派生入力アダプタ/設定2件/テストを別名で追加した。道路の旧Table文言は新版設定の参照関係で解消し、原本を変更しない。[監査](REPOSITORY_AUDIT.md)、[確定仕様](BASELINE_A_RULE_SPEC.md)、[仮定・変更台帳](ASSUMPTION_AND_CHANGE_LOG.md)を参照。

## 3. 実際に実行した検証

新規小規模テスト29件、旧A2を含む回帰全体158件が通過した。最終凍結コードでも新規29件を再確認した（同じテストの再実行を独立件数へ足さない）。手計算の非対称ODでD=7 km、W=0、arcごとceilと到着/帰着を厳密確認した。初便だけの総待機360/720/1440分も確認した。これは主設定の総Wを置き換える値ではない。

容量60/61/120/121、空車両/空便、不正な地点・拠点・便・接続・積込・バース重複・負待機・hash・不達、候補の状態保全、移動後の順序/分割/時刻、キャッシュなし再構築との一致、厳密(O,H)改善、移動上限、解なし/上限/入力不正を確認した。検証器は生成器の主計算関数を呼ばず、DecimalでODを再加算し別のイベント処理でFCFSを再構成する。

限定実行は主設定4件と感度2件、合計6試行を全て保存した。成功5件、勤務終了を満たす計画未発見1件である。事後の全出力hash・状態遷移・制約/指標照合等2622項目が通過した。これは棄却試行を成功と判定した意味ではない。保全対象218ファイルは全てハッシュ一致。詳細は[検証記録](VALIDATION_RECORD.md)、[全試行JSON](ALL_ATTEMPTS.json)、[事後監査](FINAL_AUDIT.json)。

## 4. S1〜S3の限定結果

{chr(10).join(table)}

{chr(10).join(returns)}

主設定は全車両が稼働し、非空便はS1=20、S2=40、S3=80。いずれも勤務終了制約を満たす。V回の移動はアルゴリズムの通常停止で、安全時間切れではない。局所最適・全体最適とは認定しない。全便イベント、車両別L/帰着/超過、バース別利用区間は[補助指標](AUXILIARY_METRICS.json)と各runのevents/plan/validationにある。

Tは入力/hashから独立再計算・一致確認までのwallである。各回のT_input/planning/validation、T_attempt、CPU/RSS、setup/export、環境、入力・設定・ソースhashを保存した。使用は4物理コア枠中1コア/native1thread、各試行は新規プロセスで逐次。OS cacheと共有ホストの無関係負荷は制御していない。Tを人手計画時間、正式T_A_ref、統計的性能差とは扱わない。

## 5. 再現性

S2の2回は入力・計画JSON bytes・D/W/W内訳が一致した。計画SHA256は `{b4['plan_sha256']}`。Tは{main_rows[1]['T_program']:.6f}秒と{main_rows[3]['T_program']:.6f}秒で、時間の一致を要求せずそのまま記録した。[REPRODUCIBILITY.json](REPRODUCIBILITY.json)に正本を保存した。同じ需要への計算再実行であり需要標本数を増やさない。S1⊂S2⊂S3も独立標本3件と数えない。

## 6. バース感度

{chr(10).join(sensitivity)}

全条件で同じS2需要・20台・同じ規則を用い、生成段階から実行した。4バースは主設定初回を参照する。2バースは最大V回で停止したが勤務終了超過が残り、採用D/W/T_program=nullである。棄却計画の診断値だけを別に示すとD={failed['D']:.4f} km、W={failed['W']:.4f}分（初便{failed['W_first']:.4f}、再積込{failed['W_reload']:.4f}）、最終帰着{clock(max(failed['final_return_s']))}、車両別L={min(failed['L_s'])/60:.3f}〜{max(failed['L_s'])/60:.3f}分、O合計{failed['O_s']}秒であった。これらは採用値ではない。問題自体が実行不能という結論は出さず、上限を延長しなかった。

4バースの最終帰着{clock(max(b4['final_return_s']))}、L={min(b4['L_s'])/60:.3f}〜{max(b4['L_s'])/60:.3f}分に対し、8バースは{clock(max(b8['final_return_s']))}、L={min(b8['L_s'])/60:.3f}〜{max(b8['L_s'])/60:.3f}分であった。8バースの待機減少とともに帰着・拘束も併記した。readyを希望時刻へ変えていない。割当への時刻フィードバックがあるためDも変わる。この各1回の記述結果から統計的優越性や一般的単調性は主張しない。

## 7. AとB/C/Dの比較可能性・残る不整合

需要・拠点・Route OD・容量・最大便数・勤務・作業・物理バース・D/W・独立制約検証は共有できる。Aにも負荷改善があるため「最適化なし」ではない。区域初期割当・端点候補・O/H・先着改善・最大V回という目的と探索範囲でB/C/Dと区別する。

現行B/C/Dの共通完成器はroute pool内のルート選択、車両/便所属、積込開始を最適化し、FCFS固定ではない。供給便の内部訪問順は完成器が書き換えない。したがって現行契約のW差には積込順/開始最適化も含まれる。共通FCFSに揃えた比較ではないことを明記する。旧DWT内Aも完成器を通る別経路なので、新Aをそこへ自動接続していない。

B/C/Dは通常4枝×1コア、Aは単一決定論的1プロセス。親入力から二重検証までをwallとするが、資源使用差と準備を併記する。旧単コア結果・旧Table結果・旧Tref60秒/A除外契約は今回の正式比較基準へ流用しない。正式T_A_ref、反復数、需要標本数、精度目標、J接続は別実験計画が必要である。今回B/C/Dの全面改修・本実験は行っていない。[実験契約](EXPERIMENT_CONTRACT.md)を参照。

## 8. Cookの実装済み/未実装範囲

訪問順生成interfaceと完全置換検査、割当変更後の再呼出位置、呼出回数/時間記録、後段の便/時刻接続は実装した。`orderer_wall_s`は順序アダプタと経路所要時間コンパイルを含む呼出側の包括時間である。Cookアダプタ・大田区の区域/履歴対応・複合方式の検証は未実装。NN以外へ黙って切り替えない。

既存著者commit dc4ebc0aa091d4d1eb7dc7d9b9b2d8f8c19664ceと設定・全結果を保全した。論文と競技コード、Amazon scoreと全順序適合、大田区実績への外挿を区別する。町丁目を実績区域と同等とせず、区域なしでも代表性を保証しない。車両割当/2便/再積込/バースは研究追加モデルである。[Cook接続計画](COOK_EXTENSION_PLAN.md)の事前条件を満たしてから別比較を行う。今回Cookを再実行していない。

## 9. 採否

|判定対象|判定|意味|
|---|---|---|
|実装・独立検証としての成立|PASS（検証した範囲）|小規模検算、主設定全件、S2再現が成立。2バース棄却も正しく記録|
|業務構造との対応の説明可能性|条件付きで成立|区域配送と再積込の構成を参考にできる。具体規則は研究仮定|
|対象実績への適合|未検証・資料未取得|適格な対象全体実績がない。不適合を観測した判定ではない|
|仮定付き計算ベースラインとして主比較に利用|限定付き採用|同一条件の計算方式間比較に使用可能。正式実験開始/比較パイプライン接続は別工程|

**仮定付き計算ベースラインとして利用可能。対象事業者の実績改善を示す比較には用いない。** 採用根拠は仕様・業務上の意味・共通制約・再現性・独立検証であり、NN/B/C/Dに勝ったことではない。旧FAIL記録は履歴として残す。RQと仮説の原文は変更しない。「配送実績を想定する」という原文から実績再現や実績改善を導くことはできず、計算上の代理基準という主張範囲を併記する。

## 10. 未取得・未検証と次の作業

対象ToCの実担当区域、実際の割当/順序決定、便頻度、積込ready/start/end、全車両D、同工程の人手計画T、妥当な適合許容幅は未取得である。対象実績を得られれば校正/独立検証を分離する。今回の実装PASSを実績適合PASSへ読み替えない。

実機のメモリ上限到達や外側300秒強制停止の負荷試験、他OSは未実行。小規模の上限/失敗状態と通常実行は確認したが、未実行の安全機構に実測PASSを付けない。正式比較ではFCFSか各方式の積込最適化かを研究目的に沿って確定し、A版/参照/入力hash/計時/資源契約を接続した上で、需要標本数と計算反復数・精度目標を別途決める。今回の6試行を正式統計反復へ転用しない。J、正式T_A_ref、人手時間はnullのまま。

再現コマンドは[REPRODUCE.md](REPRODUCE.md)、機械可読採否は[DECISION.json](DECISION.json)。commit/push、外部連絡、有料計算、需要/OD再生成、README/RQ/仮説の編集は行っていない。
''')
    save('DECISION.json',{'method':'A','method_version':'A_rule_v1-20261115',
        'implementation_independent_validation':'PASS_WITHIN_TESTED_SCOPE',
        'business_structure_explanation':'CONDITIONAL_RESEARCH_ASSUMPTIONS',
        'target_actual_fit':'NOT_EVALUATED_MISSING_ELIGIBLE_TARGET_DATA',
        'target_actual_mismatch_observed':False,'assumed_computational_main_baseline':'CONDITIONALLY_ACCEPTED',
        'permitted_claim':'performance and tradeoffs between computational methods under shared assumptions',
        'prohibited_claim':'improvement of the target operator actual performance or verified reproduction of its algorithm',
        'main_checks_validated':4,'all_registered_attempts':6,'all_validated':5,'no_feasible_plan_attempts':1,
        'statistical_experiment_started':False,'B_C_D_rewrite':False,'Cook_adapter_implemented':False,
        'J':None,'T_A_ref':None,'T_A_human_reference':None,'RQ_and_hypothesis_changed':False})


if __name__=='__main__':
    main()
