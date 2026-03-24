"""
環境セットアップテスト

このテストは、ローカルホスト環境が正しくセットアップされているかを検証する。
Iteration-07: ローカルホスト実装と限定的PoC
"""

import importlib
import os
from pathlib import Path
import pytest


def test_required_packages_installed():
    """必須パッケージがインストールされているかチェック"""
    required = [
        "google.genai",
        "streamlit",
        "scipy",
        "sklearn",
        "pandas",
        "pytest",
        "dotenv"
    ]

    for pkg in required:
        try:
            importlib.import_module(pkg)
        except ImportError:
            pytest.fail(f"Required package {pkg} not installed")


def test_env_file_exists():
    """.envファイルが存在するかチェック"""
    # プロジェクトルートの.envファイルを確認
    env_path = Path(__file__).parent.parent / ".env"
    assert env_path.exists(), (
        f".env file not found at {env_path}. "
        "Please create .env file from .env.example and set GEMINI_API_KEY"
    )


def test_gemini_api_key_in_env():
    """GEMINI_API_KEY_1が.envに設定されているかチェック"""
    from dotenv import load_dotenv

    # .envファイルを読み込む
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("GEMINI_API_KEY_1")
    assert api_key is not None, (
        "GEMINI_API_KEY_1 not set in .env file. "
        "Please add GEMINI_API_KEY_1=your_api_key_here to .env"
    )
    assert len(api_key) > 0, "GEMINI_API_KEY_1 is empty"


def test_api_key_format():
    """APIキーが正しいフォーマットかチェック"""
    from dotenv import load_dotenv

    # .envファイルを読み込む
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("GEMINI_API_KEY_1")

    # 基本的なフォーマットチェック
    assert api_key is not None, "GEMINI_API_KEY_1 not set"
    assert len(api_key) >= 20, (
        f"GEMINI_API_KEY_1 too short (length: {len(api_key)}). "
        "Expected at least 20 characters. "
        "Please verify your API key from https://aistudio.google.com/apikey"
    )
    assert api_key != "your_gemini_api_key_here", (
        "GEMINI_API_KEY_1 is still the placeholder value. "
        "Please replace it with your actual API key from "
        "https://aistudio.google.com/apikey"
    )


def test_ffmpeg_available():
    """ffmpeg-pythonが利用可能かチェック"""
    try:
        import ffmpeg
        # ffmpegモジュールが正しくインポートできることを確認
        assert hasattr(ffmpeg, 'input'), "ffmpeg module does not have 'input' attribute"
    except ImportError:
        pytest.fail(
            "ffmpeg-python not installed. "
            "Please run: pip install ffmpeg-python"
        )


def test_project_structure():
    """プロジェクトの基本構造が正しいかチェック"""
    project_root = Path(__file__).parent.parent

    # 必須ディレクトリの確認
    required_dirs = [
        "src",
        "tests",
        "docs",
        "knowledge-base"
    ]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Required directory {dir_name} not found"

    # 必須ファイルの確認
    required_files = [
        "requirements.txt",
        "README.md"
    ]

    for file_name in required_files:
        file_path = project_root / file_name
        assert file_path.exists(), f"Required file {file_name} not found"


def test_streamlit_app_exists():
    """Streamlitアプリファイルが存在するかチェック"""
    project_root = Path(__file__).parent.parent
    app_path = project_root / "src" / "app.py"

    assert app_path.exists(), (
        f"Streamlit app not found at {app_path}. "
        "The app.py file should be in the src directory."
    )
