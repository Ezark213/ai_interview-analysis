"""
テスト: components/styles.py
カスタムCSS注入関数のテスト
"""

import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.components.styles import inject_custom_css


def test_inject_custom_css_returns_html_tag():
    """CSS注入関数が<style>タグで囲まれたHTMLを返すか"""
    result = inject_custom_css()

    assert isinstance(result, str), "返り値は文字列であるべき"
    assert result.strip().startswith("<style>"), "<style>タグで始まるべき"
    assert result.strip().endswith("</style>"), "</style>タグで終わるべき"
    assert len(result) > 100, "CSSの内容が含まれているべき"


def test_custom_css_contains_color_palette():
    """カラーパレットが定義されているか"""
    result = inject_custom_css()

    # プライマリカラー
    assert "#1B2559" in result, "ダークネイビー（プライマリ）が定義されているべき"
    assert "#4F6AF0" in result, "ブルー（アクセント）が定義されているべき"

    # セマンティックカラー
    assert "#10B981" in result or "10B981" in result, "成功色（グリーン）が定義されているべき"
    assert "#F59E0B" in result or "F59E0B" in result, "警告色（アンバー）が定義されているべき"
    assert "#EF4444" in result or "EF4444" in result, "危険色（レッド）が定義されているべき"

    # ニュートラルカラー
    assert "#F8FAFC" in result or "F8FAFC" in result, "背景色（メイン）が定義されているべき"
    assert "#FFFFFF" in result or "FFFFFF" in result, "背景色（カード）が定義されているべき"


def test_custom_css_contains_sidebar_styles():
    """サイドバースタイル（ダークネイビー背景）が含まれているか"""
    result = inject_custom_css()

    # サイドバーのセレクタが含まれているか
    assert '[data-testid="stSidebar"]' in result, "サイドバーセレクタが含まれているべき"

    # ダークネイビー背景が含まれているか（gradient または solid）
    has_sidebar_bg = (
        "background:" in result and "#1B2559" in result
    ) or (
        "background-color:" in result and "#1B2559" in result
    ) or (
        "linear-gradient" in result and "#1B2559" in result
    )

    assert has_sidebar_bg, "サイドバーのダークネイビー背景が定義されているべき"
