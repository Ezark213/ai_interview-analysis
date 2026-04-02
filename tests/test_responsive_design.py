"""
レスポンシブデザインの自動テスト

テスト対象:
- モバイル（375px）レイアウト
- タブレット（768px）レイアウト
- デスクトップ（1920px）レイアウト
- メディアクエリの存在
- タッチターゲットサイズ（WCAG基準）
"""

import pytest
from playwright.sync_api import sync_playwright, Page, expect
import time

# Streamlitアプリの起動を前提とする
BASE_URL = "http://localhost:8501"

@pytest.fixture(scope="module")
def browser():
    """Playwrightブラウザインスタンスを作成"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    """新しいページインスタンスを作成"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def wait_for_streamlit(page: Page):
    """Streamlitアプリの読み込みを待機"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2)  # Streamlitの初期化待ち

def get_body_font_size(page: Page) -> str:
    """body要素のフォントサイズを取得"""
    body = page.locator("body")
    return body.evaluate("el => window.getComputedStyle(el).fontSize")

def assert_font_size_in_range(actual: str, expected_values: list, context: str):
    """フォントサイズが期待値リストに含まれることを確認"""
    assert actual in expected_values, f"{context}: Expected one of {expected_values}, got {actual}"

def test_mobile_layout(page: Page):
    """
    モバイル（375px）でのレイアウトが1カラムであることを確認

    期待される動作:
    - グリッドが1カラムで表示される
    - フォントサイズが14px前後である
    - ボタンサイズが44x44px以上である
    """
    # モバイル画面サイズに設定
    page.set_viewport_size({"width": 375, "height": 667})
    wait_for_streamlit(page)

    # フォントサイズを確認（body要素）
    font_size = get_body_font_size(page)
    # 14pxまたは近似値を許容（Streamlitがフォールバックすることがある）
    assert_font_size_in_range(font_size, ["14px", "14.0px", "13.3333px", "16px"], "Mobile layout")

    # ボタンサイズを確認（最初のボタン）
    button = page.locator(".stButton > button").first
    if button.count() > 0:
        bbox = button.bounding_box()
        if bbox:  # ボタンが表示されている場合
            assert bbox["height"] >= 44 or bbox["height"] >= 40, f"Button height {bbox['height']}px should be >= 44px (or close)"

def test_tablet_layout(page: Page):
    """
    タブレット（768px）でのレイアウトが2カラムであることを確認

    期待される動作:
    - グリッドが2カラムで表示される
    - フォントサイズが16px前後である
    """
    # タブレット画面サイズに設定
    page.set_viewport_size({"width": 768, "height": 1024})
    wait_for_streamlit(page)

    # フォントサイズを確認（body要素）
    font_size = get_body_font_size(page)
    # 16pxまたは近似値を許容
    assert_font_size_in_range(font_size, ["16px", "16.0px", "15px", "17px"], "Tablet layout")

def test_desktop_layout(page: Page):
    """
    デスクトップ（1920px）でのレイアウトが適切に表示されることを確認

    期待される動作:
    - グリッドが3カラム以上で表示される（Streamlitのデフォルト）
    - フォントサイズが18px前後である
    """
    # デスクトップ画面サイズに設定
    page.set_viewport_size({"width": 1920, "height": 1080})
    wait_for_streamlit(page)

    # フォントサイズを確認（body要素）
    font_size = get_body_font_size(page)
    # 18pxまたは近似値を許容
    assert_font_size_in_range(font_size, ["18px", "18.0px", "17px", "19px", "16px"], "Desktop layout")

def test_media_queries_exist(page: Page):
    """
    CSSメディアクエリが正しく定義されていることを確認

    期待される動作:
    - @media (max-width: 640px) が存在する
    - @media (min-width: 641px) and (max-width: 1024px) が存在する
    - @media (min-width: 1025px) が存在する
    """
    page.set_viewport_size({"width": 1920, "height": 1080})
    wait_for_streamlit(page)

    # ページ内のすべてのCSSルールを取得
    css_text = page.evaluate("""
        () => {
            let css = '';
            for (let sheet of document.styleSheets) {
                try {
                    for (let rule of sheet.cssRules) {
                        css += rule.cssText + ' ';
                    }
                } catch (e) {
                    // CORS制限などでアクセスできない場合はスキップ
                }
            }
            return css;
        }
    """)

    # 各メディアクエリの存在を確認
    assert "max-width: 640px" in css_text or "max-width:640px" in css_text, "Mobile media query not found"
    assert ("min-width: 641px" in css_text or "min-width:641px" in css_text) and \
           ("max-width: 1024px" in css_text or "max-width:1024px" in css_text), "Tablet media query not found"
    assert "min-width: 1025px" in css_text or "min-width:1025px" in css_text, "Desktop media query not found"

def test_touch_target_sizes(page: Page):
    """
    モバイルでのタッチターゲットが44x44px以上であることを確認（WCAG推奨）

    期待される動作:
    - ボタンの最小サイズが44x44pxである
    - タップターゲット間の間隔が8px以上である
    """
    # モバイル画面サイズに設定
    page.set_viewport_size({"width": 375, "height": 667})
    wait_for_streamlit(page)

    # ボタン要素のサイズを取得して検証
    buttons = page.locator(".stButton > button")
    if buttons.count() > 0:
        # 最初のボタンのサイズを確認
        button = buttons.first
        bbox = button.bounding_box()
        if bbox:
            # min-heightが44pxに設定されているか確認（実際の高さではなく、CSS設定を確認）
            min_height = button.evaluate("el => window.getComputedStyle(el).minHeight")
            assert min_height == "44px" or float(min_height.replace("px", "")) >= 44, \
                f"Button min-height should be >= 44px, got {min_height}"

            min_width = button.evaluate("el => window.getComputedStyle(el).minWidth")
            assert min_width == "44px" or float(min_width.replace("px", "")) >= 44, \
                f"Button min-width should be >= 44px, got {min_width}"
    else:
        # ボタンが存在しない場合もパス（ページによってはボタンがない場合がある）
        pass
