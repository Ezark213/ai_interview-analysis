# UI配色テストのセットアップと実行手順

## 📋 前提条件

- Python 3.8以上
- Streamlitアプリが `http://localhost:8501` で起動していること

## 🔧 セットアップ

### 1. Playwrightのインストール

```bash
# Playwrightとpytest-playwrightをインストール
pip install playwright pytest-playwright

# Playwrightブラウザのインストール（初回のみ）
playwright install chromium
```

### 2. 依存関係の確認

```bash
# インストール済みパッケージの確認
pip list | grep playwright
# 期待される出力:
# playwright           1.40.0
# pytest-playwright    0.4.3
```

## 🧪 テスト実行

### 方法1: pytestコマンドで実行（推奨）

```bash
# 全テストを実行
pytest tests/test_ui_colors.py -v

# 特定のテストのみ実行
pytest tests/test_ui_colors.py::test_background_color_is_dark_navy -v

# カバレッジ付きで実行
pytest tests/test_ui_colors.py -v --cov=src --cov-report=html
```

### 方法2: Pythonスクリプトとして直接実行

```bash
# tests/test_ui_colors.py を直接実行
python tests/test_ui_colors.py
```

## 📊 テスト項目

### 1. test_background_color_is_dark_navy
- **検証内容**: 背景色が `#0F172A` (ダークネイビー) であること
- **期待値**: `rgb(15, 23, 42)`
- **失敗時の対処**: `.streamlit/config.toml` の `backgroundColor` を確認

### 2. test_text_color_is_white
- **検証内容**: テキスト色が `#FFFFFF` (白) であること
- **期待値**: `rgb(255, 255, 255)`
- **失敗時の対処**: `src/app.py` のカスタムCSSでテキスト色が上書きされているか確認

### 3. test_heading_color_is_white
- **検証内容**: 見出し (h1) 色が `#FFFFFF` (白) であること
- **期待値**: `rgb(255, 255, 255)`
- **失敗時の対処**: `src/app.py` のカスタムCSSで h1 タグの色が上書きされているか確認

### 4. test_button_background_color_is_dark_blue
- **検証内容**: ボタンの背景色が `#1E3A8A` (ダークブルー) であること
- **期待値**: `rgb(30, 58, 138)`
- **失敗時の対処**: `src/app.py` のカスタムCSSでボタンの背景色が設定されているか確認

### 5. test_contrast_ratio_meets_wcag_aaa
- **検証内容**: コントラスト比が WCAG AAA基準 (7:1以上) を満たすこと
- **期待値**: `15.8:1` (±0.5の誤差許容)
- **失敗時の対処**: 背景色とテキスト色の組み合わせを見直す

### 6. test_padding_top_is_minimal
- **検証内容**: 上部余白が最小限 (1rem = 16px以下) であること
- **期待値**: `≤ 16px`
- **失敗時の対処**: `src/app.py` のカスタムCSSで `.block-container` の `padding-top` を確認

## ✅ テスト成功の例

```bash
$ pytest tests/test_ui_colors.py -v

tests/test_ui_colors.py::test_background_color_is_dark_navy PASSED      [ 16%]
tests/test_ui_colors.py::test_text_color_is_white PASSED                [ 33%]
tests/test_ui_colors.py::test_heading_color_is_white PASSED             [ 50%]
tests/test_ui_colors.py::test_button_background_color_is_dark_blue PASSED [ 66%]
tests/test_ui_colors.py::test_contrast_ratio_meets_wcag_aaa PASSED      [ 83%]
tests/test_ui_colors.py::test_padding_top_is_minimal PASSED             [100%]

============================== 6 passed in 5.23s ==============================
```

## ❌ テスト失敗の例

```bash
$ pytest tests/test_ui_colors.py::test_background_color_is_dark_navy -v

FAILED tests/test_ui_colors.py::test_background_color_is_dark_navy - AssertionError: 背景色が期待値と一致しません。
期待値: rgb(15, 23, 42)
実際の値: rgb(248, 250, 252)
→ .streamlit/config.toml の backgroundColor を確認してください
```

## 🔍 トラブルシューティング

### 問題1: Streamlitが起動していない

**エラーメッセージ**:
```
playwright._impl._api_types.Error: net::ERR_CONNECTION_REFUSED at http://localhost:8501/
```

**対処方法**:
```bash
# Streamlitアプリを起動
streamlit run src/app.py
```

### 問題2: Playwrightブラウザがインストールされていない

**エラーメッセージ**:
```
playwright._impl._api_types.Error: Executable doesn't exist at ...
```

**対処方法**:
```bash
# Chromiumブラウザをインストール
playwright install chromium
```

### 問題3: テストがタイムアウトする

**原因**: Streamlitの初期化に時間がかかっている

**対処方法**: `test_ui_colors.py` の `wait_for_timeout(2000)` を増やす（例: 5000ms）

## 📝 CI/CDパイプラインへの統合

### GitHub Actions の例

```yaml
name: UI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright pytest-playwright
          playwright install chromium

      - name: Start Streamlit app
        run: |
          streamlit run src/app.py &
          sleep 10  # Streamlitの起動を待つ

      - name: Run UI tests
        run: |
          pytest tests/test_ui_colors.py -v

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

## 📚 参考資料

- [Playwright for Python Documentation](https://playwright.dev/python/)
- [pytest-playwright GitHub](https://github.com/microsoft/playwright-pytest)
- [WCAG 2.1 Contrast Requirements](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
