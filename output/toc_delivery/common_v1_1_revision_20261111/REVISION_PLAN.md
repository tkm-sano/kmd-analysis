# A〜D共通条件 v1.1 改訂計画（実装前）

2026-11-11の追加ユーザー指示に基づき、帰着後準備時間だけを900秒から0秒へ変更する。積込1800秒/便、顧客先作業120秒/地点は研究上の固定仮定として維持する。作業時間の変動モデルを導入しない。

1. 初期status・既存ファイルhash・変更予定ファイルの原文を保存する。凍結需要、旧v1.0設定、過去output/、既存B/C/Dアルゴリズムは保全する。
2. `common_conditions_v1_1.json`を追加し、採択版・supersedes・研究仮定の由来を記録する。共通loaderの参照先とpinを更新し、旧入力の無言変換は行わない。
3. 共通検査器は設定を読む構造を維持し、ready2=return1+0、load_start2>=return1を検査する。既存D bridgeは設定値を引き継ぐためアルゴリズムは変更不要。
4. fixtureと独立集計/監査にある900秒の固定参照を解消する。帰着直後の積込可、1秒前の拒否、旧900秒ready申告の拒否、バース競合の継続、積込1800秒・作業120秒・20時制約の維持をテストする。
5. 条件・入出力・計画・データ監査文書を最新仕様へ更新する。旧検証報告の数値はv1.0履歴として保持し、v1.1結果・下界は別の節・新規出力へ記録する。
6. 共通およびToC/D関連回帰テストを実行する。独立監査を新ディレクトリへ保存し、全保全対象のhash/diffを照合する。

数式：積込end=start+1800、帰着=出発+Σceil(OD秒)+120×訪問数、ready2=return1、W=Σ(start−ready)/60。積込作業・顧客作業をWへ直接加算しない。勤務期限72000秒、その他の採択条件を維持する。

変更予定：common/config.py、common/validation.py（式の明示のみ）、tests/toc_common/*、scripts/audit_toc_common.py、docs/research/toc_delivery_common/COMMON_*.md。追加：configs/toc_delivery/common_conditions_v1_1.json、新規監査出力。既存の凍結需要・実験結果・アルゴリズム本体、README/.gitignoreの既存差分は変更しない。S1〜S3本実験、commit/pushは行わない。
