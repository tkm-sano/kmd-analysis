# <データセット名>：取得・検証記録

## 記録状態

- 記録日：`<YYYY-MM-DD>`
- 実施者：`<氏名または役割>`
- 状態：`<planned | raw_acquired | validated | processed | blocked>`
- 出典台帳ID：`<source_id>`
- 関連する実装計画：`05_src/traffic_simulation/implementation_plan.md`

## 配布元と利用条件

- 配布者：`<provider>`
- データセット：`<名称と版>`
- 配布ページ：`<URL>`
- APIまたはダウンロード先：`<URLまたは該当なし>`
- ライセンス・利用規約：`<名称とURL>`
- アクセス要件：`<不要、アカウント、APIキーの環境変数名、手動承認など>`
- 再配布制限：`<概要>`

パスワード、トークン、APIキー、Cookie、その他の秘密値は記録しない。記録するのは、環境変数名または認証情報の管理方法だけとする。

## 選択条件

- 取得日時・タイムゾーン：`<timestamp>`
- 観測期間：`<開始・終了>`
- 地理的範囲：`<地域、境界、BBOX>`
- データ選択条件：`<問い合わせパラメータ、版、表、レイヤー、車種など>`
- 選択理由：`<研究上の用途>`
- 既知の対象範囲不足：`<limitations>`

## 保存先と命名

- 配布時のファイル名：`<upstream filename>`
- 不変の生データ保存先：`03_data/raw/traffic_simulation/<source>/<filename>`
- SHA-256：`<digest>`
- 出典台帳：`03_data/metadata/traffic_simulation_sources.csv`
- 加工スクリプト：`05_src/traffic_simulation/<area>/<script>.py`
- 加工後の出力：`<リポジトリ相対パス>`

生データは改変せず保存し、Gitには登録しない。

## 事前環境確認

正本実行環境であるHayateのリポジトリルートで実行する。

```bash
source /opt/miniconda/etc/profile.d/conda.sh
conda activate /home/takuma/kmd-analysis/.conda
bash reproducibility/scripts/hayate/verify_hayate_native_environment.sh
```

Dockerは利用可能な環境での任意の追加クロスチェックであり、取得処理の必須条件ではない。

```bash
docker compose config --quiet
```

追加ツールがある場合は、確認したバージョンを記録する。

```text
<tool>: <version>
```

## 取得手順

再実行可能な正確なコマンドを記録する。認証情報には変数または `.env` を使用し、秘密値を貼り付けない。

```bash
<command>
```

期待される結果：

```text
<HTTP状態、ファイルサイズ、フィーチャ数、アーカイブ内容など>
```

## 生データの検証

```bash
shasum -a 256 03_data/raw/traffic_simulation/<source>/<filename>
<構造検証コマンド>
```

実際の結果：

```text
SHA-256: <digest>
行数・フィーチャ数: <count>
対象期間: <value>
地理的範囲: <value>
```

## 加工手順

```bash
<processing command>
```

推定値や補完値を観測値のように扱わない。欠損、重複、不正な地物、品質フラグをどのように処理したかを記述する。

## 検証手順と結果

```bash
<test and validation commands>
```

```text
テスト: <result>
入力件数: <count>
出力件数: <count>
有効件数: <count>
無効件数: <count>
異常: <summary>
```

## ルール決定、実行、分析の整理

### ルールとして決定したこと

| 対象 | 決定したルール | 判断理由 |
|---|---|---|
| `<scope>` | `<rule>` | `<reason>` |

### 実行したこと

1. `<環境確認、取得、加工、検証、台帳更新、可視化等を実行順に記録する>`

### 実施した分析と未実施の分析

- 実施：`<構造、品質、記述統計等>`
- 未実施：`<交通分析、較正、最適化等>`

取得・加工の検査結果を、交通現象やモデル性能の分析結果として扱わない。

## 恣意性とその統制

| 判断箇所 | 恣意性の有無 | 統制・解釈 |
|---|---|---|
| `<choice>` | `<研究判断・機械的・表示上等>` | `<固定方法、版管理、解釈上の制限>` |

観測値、原典属性、推定値、仮定値、表示上の選択を区別する。変更が結果へ影響する条件は既存値を上書きせず、設定版または実験IDを更新する。

## コード上・運用上の問題点

- `<外部依存、失敗時の状態、性能、検証不足、CIで扱わない事項等>`
- `<問題が解決済みなら、症状、原因、修正、データへの影響も失敗表へ記録する>`

## 失敗と修正

| 日付 | 症状 | 原因 | 修正 | データへの影響 |
|---|---|---|---|---|
| `<date>` | `<error>` | `<cause>` | `<action>` | `<none or description>` |

## 来歴とGitの確認

```bash
git check-ignore -v 03_data/raw/traffic_simulation/<source>/<filename>
git status --short
git diff --check
```

- 生データがGit除外対象：`<はい・いいえ>`
- 生成物がGit除外対象：`<はい・いいえ>`
- 出典台帳を更新済み：`<はい・いいえ>`
- 取得記録がGit管理対象：`<はい・いいえ>`
- 加工コードとテストがGit管理対象：`<はい・いいえ>`

## 解釈上の限界と次の作業

- `<データが実際に測定しているもの>`
- `<データが測定していないもの>`
- `<較正・検証利用時の制約>`
- `<次の取得、対応付け、確認作業>`
