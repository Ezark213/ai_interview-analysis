# AI面談動画解析システム

## プロジェクト概要

SES事業における面談時の行動心理学的リスクスクリーニングを、Gemini AIを活用して自動化するシステムです。
面談動画と専門的なナレッジベース（心理学・行動心理学の専門書）を組み合わせ、人間では見抜けない潜在的なリスクを客観的に評価します。

## 背景と目的

### ビジネス課題
- SES事業において、アサイン後の要員トラブルや契約解除は信用低下とコスト増大に直結
- 面談時の人間による判断だけでは、行動心理学的なリスク要因を見落とす可能性
- 重大なトラブルを1件でも未然に防ぐことが、大幅なROI向上につながる

### 実現する価値
- 客観的なリスク評価による採用精度の向上
- 人間の判断を補完する「第二の目」としてのAI活用
- 低コストでの高精度スクリーニングの実現

## 技術スタック

- **AIモデル**: Gemini 2.5 Flash（最新世代・低コスト）
- **SDK**: google-genai（最新Python SDK）
- **開発言語**: Python 3.12+
- **解析対象**: 面談動画（30分/回）+ 行動心理学ナレッジベース
- **処理能力**: 動画ネイティブ入力対応（マルチモーダル）
- **出力**: 構造化されたJSON形式の評価レポート

## 想定規模

- **月間処理件数**: 50名
- **動画時間**: 1回あたり30分（月間1,500分）
- **ナレッジベース**: 心理学専門書（約10万トークン/書籍）
- **出力レポート**: 1,000トークン/名（約1,000〜1,500文字）

## コスト試算

**月額ランニングコスト: 約11,000円**

詳細は [コスト分析ドキュメント](./docs/cost-analysis.md) を参照

## プロジェクト構成

```
ai_interview-analysis/
├── README.md                          # 本ファイル
├── requirements.txt                   # Python依存関係
├── .env.example                       # 環境変数テンプレート
├── docs/                              # ドキュメント
│   ├── revised-plan-v2.md            # 改善計画v2（最新）
│   ├── project-overview.md           # プロジェクト詳細
│   ├── technical-spec.md             # 技術仕様
│   ├── cost-analysis.md              # コスト試算
│   ├── ethics-compliance.md          # 倫理・コンプライアンス
│   └── system-architecture.md        # システム構成
├── src/                               # ソースコード
│   ├── analyzer.py                   # 動画解析CLIエントリーポイント
│   ├── knowledge_loader.py           # ナレッジベース読み込み
│   ├── prompt_builder.py             # プロンプト構築
│   ├── response_parser.py            # レスポンス解析
│   └── prompts/
│       └── system.txt                # システムプロンプトテンプレート
├── knowledge-base/                    # 評価基準ナレッジ
│   └── core-criteria.md              # 行動心理学の評価基準
└── tests/                             # テストコード（pytest）
    ├── conftest.py                   # 共通フィクスチャ
    ├── fixtures/                     # テストデータ
    │   ├── mock_gemini_response.json
    │   └── test_knowledge.md
    ├── test_analyzer.py              # アナライザーテスト
    ├── test_knowledge_loader.py      # ナレッジローダーテスト
    ├── test_prompt_builder.py        # プロンプトビルダーテスト
    └── test_response_parser.py       # レスポンスパーサーテスト
```

## セットアップ手順

### 1. 環境準備

```bash
# Python 3.12以上がインストールされていることを確認
python --version

# プロジェクトディレクトリに移動
cd ai_interview-analysis
```

### 2. 仮想環境の作成（推奨）

```bash
# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

```bash
# .env.exampleをコピーして.envを作成
cp .env.example .env

# .envファイルを編集してAPIキーを設定
# GEMINI_API_KEY=your_api_key_here
```

Gemini APIキーの取得方法:
1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. 「Get API key」をクリック
3. APIキーをコピーして`.env`に貼り付け

## 使い方

### 基本的な使用方法

```bash
# 動画ファイルを解析
python src/analyzer.py <動画ファイルのパス>

# 例
python src/analyzer.py sample_interview.mp4
```

### チャンク化機能（長時間動画対応）

**Iteration-03で追加**: 30分を超える長時間動画を5分単位に分割して解析する機能

```python
# Pythonスクリプトでチャンク化を使用
from src.video_chunker import VideoChunker
from src.chunked_analyzer import ChunkedVideoAnalyzer

# 動画をチャンク化（5分単位）
chunker = VideoChunker(chunk_duration_seconds=300)
chunks = chunker.create_chunks("video.mp4", video_duration_seconds=1800)  # 30分動画

# チャンク単位で解析
analyzer = ChunkedVideoAnalyzer(api_key="YOUR_API_KEY")
results = analyzer.analyze_chunks(chunks)

# 各チャンクの評価結果を確認
for result in results:
    print(f"Chunk {result['chunk_id']}: Score {result['overall_risk_score']}")
    print(f"Time range: {result['chunk_time_range']['start']}s - {result['chunk_time_range']['end']}s")
```

**注意**:
- 現時点では動画全体をアップロードして解析（時間範囲指定は将来実装予定）
- 動画の長さ（duration）は別途取得が必要（moviepy, ffmpeg-python等を使用）

### オプション

```bash
# APIキーを引数で指定
python src/analyzer.py --api-key YOUR_API_KEY sample.mp4

