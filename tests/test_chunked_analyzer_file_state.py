"""
ChunkedVideoAnalyzer ファイル状態待機テスト

Gemini APIのファイルアップロード後、ACTIVE状態になるまで待機することを確認する。
Iteration-07-file-state-fix: スコア0問題修正
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from chunked_analyzer import ChunkedVideoAnalyzer
from video_chunker import ChunkInfo


class TestFileStateWaiting:
    """ファイル状態待機処理のテスト"""

    @pytest.fixture
    def mock_chunk(self):
        """テスト用のChunkInfo"""
        return ChunkInfo(
            chunk_id=0,
            start_time=0,
            end_time=300,
            duration=300,
            video_path="test_video.mp4"
        )

    def test_file_state_waiting_processing_to_active(self, mocker, mock_chunk):
        """
        ファイルがPROCESSING→ACTIVE状態に遷移するまで待機することを確認
        """
        # ChunkedVideoAnalyzerのインスタンス作成
        analyzer = ChunkedVideoAnalyzer(api_key="test_api_key")

        # モックファイルオブジェクト
        mock_file_processing = MagicMock()
        mock_file_processing.name = "test_file_name"
        mock_file_processing.state = "PROCESSING"

        mock_file_active = MagicMock()
        mock_file_active.name = "test_file_name"
        mock_file_active.state = "ACTIVE"

        # モッククライアント
        mock_client = MagicMock()

        # files.upload()は最初にPROCESSING状態のファイルを返す
        mock_client.files.upload.return_value = mock_file_processing

        # files.get()は1回目はPROCESSING、2回目以降はACTIVEを返す
        mock_client.files.get.side_effect = [
            mock_file_processing,  # 1回目: まだPROCESSING
            mock_file_active       # 2回目: ACTIVE
        ]

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.text = '{"overall_risk_score": 50, "evaluation": {}}'
        mock_client.models.generate_content.return_value = mock_response

        # クライアントを差し替え
        analyzer._client = mock_client

        # モックの知識ベース読み込み、プロンプト構築、レスポンスパース
        mocker.patch('chunked_analyzer.load_knowledge_base', return_value="test knowledge")
        mocker.patch('chunked_analyzer.build_prompt', return_value="test prompt")
        mocker.patch('chunked_analyzer.parse_response', return_value={"overall_risk_score": 50})

        # モックのtime.sleep（実際に待機しない）
        mocker.patch('time.sleep')

        # analyze_chunkを実行
        result = analyzer.analyze_chunk(mock_chunk)

        # 検証1: files.get()が呼び出されたことを確認（状態待機が実行された）
        assert mock_client.files.get.call_count >= 1, \
            "files.get() should be called to check file state"

        # 検証2: generate_content()が呼び出されたことを確認（ACTIVE後に実行）
        assert mock_client.models.generate_content.called, \
            "generate_content() should be called after file is ACTIVE"

    def test_file_state_failed(self, mocker, mock_chunk):
        """
        ファイル状態がFAILEDの場合、例外を発生させることを確認
        """
        analyzer = ChunkedVideoAnalyzer(api_key="test_api_key")

        # モックファイルオブジェクト
        mock_file_processing = MagicMock()
        mock_file_processing.name = "test_file_name"
        mock_file_processing.state = "PROCESSING"

        mock_file_failed = MagicMock()
        mock_file_failed.name = "test_file_name"
        mock_file_failed.state = "FAILED"

        # モッククライアント
        mock_client = MagicMock()
        mock_client.files.upload.return_value = mock_file_processing
        mock_client.files.get.return_value = mock_file_failed

        analyzer._client = mock_client

        # モックの依存関数
        mocker.patch('chunked_analyzer.load_knowledge_base', return_value="test knowledge")
        mocker.patch('chunked_analyzer.build_prompt', return_value="test prompt")
        mocker.patch('time.sleep')

        # analyze_chunkを実行し、例外が発生することを確認
        with pytest.raises(Exception, match="File processing failed"):
            analyzer.analyze_chunk(mock_chunk)
