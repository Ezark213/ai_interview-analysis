"""
インポート検証テスト

src/ディレクトリ内のモジュールが正しくインポートできることを確認する。
Iteration-07-hotfix: ModuleNotFoundError修正
"""

import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_analyzer_import():
    """VideoAnalyzerが正しくインポートできることを確認"""
    try:
        from analyzer import VideoAnalyzer
        assert VideoAnalyzer is not None
    except ImportError as e:
        pytest.fail(f"Failed to import VideoAnalyzer: {e}")


def test_chunked_analyzer_import():
    """ChunkedVideoAnalyzerが正しくインポートできることを確認"""
    try:
        from chunked_analyzer import ChunkedVideoAnalyzer
        assert ChunkedVideoAnalyzer is not None
    except ImportError as e:
        pytest.fail(f"Failed to import ChunkedVideoAnalyzer: {e}")


def test_no_src_prefix_in_imports():
    """src/内のファイルに'from src.'形式のインポートが残っていないことを確認"""
    import subprocess

    result = subprocess.run(
        ['grep', '-rn', 'from src\\.', str(project_root / 'src'), '--include=*.py'],
        capture_output=True,
        text=True
    )

    # grepの戻り値: 0=見つかった, 1=見つからない, 2=エラー
    if result.returncode == 0:
        pytest.fail(
            f"Found 'from src.' imports in src/ directory:\n{result.stdout}"
        )
    elif result.returncode == 2:
        pytest.fail(f"Error running grep: {result.stderr}")
    # returncode == 1 は正常（パターンが見つからない）


def test_video_chunker_import():
    """video_chunkerモジュールが正しくインポートできることを確認"""
    try:
        from video_chunker import VideoChunker, ChunkInfo, get_video_duration
        assert VideoChunker is not None
        assert ChunkInfo is not None
        assert get_video_duration is not None
    except ImportError as e:
        pytest.fail(f"Failed to import from video_chunker: {e}")


def test_knowledge_loader_import():
    """knowledge_loaderモジュールが正しくインポートできることを確認"""
    try:
        from knowledge_loader import load_knowledge_base
        assert load_knowledge_base is not None
    except ImportError as e:
        pytest.fail(f"Failed to import load_knowledge_base: {e}")
