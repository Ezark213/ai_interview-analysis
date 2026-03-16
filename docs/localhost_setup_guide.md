# ローカルホスト環境セットアップガイド

**作成日**: 2026-03-16  
**対象**: AI面談動画解析システム Iteration-07  
**目的**: ローカル環境でのシステムセットアップと起動手順

---

## 前提条件

以下がインストールされていることを確認してください：

- **Python 3.9以上** (推奨: 3.12以上)
- **pip** (最新版)
- **Gemini APIキー** ([Google AI Studio](https://aistudio.google.com/apikey)で取得)

---

## セットアップ手順

### 1. 依存関係のインストール

プロジェクトルートで以下を実行：

```bash
pip install -r requirements.txt
```

**インストールされるパッケージ**:
- google-genai (Gemini API SDK)
- streamlit (UI)
- scipy, scikit-learn, pandas (PoC分析用)
- pytest, pytest-mock (テスト用)
- python-dotenv (環境変数管理)
- ffmpeg-python (動画処理)

**トラブルシューティング**:
- タイムアウトエラーが発生した場合: `pip install -r requirements.txt --timeout 120`
- 個別インストール: `pip install streamlit ffmpeg-python --timeout 120`

### 2. .envファイルの作成

.env.exampleをコピーして.envを作成：

```bash
cp .env.example .env
```

エディタで`.env`を開き、GeminiAPIキーを設定：

```bash
# Gemini API Configuration
GEMINI_API_KEY=your_actual_api_key_here

# Optional: Cache settings
CACHE_DIR=.cache
CACHE_TTL_HOURS=24

# Optional: Video processing settings
MAX_CHUNK_DURATION_MINUTES=5
MAX_WORKERS=4
```

**APIキーの取得方法**:
1. [Google AI Studio](https://aistudio.google.com/apikey)にアクセス
2. 「Create API Key」をクリック
3. 生成されたキーをコピーして`.env`に貼り付け

### 3. 環境セットアップの検証

環境が正しくセットアップされているか確認：

```bash
pytest tests/test_environment_setup.py -v
```

**期待される出力**:
```
tests/test_environment_setup.py::test_required_packages_installed PASSED
tests/test_environment_setup.py::test_env_file_exists PASSED
tests/test_environment_setup.py::test_gemini_api_key_in_env PASSED
tests/test_environment_setup.py::test_api_key_format PASSED
tests/test_environment_setup.py::test_ffmpeg_available PASSED
tests/test_environment_setup.py::test_project_structure PASSED
tests/test_environment_setup.py::test_streamlit_app_exists PASSED

============================== 7 passed ==============================
```

---

## Streamlitアプリの起動

### 起動方法

プロジェクトルートで以下を実行：

```bash
cd src
streamlit run app.py
```

または、プロジェクトルートから：

```bash
streamlit run src/app.py
```

### 起動確認

ブラウザが自動的に開き、以下のURLにアクセスします：

**Local URL**: http://localhost:8501

ブラウザが自動で開かない場合は、手動でURLを開いてください。

### ポート変更（オプション）

ポート8501が使用中の場合、別のポートを指定：

```bash
streamlit run src/app.py --server.port 8502
```

---

## 動作確認手順

### 1. Streamlit UIでの確認

1. ブラウザでhttp://localhost:8501にアクセス
2. 以下のコンポーネントが表示されることを確認：
   - タイトル: 「AI面談動画解析システム」
   - サイドバー: 設定オプション（APIキー、モデル選択等）
   - メインエリア: 動画アップロード欄
   - ボタン: 「解析開始」

### 2. 動画アップロードと解析

1. 「Browse files」または動画ファイルをドラッグ&ドロップ
2. 対応フォーマット: `.mp4`, `.mov`, `.avi`, `.webm`
3. 「解析開始」ボタンをクリック
4. 進捗バーが表示され、解析が開始される
5. 解析完了後、結果が表示される：
   - 総合評価スコア
   - 各評価項目のスコア（コミュニケーション、ストレス耐性等）
   - リスクシグナル
   - ポジティブシグナル
   - 推奨事項

### 3. 実動画でのテスト（CLI）

コマンドラインから直接テストすることも可能：

```bash
python test_real_video.py
```

**注意**: `test_real_video.py`内の動画パスを実際のファイルパスに変更してください。

---

## アプリの停止

Streamlitアプリを停止するには：

- **Windows**: コマンドプロンプト/PowerShellで `Ctrl + C`
- **macOS/Linux**: ターミナルで `Ctrl + C`

---

## 次のステップ

セットアップが完了したら：

1. **実動画での動作確認**: 実際の面談動画をアップロードして動作を確認
2. **結果の検証**: ハルシネーション警告が0件であることを確認
3. **トラブルシューティング**: エラーが発生した場合は[troubleshooting.md](./troubleshooting.md)を参照

---

## 参考情報

- **プロジェクト計画**: [revised-plan-v2.md](./revised-plan-v2.md)
- **運用マニュアル**: [operation_manual.md](./operation_manual.md)
- **Gemini API ドキュメント**: https://ai.google.dev/
- **Streamlit ドキュメント**: https://docs.streamlit.io/

---

**作成者**: Iteration-07 Execution Agent  
**レビュー**: 未実施
