# AI面談動画解析システム 運用マニュアル

**バージョン**: 1.0
**作成日**: 2026年3月23日
**対象**: システム利用者、管理者

---

## 目次

1. [システム概要](#1-システム概要)
2. [事前準備](#2-事前準備)
3. [Streamlit Web UIの使い方](#3-streamlit-web-uiの使い方)
4. [CLIの使い方](#4-cliの使い方)
5. [結果の見方](#5-結果の見方)
6. [トラブルシューティング](#6-トラブルシューティング)
7. [ベストプラクティス](#7-ベストプラクティス)
8. [FAQ](#8-faq)

---

## 1. システム概要

### 1.1 目的

SES事業における面談時の行動心理学的リスクスクリーニングを、Gemini AIを活用して自動化します。
面談動画を解析し、客観的なリスク評価レポートを生成します。

### 1.2 主な機能

- 📹 **動画解析**: 面談動画（最大30分）の自動解析
- 🔄 **長時間動画対応**: 5分単位のチャンク分割で安定処理
- 📊 **構造化レポート**: JSON形式の評価結果（総合スコア、カテゴリ別評価）
- 🌐 **Web UI**: ブラウザで簡単操作（Streamlit）
- 💻 **CLI**: コマンドラインでの一括処理
- 🔑 **複数APIキー対応**: 自動フェイルオーバーでクォータ制限を回避

### 1.3 処理フロー

```
面談動画アップロード
    ↓
動画サイズ確認（50MB以上？）
    ↓
Yes → チャンク分割（5分単位）→ 各チャンクを解析 → 統合
No  → 直接解析
    ↓
結果表示（総合評価、時系列分析）
```

---

## 2. 事前準備

### 2.1 必要なソフトウェア

#### Python 3.12以上

```bash
# バージョン確認
python --version
```

#### ffmpeg（動画処理に必須）

```bash
# Windows (Chocolatey)
choco install ffmpeg

# Mac (Homebrew)
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# インストール確認
ffmpeg -version
```

### 2.2 環境構築

#### 1. リポジトリのクローン（初回のみ）

```bash
git clone https://github.com/Ezark213/ai_interview-analysis.git
cd ai_interview-analysis
```

#### 2. 仮想環境の作成（推奨）

```bash
# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

#### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

#### 4. APIキーの設定

`.env`ファイルを作成:

```bash
# APIキー1（必須）
GEMINI_API_KEY_1=your_first_api_key_here

# APIキー2（オプション - 自動フェイルオーバー用）
GEMINI_API_KEY_2=your_second_api_key_here
```

**APIキーの取得方法**:
1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. 「Get API key」をクリック
3. APIキーをコピーして`.env`に貼り付け

**複数APIキーの推奨理由**:
- 無料枠: 15 RPM（リクエスト/分）、150万トークン/日
- 長時間動画（30分）のチャンク解析では、複数リクエストが必要
- APIキー1でクォータ制限に達すると、自動的にAPIキー2に切り替わります

---

## 3. Streamlit Web UIの使い方

### 3.1 起動方法

```bash
cd ai_interview-analysis
streamlit run src/app.py
```

ブラウザで `http://localhost:8502` が自動的に開きます。

### 3.2 動画アップロード

1. **サイドバー**で複数APIキーの設定状況を確認
2. **メインエリア**にドラッグ&ドロップで動画をアップロード
   - 対応形式: mp4, mov, avi, mkv
   - 推奨: 30分以内、1GB以下
3. 「解析開始」ボタンをクリック

### 3.3 解析プロセス

#### 小さい動画（50MB未満）
- 直接解析（5-10分）

#### 大きい動画（50MB以上）
1. 動画の長さを自動取得
2. 5分単位でチャンク分割（物理的にmp4ファイルを分割）
3. 各チャンクを順次解析（進捗バー表示）
4. 結果を統合して総合評価を生成

**処理時間の目安**:
- 5分動画: 約5分
- 30分動画（6チャンク）: 約30-40分

### 3.4 結果の表示

#### 総合評価
- **総合スコア**: 0-100点（リスクが低いほど高得点）
- **リスクレベル**: 低/中/高
- **推奨事項**: AI の判断に基づく推奨

#### カテゴリ別評価
- コミュニケーション能力
- ストレス耐性
- 信頼性
- チームワーク

各カテゴリに観察事項と確信度を表示。

#### 時系列分析（チャンク解析のみ）
- チャンク別のスコア推移
- 時間経過による変化を確認

#### JSON出力
- 「JSONをダウンロード」ボタンで詳細データを保存

---

## 4. CLIの使い方

### 4.1 基本的な使い方

```bash
# 単一動画を解析
python src/analyzer.py sample_interview.mp4
```

### 4.2 オプション

```bash
# APIキーを引数で指定
python src/analyzer.py --api-key YOUR_API_KEY sample.mp4

# 使用するモデルを指定
python src/analyzer.py --model gemini-2.5-flash sample.mp4

# 出力先を指定
python src/analyzer.py sample.mp4 --output results/report.json
```

### 4.3 チャンク解析の実行（Python スクリプト）

```python
from src.video_chunker import VideoChunker, get_video_duration
from src.chunked_analyzer import ChunkedVideoAnalyzer
from src.chunk_integrator import ChunkIntegrator

# 動画の長さを取得
duration = get_video_duration("video.mp4")

# 動画を5分単位で分割
chunker = VideoChunker(chunk_duration_seconds=300)
chunks = chunker.create_chunks("video.mp4", duration, split_physically=True)

# チャンク単位で解析
analyzer = ChunkedVideoAnalyzer()
chunk_results = analyzer.analyze_chunks(chunks, parallel=False)

# 結果を統合
integrator = ChunkIntegrator()
final_result = integrator.integrate_chunks(chunk_results)

# クリーンアップ
chunker.cleanup()
```

---

## 5. 結果の見方

### 5.1 総合スコアの解釈

| スコア | リスクレベル | 解釈 |
|--------|-------------|------|
| 80-100 | 低 | 問題なし。技術面・人間性ともに良好 |
| 60-79 | 低-中 | 概ね問題なし。一部注意が必要 |
| 40-59 | 中 | 慎重に判断。追加面談を推奨 |
| 20-39 | 高 | リスクあり。詳細確認が必要 |
| 0-19 | 非常に高 | 重大なリスク。採用見送りを検討 |

### 5.2 カテゴリ別スコアの見方

#### コミュニケーション能力
- 非言語（アイコンタクト、表情、姿勢）
- 言語（明瞭さ、論理性、質問への回答）

#### ストレス耐性
- 難しい質問への反応
- プレッシャー下での振る舞い

#### 信頼性
- 一貫性のある回答
- 具体的なエピソード
- 誠実さ

#### チームワーク
- 協調性に関する発言
- 過去のチーム経験

### 5.3 Red Flags（警告サイン）

以下の項目が記載されている場合は要注意:
- 視線を避ける
- 回答に矛盾がある
- 過度に防衛的
- 他責的な発言が多い
- ストレスサインが頻繁

### 5.4 免責事項

**重要**: 本評価はAIによる参考情報です。
- 最終判断は必ず人間が行ってください
- 偽陽性（問題ない人を誤判定）の可能性があります
- AIの限界を理解した上で運用してください

---

## 6. トラブルシューティング

### 6.1 よくあるエラー

#### エラー: `ModuleNotFoundError: No module named 'google.genai'`

**原因**: 依存関係がインストールされていない

**解決方法**:
```bash
pip install -r requirements.txt
```

#### エラー: `ffmpeg: command not found`

**原因**: ffmpegがインストールされていない

**解決方法**: [2.1 必要なソフトウェア](#21-必要なソフトウェア) を参照

#### エラー: `API quota exceeded`

**原因**: APIの無料枠を使い切った

**解決方法**:
1. `.env`にAPIキー2を追加（自動フェイルオーバー）
2. 別のGoogleアカウントでAPIキーを取得
3. 翌日まで待つ（無料枠は1日ごとにリセット）

#### エラー: `Video file too large`

**原因**: 動画ファイルが大きすぎる

**解決方法**:
- 動画を圧縮（解像度を下げる、ビットレートを下げる）
- チャンク解析を使用（Streamlit UIで自動実行）

#### 警告: `Low confidence in evaluation`

**原因**: AIの確信度が低い

**対処法**:
- 追加面談を実施
- 人間の評価を重視
- 動画の品質を確認（画質、音質）

### 6.2 動画の品質チェック

解析精度を高めるために、以下を確認:
- ✅ 解像度: 720p以上推奨
- ✅ 音質: クリアに聞こえる
- ✅ 照明: 顔が明瞭に見える
- ✅ カメラ位置: 顔全体が映っている
- ✅ 背景: ノイズが少ない

---

## 7. ベストプラクティス

### 7.1 動画撮影のコツ

1. **カメラ設定**
   - 固定カメラで正面から撮影
   - 候補者の上半身が映るようにフレーミング
   - 照明は候補者の顔に当たるように

2. **音声録音**
   - できるだけ静かな環境
   - マイクを候補者に近づける
   - 音声レベルをチェック

3. **面談進行**
   - 候補者に事前に動画撮影を説明
   - リラックスできる雰囲気作り
   - 標準的な質問を含める

### 7.2 評価の活用方法

1. **第一次スクリーニング**
   - AIスコアが低い候補者は追加面談
   - 高スコアでも人間の最終判断が必須

2. **面接官の補助**
   - AIが検出したリスクシグナルを事前確認
   - 面談時に深掘りすべきポイントを把握

3. **継続的改善**
   - 評価結果とアサイン後の結果を記録
   - 四半期ごとに精度を検証

### 7.3 倫理的配慮

- 候補者の同意を得る
- 動画の保管期間を明確にする
- 個人情報保護に配慮
- AIの限界を理解した運用

---

## 8. FAQ

### Q1: 動画の長さに制限はありますか？

A: 推奨は30分以内です。それ以上の動画も処理可能ですが、処理時間とコストが増加します。

### Q2: どの形式の動画に対応していますか？

A: mp4, mov, avi, mkv などの一般的な形式に対応しています。

### Q3: 月に何件まで解析できますか？

A: 無料枠の場合、月間約50件（30分動画）が目安です。詳細は [コスト分析ドキュメント](./cost-analysis.md) を参照。

### Q4: AIの評価はどれくらい正確ですか？

A: 現在精度検証中です。人間の評価との相関係数70%以上を目標としています。

### Q5: オフラインで使えますか？

A: いいえ、Gemini APIへのインターネット接続が必要です。

### Q6: 複数の候補者を一度に解析できますか？

A: CLIを使えば、スクリプトで複数動画を順次処理できます。並列処理は現在非対応です。

### Q7: 結果をExcelに出力できますか？

A: JSON形式で出力されるので、Excelにインポートするか、Pythonスクリプトで変換できます。

### Q8: APIキーは有料ですか？

A: Gemini APIには無料枠があります（15 RPM、150万トークン/日）。詳細は [Google AI Studio](https://aistudio.google.com/app/apikey) を参照。

---

## サポート

### 問い合わせ先

- プロジェクトオーナー: 岩男様
- GitHub Issues: https://github.com/Ezark213/ai_interview-analysis/issues

### リソース

- [プロジェクト概要](./project-overview.md)
- [技術仕様](./technical-spec.md)
- [コスト分析](./cost-analysis.md)
- [倫理・コンプライアンス](./ethics-compliance.md)

---

**最終更新**: 2026年3月23日
**バージョン**: 1.0