# 使用するモデルを指定
python src/analyzer.py --model gemini-2.5-flash sample.mp4
```

### 出力例

```json
{
  "overall_risk_score": 65,
  "risk_level": "低",
  "evaluation": {
    "communication": {
      "score": 75,
      "observations": ["適切なアイコンタクト", "明瞭な発話"],
      "confidence": "高"
    },
    "stress_tolerance": {
      "score": 60,
      "observations": ["難しい質問で若干の動揺"],
      "confidence": "中"
    },
    "reliability": {
      "score": 70,
      "observations": ["具体的なエピソードを交えて説明"],
      "confidence": "高"
    },
    "teamwork": {
      "score": 65,
      "observations": ["チーム経験について前向きに語る"],
      "confidence": "中"
    }
  },
  "red_flags": [],
  "positive_signals": ["技術的な質問に具体的に回答"],
  "recommendation": "技術力に問題なし。チーム経験の追加確認を推奨。",
  "disclaimer": "本評価はAIによる参考情報です。最終判断は人間が行ってください。"
}
```

## テスト実行方法

### 全テストを実行

```bash
pytest tests/ -v
```

### 特定のテストファイルのみ実行

```bash
# ナレッジローダーのテスト
pytest tests/test_knowledge_loader.py -v

# アナライザーのテスト
pytest tests/test_analyzer.py -v
```

### カバレッジレポート（オプション）

```bash
# カバレッジ測定
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html

# レポートをブラウザで開く
# htmlcov/index.html
```

## 開発状況

### ✅ Milestone 1: MVP（動く最小構成）- 完了
- [x] Python開発環境のセットアップ
- [x] Gemini 2.5 Flash API統合
- [x] 簡易ナレッジベース（行動心理学の評価基準）
- [x] 動画解析CLIスクリプト
- [x] プロンプト設計（バイアス防止・構造化出力）
- [x] 環境変数管理（.env / .env.example）
- [x] テストコード（モック使用、22テスト全てPASS）

### ✅ Milestone 2: 実用版（精度・使い勝手の向上）- 完了
- [x] 動画チャンク化機能の基本実装（Iteration-03）
  - [x] VideoChunker: 動画を時間軸で分割（5分単位）
  - [x] ChunkedVideoAnalyzer: チャンク単位での解析機能
  - [x] テストコード（12テスト全てPASS）
- [x] 並列解析の最適化（Phase 1完了）
  - [x] ThreadPoolExecutorによる並列処理実装
  - [x] 処理時間を最大1/6に短縮
- [x] コンテキストキャッシュの実装（Phase 1完了）
  - [x] CacheManager: ナレッジベースの明示的キャッシュ
  - [x] 90%コスト削減（月額1,260円 → 約130円）
- [x] 統合レイヤー（チャンク結果 → 総合評価）（Phase 1完了）
  - [x] ChunkIntegrator: チャンク結果の統合
  - [x] 一貫性チェック、時系列パターン抽出
- [x] Streamlit UI（動画アップロード + 結果表示）（Phase 1完了）
  - [x] チャンク解析オプションの追加
  - [x] 時系列分析の表示
  - [x] 進捗バー表示
- [x] 動画長取得機能（Phase 1完了）
  - [x] ffmpeg-pythonによる自動取得
  - [x] エラーハンドリングと推定値フォールバック
- [ ] 実動画テスト（google-genai SDK実証）（次回）

### 次のステップ

### Milestone 3: 運用準備（精度検証・コンプライアンス）
- [ ] 精度検証（同一動画5回解析で一貫性チェック）
- [ ] 人間の評価との比較テスト
- [ ] 候補者同意書テンプレート
- [ ] 運用マニュアル
- [ ] Whisper API統合（オプション: 文字起こし精度向上）

## 重要な留意事項

### 倫理・コンプライアンス
- **候補者の同意**: 動画解析とプロファイリングについて事前同意が必須
- **AIの限界**: 判定結果は参考情報であり、最終決定は必ず人間が行う
- **バイアスとハルシネーション**: 偽陽性（誤判定）のリスクを理解した運用が必要

詳細は [倫理・コンプライアンスドキュメント](./docs/ethics-compliance.md) を参照

---

## 今後の課題（運用化に向けて）

### 📊 精度向上のための課題

システムの基本機能は完成しましたが、実運用に向けて以下の課題に取り組む必要があります。

#### 1. PoC実施による精度検証（最優先）

**現状の問題**:
- 実動画テストは1件のみ（95点評価）
- 人間の評価との相関が未検証
- 偽陽性率・偽陰性率が不明

**目標**:
- 過去の面談動画5～10名で検証
- 人間の評価との相関係数 > 0.7
- 偽陽性率 < 20%

**期限**: 2026年4月中旬まで

#### 2. ハルシネーション対策の強化（優先度: 高）

**現状の問題**:
- AIの評価がどのナレッジベースを参照したか不明確
- ハルシネーション検出ルールが未整備

**対策**:
- システムプロンプトに「出典明記」を追加
- レスポンスパーサーにバリデーション追加
- 確信度が低い評価の取り扱いルール策定

**期限**: 2026年4月初旬

#### 3. 継続的な改善のフィードバックループ構築（優先度: 中）

**現状の問題**:
- 評価結果のフィードバックを収集・分析する仕組みがない
- 運用後の精度低下を検知できない

**対策**:
- 評価結果と実際のアサイン結果を追跡する仕組み
- 3ヶ月ごとの精度再評価
- プロンプト・ナレッジベースの定期的な改善

**期限**: 運用開始後、継続的に実施

詳細は [今後の課題と対策](./docs/今後の課題と対策.md) を参照

---

## ライセンス

TBD

## コントリビューター

- プロジェクトオーナー: 岩男様
- 技術アドバイザー: [名前]

## 関連リソース

- [Gemini API公式ドキュメント](https://ai.google.dev/docs)
- [Vertex AI公式ドキュメント](https://cloud.google.com/vertex-ai/docs)
