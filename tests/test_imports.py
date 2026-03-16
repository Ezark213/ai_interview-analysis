"""
インポート検証テスト

src/ディレクトリ内のモジュールが正しくインポートできることを確認する。
Iteration-07-hotfix: ModuleNotFoundError修正
相対インポート対応: パッケージとしてインポート
"""

import pytest
from pathlib import Path

# プロジェクトルートを取得（grep用）
project_root = Path(__file__).parent.parent


def test_analyzer_import():
    """VideoAnalyzerが正しくインポートできることを確認"""
    try:
        from src.analyzer import VideoAnalyzer
        assert VideoAnalyzer is not None
    except ImportError as e:
        pytest.fail(f"Failed to import VideoAnalyzer: {e}")


def test_chunked_analyzer_import():
    """ChunkedVideoAnalyzerが正しくインポートできることを確認"""
    try:
        from src.chunked_analyzer import ChunkedVideoAnalyzer
        assert ChunkedVideoAnalyzer is not None
    except ImportError as e:
        pytest.fail(f"Failed to import ChunkedVideoAnalyzer: {e}")


def test_no_src_prefix_in_imports():
    """
    内部モジュールに'from src.'形式のインポートが残っていないことを確認

    注: app.py と streamlit_app.py はエントリーポイントスクリプトなので、
         動的インポートで 'from src.xxx' を使用するのは正常
    """
    import subprocess

    result = subprocess.run(
        ['grep', '-rn', 'from src\\.', str(project_root / 'src'), '--include=*.py',
         '--exclude=app.py', '--exclude=streamlit_app.py'],
        capture_output=True,
        text=True
    )

    # grepの戻り値: 0=見つかった, 1=見つからない, 2=エラー
    if result.returncode == 0:
        pytest.fail(
            f"Found 'from src.' imports in internal modules (excluding app.py, streamlit_app.py):\n{result.stdout}"
        )
    elif result.returncode == 2:
        pytest.fail(f"Error running grep: {result.stderr}")
    # returncode == 1 は正常（パターンが見つからない）


def test_video_chunker_import():
    """video_chunkerモジュールが正しくインポートできることを確認"""
    try:
        from src.video_chunker import VideoChunker, ChunkInfo, get_video_duration
        assert VideoChunker is not None
        assert ChunkInfo is not None
        assert get_video_duration is not None
    except ImportError as e:
        pytest.fail(f"Failed to import from video_chunker: {e}")


def test_knowledge_loader_import():
    """knowledge_loaderモジュールが正しくインポートできることを確認"""
    try:
        from src.knowledge_loader import load_knowledge_base
        assert load_knowledge_base is not None
    except ImportError as e:
        pytest.fail(f"Failed to import load_knowledge_base: {e}")
