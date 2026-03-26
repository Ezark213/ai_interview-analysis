"""
テスト: components/ui.py
UIヘルパーコンポーネントのテスト
"""

import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.components.ui import render_page_header


def test_render_page_header_basic():
    """基本的なページヘッダーが生成されるか"""
    title = "テストページ"
    description = "これはテスト用の説明文です"

    result = render_page_header(title, description)

    assert isinstance(result, str), "返り値は文字列であるべき"
    assert title in result, "タイトルが含まれているべき"
    assert description in result, "説明文が含まれているべき"
    assert len(result) > 0, "空文字列ではないべき"


def test_render_page_header_with_empty_description():
    """説明が空の場合も動作するか"""
    title = "タイトルのみ"

    # 説明を省略した場合
    result1 = render_page_header(title)
    assert isinstance(result1, str), "返り値は文字列であるべき"
    assert title in result1, "タイトルが含まれているべき"

    # 説明を空文字列で指定した場合
    result2 = render_page_header(title, "")
    assert isinstance(result2, str), "返り値は文字列であるべき"
    assert title in result2, "タイトルが含まれているべき"


def test_render_page_header_markdown_format():
    """Markdown形式が正しいか"""
    title = "マークダウンテスト"
    description = "マークダウン形式のテストです"

    result = render_page_header(title, description)

    # h1タグまたは # が含まれているか（Streamlitのマークダウン形式）
    has_h1 = ("# " in result or "<h1>" in result)
    assert has_h1, "h1レベルの見出しが含まれているべき"

    # 区切り線が含まれているか
    has_divider = ("---" in result or "<hr" in result or "divider" in result.lower())
    assert has_divider, "区切り線が含まれているべき"
