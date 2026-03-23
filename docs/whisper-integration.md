# Whisper API統合ガイド

**作成日**: 2026年3月23日
**ステータス**: 実装完了（Milestone 3）

---

## 概要

OpenAI Whisper APIを使用して、動画から音声を抽出し、テキストに変換します。
文字起こしされたテキストを解析に含めることで、より精度の高い評価が可能になります。

---

## 目的

### なぜ文字起こしが必要か

1. **非言語情報の補完**: 動画だけでは、細かいニュアンスや言葉選びを見逃す可能性
2. **検索可能性**: テキスト化することで、特定のキーワードやフレーズを検索可能
3. **精度向上**: 発言内容を正確に把握することで、評価の信頼性向上

---

## セットアップ

### 1. OpenAI APIキーの取得

1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. アカウントを作成（またはログイン）
3. [API Keys](https://platform.openai.com/api-keys) ページで新しいAPIキーを作成
4. APIキーをコピー

### 2. 環境変数の設定

`.env`ファイルに以下を追加:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 依存関係のインストール

```bash
pip install openai>=1.12.0
```

または

```bash
pip install -r requirements.txt
```

---

## 使い方

### 方法1: CLIで文字起こし

```bash
# 動画から音声を抽出して文字起こし
python src/whisper_transcriber.py video.mp4

# 結果をJSONファイルに保存
python src/whisper_transcriber.py video.mp4 --output transcript.json

# 結果をテキストファイルに保存
python src/whisper_transcriber.py video.mp4 --output transcript.txt

# 言語を指定（デフォルト: ja）
python src/whisper_transcriber.py video.mp4 --language en
```

### 方法2: Pythonスクリプトで使用

```python
from src.whisper_transcriber import WhisperTranscriber

# 初期化
transcriber = WhisperTranscriber()

# 動画を文字起こし
result = transcriber.transcribe_video("video.mp4")

# 結果を表示
print(result["text"])

# セグメント情報（タイムスタンプ付き）
for seg in result["segments"]:
    print(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")

# 結果を保存
transcriber.save_transcript(result, "transcript.json")
```

---

## 出力形式

### JSON形式

```json
{
  "text": "こんにちは、私の名前は山田太郎です。本日はよろしくお願いします。",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "こんにちは、私の名前は山田太郎です。"
    },
    {
      "start": 2.5,
      "end": 5.0,
      "text": "本日はよろしくお願いします。"
    }
  ]
}
```

### テキスト形式

```
こんにちは、私の名前は山田太郎です。本日はよろしくお願いします。

--- セグメント情報 ---
[0.0s - 2.5s] こんにちは、私の名前は山田太郎です。
[2.5s - 5.0s] 本日はよろしくお願いします。
```

---

## コスト

### Whisper APIの料金

- **価格**: $0.006 / 分（約0.9円/分、1ドル=150円換算）
- **30分動画**: 約27円

### 月間コスト試算（50名処理）

- 50名 × 30分 × 0.9円/分 = **1,350円/月**

---

## 解析への統合（今後の拡張）

現在、文字起こし機能は独立したモジュールとして実装されています。
今後、以下のように解析システムに統合することができます：

### 統合案1: プロンプトに文字起こしを追加

```python
# analyzer.pyを拡張
from src.whisper_transcriber import WhisperTranscriber

transcriber = WhisperTranscriber()
transcript = transcriber.transcribe_video("video.mp4")

# Gemini APIに送信するプロンプトに文字起こしを追加
prompt = f"""
動画と文字起こしテキストを分析してください。

--- 文字起こし ---
{transcript['text']}

--- 評価基準 ---
{knowledge_base}
"""
```

### 統合案2: チャンク解析で時系列文字起こし

```python
# 各チャンクの文字起こしを取得
for i, chunk in enumerate(chunks):
    transcript = transcriber.transcribe_video(chunk["path"])
    chunk["transcript"] = transcript["text"]

    # Gemini APIで解析（動画 + 文字起こし）
    result = analyze_with_transcript(chunk["path"], chunk["transcript"])
```

---

## トラブルシューティング

### エラー: `openai.error.AuthenticationError`

**原因**: APIキーが無効または設定されていない

**解決方法**:
1. `.env`ファイルに`OPENAI_API_KEY`が設定されているか確認
2. APIキーが正しいか確認
3. OpenAI Platformで使用制限を確認

### エラー: `ffmpeg: command not found`

**原因**: ffmpegがインストールされていない

**解決方法**: [運用マニュアル](./operation-manual.md#21-必要なソフトウェア) を参照

### 文字起こしの精度が低い

**原因**: 音声品質が悪い

**対処法**:
- 動画の音声品質を確認
- ノイズが多い場合は、ノイズキャンセリングツールを使用
- マイクの位置を調整して再撮影

---

## ベストプラクティス

### 1. 音声品質の確保

- **クリアな音声**: ノイズを最小限に
- **適切な音量**: 小さすぎず、大きすぎず
- **エコーの回避**: 反響の少ない環境で録音

### 2. 言語の指定

- 日本語面談: `--language ja`
- 英語面談: `--language en`
- 自動検出も可能ですが、明示的な指定を推奨

### 3. コスト管理

- 文字起こしは必要な場合のみ実行
- 動画の長さを確認してからコストを見積もる

---

## 今後の改善案

1. **自動統合**: analyzer.pyで`--use-transcript`フラグを追加し、自動的に文字起こしを実行
2. **キャッシュ**: 同じ動画の文字起こし結果をキャッシュして再利用
3. **感情分析**: 文字起こしテキストから感情やトーンを分析
4. **キーワード抽出**: 重要なキーワードやフレーズを自動抽出

---

## まとめ

Whisper API統合により、動画解析の精度向上が期待できます。
文字起こしは独立したモジュールとして実装されているため、必要に応じて柔軟に活用できます。

---

**関連ドキュメント**:
- [運用マニュアル](./operation-manual.md)
- [技術仕様](./technical-spec.md)
- [コスト分析](./cost-analysis.md)
