"""動画解析アナライザーのテスト"""
import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.analyzer import VideoAnalyzer


class TestVideoAnalyzer:
    """動画解析機能のテスト（モック使用）"""

    @pytest.fixture
    def api_key(self):
        """テスト用APIキー"""
        return "test_api_key_12345"

    @pytest.fixture
    def analyzer(self, api_key):
        """VideoAnalyzerインスタンス"""
        return VideoAnalyzer(api_key=api_key, model="gemini-2.5-flash")

    @pytest.fixture
    def mock_video_file(self, tmp_path):
        """テスト用の動画ファイル（ダミー）"""
        video_path = tmp_path / "test_video.mp4"
        video_path.write_bytes(b"dummy video content")
        return str(video_path)

    def test_analyze_video_success(self, analyzer, mock_video_file, mock_gemini_response):
        """モックAPIで正常解析フロー"""
        # clientプロパティを直接モック
        mock_client = MagicMock()

        # ファイルアップロードのモック
        mock_file = MagicMock()
        mock_client.files.upload.return_value = mock_file

        # generate_contentのモック（JSONレスポンスを返す）
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_response, ensure_ascii=False)
        mock_client.models.generate_content.return_value = mock_response

        # analyzerのclientをモックに置き換え
        analyzer._client = mock_client

        # 実行
        result = analyzer.analyze(mock_video_file)

        # 検証
        assert result["overall_risk_score"] == 65
        assert result["risk_level"] == "低"
        assert "communication" in result["evaluation"]

        # APIが正しく呼ばれたことを確認
        mock_client.files.upload.assert_called_once()
        mock_client.models.generate_content.assert_called_once()

    def test_analyze_video_file_not_found(self, analyzer):
        """存在しないファイルでFileNotFoundError"""
        nonexistent_file = "/path/to/nonexistent/video.mp4"

        # 実行と検証
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            analyzer.analyze(nonexistent_file)

    def test_analyze_video_unsupported_format(self, analyzer, tmp_path):
        """.txtなどサポート外の拡張子でValueError"""
        # サポート外のファイル
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is not a video", encoding="utf-8")

        # 実行と検証
        with pytest.raises(ValueError, match="Unsupported video format"):
            analyzer.analyze(str(txt_file))

    def test_analyze_video_api_error(self, analyzer, mock_video_file):
        """APIエラー時の適切なハンドリング"""
        mock_client = MagicMock()

        # ファイルアップロードは成功
        mock_file = MagicMock()
        mock_client.files.upload.return_value = mock_file

        # generate_contentでエラー
        mock_client.models.generate_content.side_effect = Exception("API Error")

        # analyzerのclientをモックに置き換え
        analyzer._client = mock_client

        # 実行と検証
        with pytest.raises(Exception, match="API Error"):
            analyzer.analyze(mock_video_file)

    def test_supported_formats(self, analyzer, tmp_path):
        """サポートされている拡張子: .mp4, .mov, .avi, .webm"""
        supported_formats = [".mp4", ".mov", ".avi", ".webm"]

        for ext in supported_formats:
            # テストファイル作成
            video_file = tmp_path / f"test{ext}"
            video_file.write_bytes(b"dummy")

            # モックAPIで実行（エラーが出ないことを確認）
            mock_client = MagicMock()

            mock_file = MagicMock()
            mock_client.files.upload.return_value = mock_file

            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "overall_risk_score": 70,
                "risk_level": "低",
                "evaluation": {
                    "communication": {"score": 70, "observations": [], "confidence": "高"},
                    "stress_tolerance": {"score": 70, "observations": [], "confidence": "高"},
                    "reliability": {"score": 70, "observations": [], "confidence": "高"},
                    "teamwork": {"score": 70, "observations": [], "confidence": "高"}
                },
                "red_flags": [],
                "positive_signals": [],
                "recommendation": "test",
                "disclaimer": "test"
            })
            mock_client.models.generate_content.return_value = mock_response

            # analyzerのclientをモックに置き換え
            analyzer._client = mock_client

            # 実行（例外が発生しないことを確認）
            result = analyzer.analyze(str(video_file))
            assert result["overall_risk_score"] == 70
