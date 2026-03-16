# トラブルシューティングガイド

**作成日**: 2026-03-16  
**対象**: AI面談動画解析システム  
**目的**: よくあるエラーと対処法

---

## 目次

1. [環境セットアップ関連](#環境セットアップ関連)
2. [Streamlit起動関連](#streamlit起動関連)
3. [動画解析関連](#動画解析関連)
4. [API関連](#api関連)
5. [その他](#その他)

---

## 環境セットアップ関連

### エラー: `ModuleNotFoundError: No module named 'xxx'`

**原因**: 必須パッケージがインストールされていない

**対処法**:
```bash
pip install -r requirements.txt
```

個別にインストールする場合:
```bash
pip install google-genai streamlit scipy scikit-learn pandas pytest pytest-mock python-dotenv ffmpeg-python
```

### エラー: `pip install`がタイムアウトする

**原因**: ネットワークが遅い、PyPIサーバーへの接続が不安定

**対処法**:
```bash
# タイムアウト時間を延長
pip install -r requirements.txt --timeout 120

# または個別にインストール
pip install streamlit ffmpeg-python --timeout 120
```

### エラー: `GEMINI_API_KEY not found in .env`

**原因**: .envファイルが存在しない、またはAPIキーが設定されていない

**対処法**:
1. .envファイルを作成:
   ```bash
   cp .env.example .env
   ```

2. エディタで.envを開き、APIキーを設定:
   ```bash
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. APIキーの取得: https://aistudio.google.com/apikey

### エラー: `GEMINI_API_KEY too short`

**原因**: APIキーが正しく設定されていない、またはプレースホルダーのまま

**対処法**:
1. .envファイルを確認
2. `your_api_key_here`がそのまま残っていないか確認
3. 正しいAPIキーをGoogle AI Studioから取得して設定

---

## Streamlit起動関連

### エラー: `streamlit: command not found`

**原因**: streamlitがインストールされていない、またはPATHが通っていない

**対処法**:
```bash
# streamlitをインストール
pip install streamlit

# Pythonモジュールとして実行
python -m streamlit run src/app.py
```

### エラー: `Address already in use` (ポート8501が使用中)

**原因**: 既に別のStreamlitアプリがポート8501で動作している

**対処法**:
```bash
# 別のポートを指定
streamlit run src/app.py --server.port 8502
```

または、既存のStreamlitプロセスを停止:
```bash
# Windows
taskkill /F /IM streamlit.exe

# macOS/Linux
pkill -f streamlit
```

### エラー: Streamlitアプリがブラウザで開かない

**原因**: ブラウザが自動起動しない、またはネットワーク設定の問題

**対処法**:
1. ブラウザを手動で開き、http://localhost:8501 にアクセス
2. コンソールに表示されるURLを確認
3. ファイアウォール設定を確認

---

## 動画解析関連

### エラー: `Unsupported video format: .wmv`

**原因**: サポート外の動画フォーマット

**対処法**:
- サポートフォーマットに変換: `.mp4`, `.mov`, `.avi`, `.webm`
- ffmpegで変換:
  ```bash
  ffmpeg -i input.wmv -c:v libx264 -c:a aac output.mp4
  ```

### エラー: `Video file not found`

**原因**: 動画ファイルのパスが間違っている

**対処法**:
1. ファイルパスを確認（絶対パスを使用推奨）
2. ファイル名にスペースや特殊文字が含まれている場合は引用符で囲む
3. Windows環境では`\`または`/`を使用

### エラー: `UnicodeEncodeError` (日本語ファイル名)

**原因**: Windows環境でcp932エンコーディングの制限

**対処法**:
1. ファイル名を英数字に変更
2. またはスクリプト内でUTF-8エンコーディングを設定（既に対応済み）

### エラー: メモリ不足（大容量動画）

**原因**: 動画ファイルが大きすぎる

**対処法**:
1. 動画を圧縮:
   ```bash
   ffmpeg -i input.mp4 -vcodec h264 -acodec aac -b:v 1M output.mp4
   ```
2. チャンク時間を短く設定（デフォルト5分 → 3分等）
3. 並列ワーカー数を減らす（デフォルト4 → 2等）

---

## API関連

### エラー: `google.genai.errors.AuthenticationError`

**原因**: APIキーが無効、または権限がない

**対処法**:
1. APIキーを再確認: https://aistudio.google.com/apikey
2. 新しいAPIキーを生成して.envに設定
3. APIキーに適切な権限があるか確認

### エラー: `google.genai.errors.RateLimitError`

**原因**: APIリクエスト制限を超えた

**対処法**:
1. 無料枠の場合: 1日あたり250リクエストまで
2. 有料プランへのアップグレードを検討
3. リクエスト間隔を空ける（並列ワーカー数を減らす）
4. 時間をおいて再試行

### エラー: `ReadTimeoutError` (API呼び出しタイムアウト)

**原因**: ネットワークが遅い、またはAPIサーバーの応答が遅い

**対処法**:
1. ネットワーク接続を確認
2. 動画サイズを削減
3. タイムアウト設定を延長（コード修正が必要）

### エラー: `google.genai.errors.InvalidArgument`

**原因**: APIリクエストのパラメータが不正

**対処法**:
1. 動画フォーマットを確認（サポート形式: mp4, mov, avi, webm）
2. 動画サイズを確認（推奨: 500MB以下）
3. ログを確認してエラー詳細を特定

---

## その他

### エラー: `pytest: command not found`

**原因**: pytestがインストールされていない

**対処法**:
```bash
pip install pytest pytest-mock
```

### エラー: テストが失敗する

**原因**: 環境が正しくセットアップされていない、または.envが不正

**対処法**:
1. 環境セットアップテストを実行:
   ```bash
   pytest tests/test_environment_setup.py -v
   ```
2. 失敗したテストのエラーメッセージを確認
3. .envファイルの設定を再確認

### エラー: `'ChunkedVideoAnalyzer' object has no attribute 'xxx'`

**原因**: メソッド名が間違っている（旧バージョンのコード）

**対処法**:
- `analyze_video_chunks` → `analyze_chunks`
- `integrate_chunk_results` → `integrate_chunks`
- 最新のコードを確認

### 解析結果が全て0点になる

**原因**: 動画に音声がない、または動画が正しく処理されていない

**対処法**:
1. 動画に音声が含まれているか確認
2. 動画形式を確認（推奨: mp4）
3. 動画の長さを確認（短すぎると解析が不十分）
4. ログを確認してエラーがないか確認

---

## エスカレーション

上記の対処法で解決しない場合:

1. **ログ確認**: コンソール出力やエラートレースバックを確認
2. **Issue報告**: プロジェクトのGitHubリポジトリにIssueを作成
3. **サポート**: 開発チームに連絡

---

## 参考情報

- **セットアップガイド**: [localhost_setup_guide.md](./localhost_setup_guide.md)
- **運用マニュアル**: [operation_manual.md](./operation_manual.md)
- **Gemini API ドキュメント**: https://ai.google.dev/docs
- **Streamlit フォーラム**: https://discuss.streamlit.io/

---

**作成者**: Iteration-07 Execution Agent  
**更新日**: 2026-03-16
