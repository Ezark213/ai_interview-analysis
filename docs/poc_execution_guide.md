# PoC実施ガイド（Iteration-05）

## 概要

このガイドは、AI面談動画解析システムのPoC（Proof of Concept）を実施する手順を説明します。

**対象**: プロジェクトオーナー、技術担当者
**前提**: Python 3.12以上、必要なライブラリがインストール済み
**作成日**: 2026-03-16
**バージョン**: 1.0

---

## 1. 事前準備

### 1.1 環境確認

```bash
# Pythonバージョン確認
python --version  # 3.12以上であることを確認

# 仮想環境の有効化（まだの場合）
cd ai_interview-analysis
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 依存関係のインストール
pip install -r requirements.txt
```

### 1.2 必要なファイルの確認

以下のファイルが準備されていることを確認:

- [ ] **動画ファイル**: `videos/` ディレクトリに5〜10名分
- [ ] **人間評価結果**: `human_evaluations.csv`
- [ ] **動画メタデータ（任意）**: `video_metadata.json`

---

## 2. ステップ1: 動画の準備

### 2.1 動画ファイルの配置

```bash
# プロジェクトルートで実行
mkdir -p videos

# 動画ファイルを配置
# videos/
#   ├── interview_C001.mp4
#   ├── interview_C002.mp4
#   └── ...
```

### 2.2 動画の確認

```bash
# 動画ファイルのリストを確認
ls videos/*.mp4

# ファイルが正しく配置されていることを確認
```

---

## 3. ステップ2: 人間評価結果の準備

### 3.1 CSVファイルの作成

`human_evaluations.csv` を作成し、以下の形式で入力:

```csv
candidate_id,candidate_name,human_score,human_decision,actual_outcome,issue_type,notes
C001,候補者A,90,採用,成功,なし,プロジェクトで高い成果を上げている
C002,候補者B,85,採用,成功,なし,技術力・協調性共に優秀
C003,候補者C,40,見送り,該当なし,人間関係,面談時の態度に懸念あり
C004,候補者D,50,条件付採用,失敗,早期退職,3ヶ月で退職（ストレス耐性不足）
C005,候補者E,70,採用,成功,なし,標準的なパフォーマンス
```

**必須列**:
- `candidate_id`: 候補者ID（動画ファイル名と対応）
- `human_score`: 人間評価スコア（0-100）
- `human_decision`: 採用 / 見送り / 条件付採用
- `actual_outcome`: 成功 / 失敗 / 該当なし

### 3.2 CSVファイルの検証

```bash
# CSVファイルの内容を確認
head -5 human_evaluations.csv

# 列数が正しいことを確認（7列）
```

---

## 4. ステップ3: AI評価の実行

### 4.1 各動画を解析

```bash
# 候補者1の動画を解析
python src/analyzer.py videos/interview_C001.mp4 > ai_results/C001.json

# 候補者2の動画を解析
python src/analyzer.py videos/interview_C002.mp4 > ai_results/C002.json

# ...（全候補者分を実行）
```

**注意**:
- 1動画あたり数分〜10分程度かかります
- APIコストが発生します（Gemini API）
- エラーが発生した場合は、エラーメッセージを確認してください

### 4.2 AI評価結果の統合

各候補者のJSON結果を1つのファイルに統合:

```bash
# PowerShell（Windows）の場合
echo "[" > ai_results.json
Get-Content ai_results\C001.json >> ai_results.json
echo "," >> ai_results.json
Get-Content ai_results\C002.json >> ai_results.json
# ...（必要に応じて全候補者分を追加）
echo "]" >> ai_results.json

# または、Pythonスクリプトで統合
python scripts/merge_ai_results.py ai_results/ > ai_results.json
```

**または、手動で統合**:

`ai_results.json` を手動で作成:

```json
[
  {
    "candidate_id": "C001",
    "overall_risk_score": 85,
    ...
  },
  {
    "candidate_id": "C002",
    "overall_risk_score": 78,
    ...
  }
]
```

---

## 5. ステップ4: PoC分析の実行

### 5.1 サンプルデータでのドライラン（練習）

```bash
# サンプルデータで動作確認
python src/poc_analysis.py --sample --output poc_report_sample.md

# 出力ファイルを確認
ls poc_report_sample.md
ls poc_report_sample.json
```

### 5.2 実データでのPoC分析

```bash
# 実データで分析
python src/poc_analysis.py \
  --ai-results ai_results.json \
  --human-evals human_evaluations.csv \
  --output poc_report.md

# 出力ファイルを確認
ls poc_report.md
ls poc_report.json
```

### 5.3 結果の確認

コンソールに表示されるサマリーを確認:

```
[PoC Analysis] Results Summary
  Correlation (Pearson): 0.994
  False Positive Rate: 0.00%
  False Negative Rate: 33.33%
  Overall: PASS / NEEDS IMPROVEMENT
```

---

## 6. ステップ5: レポートの読み方

### 6.1 Markdownレポート

`poc_report.md` をテキストエディタまたはMarkdownビューアで開く:

```bash
# Markdownビューア（VS Codeなど）で開く
code poc_report.md
```

### 6.2 レポートの構成

1. **サマリー**: 対象候補者数、スコア平均
2. **相関係数**: AIと人間の評価の一致度
3. **混同行列**: TP, FP, TN, FNの内訳
4. **偽陽性率・偽陰性率**: 誤判定の割合
5. **ハルシネーション検証**: 警告の有無
6. **総合判定**: 合格 / 要改善
7. **推奨事項**: 改善の方向性

