"""
エンコーディングテスト

Windows環境でUTF-8が正しく動作することを確認する。
Iteration-07-encoding-fix: asciiエンコーディングエラー修正
"""

import pytest
import sys


def test_japanese_string_encoding():
    """日本語文字列が正しく処理できることを確認"""
    japanese_text = "チャンクを解析中..."

    # 文字列をエンコード・デコードしてエラーが発生しないことを確認
    try:
        encoded = japanese_text.encode('utf-8')
        decoded = encoded.decode('utf-8')
        assert decoded == japanese_text
    except UnicodeEncodeError as e:
        pytest.fail(f"Failed to encode Japanese text: {e}")
    except UnicodeDecodeError as e:
        pytest.fail(f"Failed to decode Japanese text: {e}")


def test_stdout_encoding():
    """stdout/stderrがUTF-8エンコーディングを使用していることを確認（Windows環境）"""
    if sys.platform == 'win32':
        # Windows環境でのみチェック
        assert sys.stdout.encoding.lower() in ['utf-8', 'utf8'], \
            f"stdout encoding is {sys.stdout.encoding}, expected utf-8"
        assert sys.stderr.encoding.lower() in ['utf-8', 'utf8'], \
            f"stderr encoding is {sys.stderr.encoding}, expected utf-8"
    else:
        # 非Windows環境ではスキップ
        pytest.skip("Not Windows environment")


def test_print_japanese():
    """日本語文字列のprint()が正常に動作することを確認"""
    try:
        print("テスト: チャンク解析中...")
        print("成功: UTF-8エンコーディング")
    except UnicodeEncodeError as e:
        pytest.fail(f"Failed to print Japanese text: {e}")
