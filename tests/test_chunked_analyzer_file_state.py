"""
ChunkedVideoAnalyzer ファイル状態待機テスト

Gemini APIのファイルアップロード後、ACTIVE状態になるまで待機することを確認する。
Iteration-07-file-state-fix: スコア0問題修正
更新: IT-11 — api_keys引数、モックパス修正
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.chunked_analyzer import ChunkedVideoAnalyzer
from src.video_chunker import ChunkInfo


class TestFileStateWaiting:
    """ファイル状態待機処理のテスト"""

    @pytest.fixture
    def mock_chunk(self, tmp_path):
        """テスト用のChunkInfo（実在するダミーファイル）"""
        video_path = tmp_path / "test_video.mp4"
        video_path.write_bytes(b"\x00" * 100)
        return ChunkInfo(
            chunk_id=0,
            start_time=0,
            end_time=300,
            duration=300,
            video_path=str(video_path)
        )

    def test_file_state_waiting_processing_to_active(self, mocker, mock_chunk):
        """
        ファイルがPROCESSING→ACTIVE状態に遷移するまで待機することを確認
        """
        analyzer = ChunkedVideoAnalyzer(api_keys=["test_api_key"])

        # モックファイルオブジェクト
        mock_file_processing = MagicMock()
        mock_file_processing.name = "test_file_name"
        mock_file_processing.state = "PROCESSING"

        mock_file_active = MagicMock()
        mock_file_active.name = "test_file_name"
        mock_file_active.state = "ACTIVE"

        # モッククライアント
        mock_client = MagicMock()
        # models.list()がイテラブルを返すように設定
        mock_client.models.list.return_value = iter([])
        # files.upload()は最初にPROCESSING状態のファイルを返す
        mock_client.files.upload.return_value = mock_file_processing
        # files.get()は1回目はPROCESSING、2回目以降はACTIVEを返す
        mock_client.files.get.side_effect = [
            mock_file_processing,  # 1回目: まだPROCESSING
            mock_file_active       # 2回目: ACTIVE
        ]

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "overall_risk_score": 50,
            "risk_level": "中",
            "evaluation": {
                "communication": {"score": 55, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                "stress_tolerance": {"score": 50, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                "reliability": {"score": 50, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                "teamwork": {"score": 50, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
            },
            "behavioral_metrics": None,
            "red_flags": [],
            "positive_signals": [],
            "recommendation": "テスト",
            "disclaimer": "テスト"
        }, ensure_ascii=False)
        mock_client.models.generate_content.return_value = mock_response

        # クライアントを差し替え
        analyzer._client = mock_client

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
        ファイル状態がFAILEDの場合、エラー結果が返されることを確認
        """
        analyzer = ChunkedVideoAnalyzer(api_keys=["test_api_key"])

        # モックファイルオブジェクト
        mock_file_processing = MagicMock()
        mock_file_processing.name = "test_file_name"
        mock_file_processing.state = "PROCESSING"

        mock_file_failed = MagicMock()
        mock_file_failed.name = "test_file_name"
        mock_file_failed.state = "FAILED"

        # モッククライアント
        mock_client = MagicMock()
        mock_client.models.list.return_value = iter([])
        mock_client.files.upload.return_value = mock_file_processing
        mock_client.files.get.return_value = mock_file_failed

        analyzer._client = mock_client

        # モックのtime.sleep
        mocker.patch('time.sleep')

        # analyze_chunkを実行 — FAILEDファイルはエラーdictで返される
        result = analyzer.analyze_chunk(mock_chunk)

        assert result["status"] == "error"
        assert "ERR_005" in result.get("error_code", "")