### 6.3 合格基準の確認

レポートの「6. 総合判定」セクションを確認:

| 項目 | 結果 | 閾値 | 判定 |
|---|---|---|---|
| 相関係数（Pearson） | 0.994 | ≥ 0.7 | ✅ |
| 偽陽性率 | 0.00% | < 20% | ✅ |
| 偽陰性率 | 33.33% | < 10% | ❌ |

**総合判定**: 全ての項目が ✅ の場合、PoC合格

---

## 7. 結果の解釈

### 7.1 PoC合格の場合

**次のアクション**:
1. Iteration-06へ進む（候補者同意書・運用マニュアル作成）
2. 実運用の準備を開始
3. 継続的な精度モニタリングの仕組みを構築

### 7.2 PoC不合格の場合

**原因の特定**:

#### 相関係数が低い（< 0.7）
- **原因**: AIの評価基準が人間と異なる
- **対策**:
  - プロンプトを改善（評価基準を明確化）
  - ナレッジベースを拡充
  - 評価カテゴリを見直し

#### 偽陽性率が高い（≥ 20%）
- **原因**: 問題ある候補者を見逃している
- **対策**:
  - リスクシグナルの検出基準を厳格化
  - ナレッジベースに問題行動のパターンを追加
  - スコアの閾値を引き上げる（例: 70 → 75）

#### 偽陰性率が高い（≥ 10%）
- **原因**: 優秀な候補者を誤って見送っている
- **対策**:
  - ポジティブシグナルの検出を強化
  - スコアの閾値を引き下げる（例: 70 → 65）
  - 確信度が低い場合の評価方法を見直し

#### ハルシネーション警告が多い
- **原因**: AIが根拠のない推測をしている
- **対策**:
  - プロンプトで出典明記を徹底
  - ナレッジベースの範囲を明確化
  - 観察事実のみを報告するよう強調

---

## 8. トラブルシューティング

### 8.1 動画解析でエラーが発生

**エラー**: `FileNotFoundError: Video file not found`

**対策**:
```bash
# ファイルパスを確認
ls videos/interview_C001.mp4

# 絶対パスで指定
python src/analyzer.py "C:\Users\yiwao\ai_interview-analysis\videos\interview_C001.mp4"
```

### 8.2 PoC分析でエラーが発生

**エラー**: `ModuleNotFoundError: No module named 'scipy'`

**対策**:
```bash
# 依存関係を再インストール
pip install -r requirements.txt

# または個別にインストール
pip install scipy scikit-learn pandas
```

### 8.3 JSON形式エラー

**エラー**: `JSONDecodeError: Expecting value`

**対策**:
```bash
# JSONの形式を確認
cat ai_results.json | python -m json.tool

# 手動で修正するか、再度AI評価を実行
```

### 8.4 CSV形式エラー

**エラー**: `KeyError: 'candidate_id'`

**対策**:
```bash
# CSVの列名を確認
head -1 human_evaluations.csv

# 必須列が含まれているか確認:
# candidate_id, human_score, human_decision, actual_outcome
```

---

## 9. ベストプラクティス

### 9.1 動画品質の確保

- 解像度: 720p以上
- 音質: ノイズが少ない、明瞭な音声
- カメラアングル: 候補者の表情・視線が確認できる
- 照明: 十分な明るさ

### 9.2 サンプルの選定

- バランス: 優秀・問題あり・判断困難を均等に
- 無作為抽出: 意図的な選定を避ける
- サンプルサイズ: 可能な限り10名に近づける

### 9.3 データ管理

- 個人情報保護: 候補者名を匿名化
- セキュリティ: 動画ファイルは厳重に管理
- バックアップ: データを定期的にバックアップ

---

## 10. チェックリスト

### 事前準備
- [ ] Python 3.12以上がインストール済み
- [ ] 仮想環境が有効化されている
- [ ] 依存関係がインストール済み
- [ ] APIキーが設定されている

### データ準備
- [ ] 動画ファイルが配置済み（5〜10名分）
- [ ] `human_evaluations.csv` が作成済み
- [ ] 動画品質が十分（画質・音質）

### AI評価
- [ ] 各動画をAI解析済み
- [ ] `ai_results.json` が作成済み
- [ ] ハルシネーション警告を確認済み

### PoC分析
- [ ] `python src/poc_analysis.py` が実行済み
- [ ] `poc_report.md` が生成済み
- [ ] 合格基準を確認済み

### 結果の確認
- [ ] 相関係数が ≥ 0.7
- [ ] 偽陽性率が < 20%
- [ ] 偽陰性率が < 10%
- [ ] ハルシネーション警告が 0件

---

## 11. 参考情報

### 関連ドキュメント

- [PoC実施計画](./poc_plan.md): PoC の目的・合格基準・評価指標
- [評価ガイドライン](./evaluation_guidelines.md): 確信度の定義・出典ルール

### コマンド一覧

```bash
# サンプルデータでPoC分析
python src/poc_analysis.py --sample --output poc_report_sample.md

# 実データでPoC分析
python src/poc_analysis.py \
  --ai-results ai_results.json \
  --human-evals human_evaluations.csv \
  --output poc_report.md

# 動画解析（個別）
python src/analyzer.py videos/interview_C001.mp4 > ai_results/C001.json

# テスト実行
pytest tests/test_poc_analysis.py -v
```

---

## 更新履歴

| 日付 | バージョン | 内容 |
|---|---|---|
| 2026-03-16 | 1.0 | 初版作成（Iteration-05） |
