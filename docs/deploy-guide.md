# Streamlit Community Cloud デプロイガイド

## 前提条件
- GitHubアカウント（リポジトリ: `Ezark213/ai_interview-analysis`）
- Gemini APIキー（1〜2個）

## デプロイ手順

### 1. GitHubリポジトリの準備

以下のファイルがリポジトリに含まれていることを確認:

```
ai_interview-analysis/
├── src/app.py                  # メインアプリケーション
├── requirements.txt            # Python依存関係
├── packages.txt                # システムパッケージ（ffmpeg）
└── .streamlit/config.toml      # Streamlit設定
```

**重要**: `.streamlit/secrets.toml`は`.gitignore`に含まれているため、GitHubにはプッシュされません。

### 2. Streamlit Community Cloudにデプロイ

1. https://share.streamlit.io/ にアクセスし、GitHubアカウントでログイン
2. 「New app」をクリック
3. 以下を設定:
   - **Repository**: `Ezark213/ai_interview-analysis`
   - **Branch**: `main`
   - **Main file path**: `src/app.py`
4. 「Advanced settings」を展開

### 3. Secrets設定（APIキー）

「Advanced settings」内の「Secrets」欄に以下を入力:

```toml
GEMINI_API_KEY_1 = "あなたのAPIキー1"
GEMINI_API_KEY_2 = "あなたのAPIキー2"
OPENAI_API_KEY = "あなたのOpenAI APIキー"
```

- APIキー2はオプション（自動フェイルオーバー用）
- APIキーは[Google AI Studio](https://aistudio.google.com/app/apikey)で取得
- OPENAI_API_KEYはオプション（Whisper文字起こし機能用、$0.006/分）
- OpenAI APIキーは[OpenAI Platform](https://platform.openai.com/api-keys)で取得

### 4. デプロイ実行

「Deploy!」をクリックしてデプロイを開始。

初回デプロイは数分かかります（`packages.txt`のffmpegインストールを含むため）。

### 5. 動作確認

デプロイ完了後、公開URLで以下を確認:
- [ ] アプリがロードされる
- [ ] サイドバーに「APIキーが設定されています」と表示される
- [ ] 動画をアップロードできる
- [ ] 解析が正常に完了し、結果が表示される

## Secrets更新方法（デプロイ後）

1. https://share.streamlit.io/ でアプリを選択
2. 右上の「...」メニュー → 「Settings」
3. 「Secrets」タブでAPIキーを更新
4. 「Save」をクリック（アプリが自動で再起動）

## トラブルシューティング

### ffmpegが見つからない
`packages.txt`がリポジトリルートに存在するか確認。内容は`ffmpeg`のみ。

### APIキーエラー
Streamlit Cloudの「Settings」→「Secrets」でキーが正しく設定されているか確認。

### ファイルアップロードエラー
Streamlit Cloudの無料枠ではアップロード上限が200MB。動画サイズを確認。

### メモリ不足エラー
長時間動画（60分超）の場合、Streamlit Cloudのメモリ制限に達する可能性あり。動画を短く分割して再試行。

## ローカル開発でのSecrets設定

ローカル環境では`.streamlit/secrets.toml`を使用:

```toml
GEMINI_API_KEY_1 = "あなたのAPIキー1"
GEMINI_API_KEY_2 = "あなたのAPIキー2"
OPENAI_API_KEY = "あなたのOpenAI APIキー"
```

このファイルは`.gitignore`に含まれているため、GitHubにはプッシュされません。
ただし、`.env`ファイルがある場合はそちらが優先されます。
