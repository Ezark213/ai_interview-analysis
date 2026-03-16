"""共通フィクスチャ設定"""
import json
import os
import pytest


@pytest.fixture
def fixtures_dir():
    """フィクスチャディレクトリのパスを返す"""
    return os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def mock_gemini_response(fixtures_dir):
    """モックGeminiレスポンスJSONを読み込む"""
    with open(os.path.join(fixtures_dir, "mock_gemini_response.json"), "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def test_knowledge_path(fixtures_dir):
    """テスト用ナレッジファイルのパスを返す"""
    return os.path.join(fixtures_dir, "test_knowledge.md")
