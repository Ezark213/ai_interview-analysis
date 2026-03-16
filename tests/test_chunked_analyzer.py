"""チャンク解析機能のテスト"""
import json
import pytest
from unittest.mock import MagicMock
from src.chunked_analyzer import ChunkedVideoAnalyzer
from src.video_chunker import ChunkInfo


class TestChunkedVideoAnalyzer:
    """チャンク単位での動画解析機能のテスト"""

    @pytest.fixture
    def api_key(self):
        """テスト用APIキー"""
        return "test_api_key_12345"

    @pytest.fixture
    def analyzer(self, api_key):
        """ChunkedVideoAnalyzerインスタンス"""
        return ChunkedVideoAnalyzer(api_key=api_key, model="gemini-2.5-flash")

    @pytest.fixture
    def single_chunk(self, tmp_path):
        """単一チャンク情報"""
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"dummy")
        return ChunkInfo(
            chunk_id=0,
            start_time=0,
            end_time=300,
            duration=300,
            video_path=str(video_path)
        )

    @pytest.fixture
    def multiple_chunks(self, tmp_path):
        """複数チャンク情報（3チャンク）"""
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"dummy")
        return [
            ChunkInfo(chunk_id=0, start_time=0, end_time=300, duration=300, video_path=str(video_path)),
            ChunkInfo(chunk_id=1, start_time=300, end_time=600, duration=300, video_path=str(video_path)),
            ChunkInfo(chunk_id=2, start_time=600, end_time=900, duration=300, video_path=str(video_path))
        ]

    @pytest.fixture
    def mock_gemini_response(self):
        """モックGeminiレスポンス"""
        return {
            "overall_risk_score": 70,
            "risk_level": "低",
            "evaluation": {
                "communication": {"score": 75, "observations": ["明瞭な発話"], "confidence": "高"},
                "stress_tolerance": {"score": 65, "observations": ["落ち着いている"], "confidence": "中"},
                "reliability": {"score": 70, "observations": ["具体的な説明"], "confidence": "高"},
                "teamwork": {"score": 70, "observations": ["協調的"], "confidence": "中"}
            },
            "red_flags": [],
            "positive_signals": ["技術力あり"],
            "recommendation": "問題なし",
            "disclaimer": "本評価はAIによる参考情報です。"
        }

    def test_analyze_single_chunk(self, analyzer, single_chunk, mock_gemini_response):
        """正常系: 単一チャンクを解析してJSON評価を取得"""
        # モッククライアントの設定
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_client.files.upload.return_value = mock_file

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_response, ensure_ascii=False)
        mock_client.models.generate_content.return_value = mock_response

        analyzer._client = mock_client

        # 実行
        result = analyzer.analyze_chunk(single_chunk)

        # 検証
        assert result["overall_risk_score"] == 70
        assert result["risk_level"] == "低"
        assert "chunk_id" in result  # チャンクIDが付加されていること
        assert result["chunk_id"] == 0
        assert "chunk_time_range" in result  # 時間範囲が付加されていること
        assert result["chunk_time_range"]["start"] == 0
        assert result["chunk_time_range"]["end"] == 300

        # APIが正しく呼ばれたことを確認
        mock_client.files.upload.assert_called_once()

    def test_analyze_multiple_chunks(self, analyzer, multiple_chunks, mock_gemini_response):
        """正常系: 複数チャンクを順次解析"""
        # モッククライアントの設定
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_client.files.upload.return_value = mock_file

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_response, ensure_ascii=False)
        mock_client.models.generate_content.return_value = mock_response

        analyzer._client = mock_client

        # 実行
        results = analyzer.analyze_chunks(multiple_chunks)

        # 検証
        assert len(results) == 3
        assert results[0]["chunk_id"] == 0
        assert results[1]["chunk_id"] == 1
        assert results[2]["chunk_id"] == 2

        # 各チャンクの時間範囲が正しいこと
        assert results[0]["chunk_time_range"]["start"] == 0
        assert results[0]["chunk_time_range"]["end"] == 300
        assert results[1]["chunk_time_range"]["start"] == 300
        assert results[1]["chunk_time_range"]["end"] == 600

        # APIが3回呼ばれたことを確認
        assert mock_client.files.upload.call_count == 3

    def test_analyze_chunk_api_error(self, analyzer, single_chunk):
        """異常系: APIエラー時の適切なハンドリング"""
        # モッククライアントでエラーを発生させる
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_client.files.upload.return_value = mock_file
        mock_client.models.generate_content.side_effect = Exception("API Error")

        analyzer._client = mock_client

        # 実行と検証
        with pytest.raises(Exception, match="API Error"):
            analyzer.analyze_chunk(single_chunk)

    def test_analyze_chunk_corrupted_file(self, analyzer, tmp_path):
        """異常系: チャンクファイルが破損している場合"""
        # 破損したファイル（存在するが読み込めない想定）
        # ここでは存在しないファイルとして模擬
        corrupted_chunk = ChunkInfo(
            chunk_id=0,
            start_time=0,
            end_time=300,
            duration=300,
            video_path="/path/to/corrupted.mp4"  # 存在しないパス
        )

        mock_client = MagicMock()
        analyzer._client = mock_client

        # ファイルアップロードでエラー
        mock_client.files.upload.side_effect = FileNotFoundError("File not found")

        # 実行と検証
        with pytest.raises(FileNotFoundError):
            analyzer.analyze_chunk(corrupted_chunk)

    def test_analyze_chunks_parallel(self, analyzer, multiple_chunks, mock_gemini_response):
        """正常系: 複数チャンクを並列解析"""
        # モッククライアントの設定
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_client.files.upload.return_value = mock_file

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_response, ensure_ascii=False)
        mock_client.models.generate_content.return_value = mock_response

        analyzer._client = mock_client

        # 実行（並列処理を明示的に指定）
        results = analyzer.analyze_chunks(multiple_chunks, parallel=True, max_workers=3)

        # 検証
        assert len(results) == 3

        # 結果の順序が保持されていること（chunk_id順）
        assert results[0]["chunk_id"] == 0
        assert results[1]["chunk_id"] == 1
        assert results[2]["chunk_id"] == 2

        # 各チャンクの時間範囲が正しいこと
        assert results[0]["chunk_time_range"]["start"] == 0
        assert results[0]["chunk_time_range"]["end"] == 300

        # APIが3回呼ばれたことを確認
        assert mock_client.files.upload.call_count == 3

    def test_analyze_chunks_sequential(self, analyzer, multiple_chunks, mock_gemini_response):
        """正常系: 複数チャンクを順次解析（並列処理無効）"""
        # モッククライアントの設定
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_client.files.upload.return_value = mock_file

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_response, ensure_ascii=False)
        mock_client.models.generate_content.return_value = mock_response

        analyzer._client = mock_client

        # 実行（並列処理を無効化）
        results = analyzer.analyze_chunks(multiple_chunks, parallel=False)

        # 検証
        assert len(results) == 3
        assert results[0]["chunk_id"] == 0
        assert results[1]["chunk_id"] == 1
        assert results[2]["chunk_id"] == 2

    def test_analyze_chunks_parallel_with_error(self, analyzer, multiple_chunks, mock_gemini_response):
        """並列処理中にエラーが発生した場合のハンドリング"""
        # モッククライアントの設定
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_client.files.upload.return_value = mock_file

        # 2番目のチャンクでエラーを発生させる
        call_count = 0

        def mock_generate_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("API Error on chunk 2")
            mock_response = MagicMock()
            mock_response.text = json.dumps(mock_gemini_response, ensure_ascii=False)
            return mock_response

        mock_client.models.generate_content.side_effect = mock_generate_side_effect

        analyzer._client = mock_client

        # 実行
        results = analyzer.analyze_chunks(multiple_chunks, parallel=True, max_workers=3)

        # 検証: エラーが発生したチャンクはエラー情報が記録されている
        assert len(results) == 3

        # エラーが発生したチャンク（chunk_id=1）を確認
        error_result = next((r for r in results if r.get("error")), None)
        assert error_result is not None
        assert "error" in error_result
        assert "API Error" in error_result["error"]
