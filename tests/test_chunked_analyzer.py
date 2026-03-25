"""チャンク解析機能のテスト

更新: IT-11 — api_keys引数、ファイル状態待機、エラーdict返却に対応
"""
import json
import pytest
from unittest.mock import MagicMock
from src.chunked_analyzer import ChunkedVideoAnalyzer
from src.video_chunker import ChunkInfo


def _make_mock_file(state="ACTIVE"):
    """テスト用モックファイルオブジェクト"""
    mock_file = MagicMock()
    mock_file.name = "test_uploaded_file"
    mock_file.state = state
    return mock_file


def _make_mock_client(mock_gemini_response, mock_file=None):
    """テスト用モッククライアントを構築"""
    if mock_file is None:
        mock_file = _make_mock_file()

    mock_client = MagicMock()
    # models.list()がイテラブルを返すように設定
    mock_client.models.list.return_value = iter([])
    # ファイルアップロード
    mock_client.files.upload.return_value = mock_file
    # ファイル状態取得（ACTIVE）
    mock_client.files.get.return_value = mock_file
    # コンテンツ生成
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_gemini_response, ensure_ascii=False)
    mock_client.models.generate_content.return_value = mock_response

    return mock_client


class TestChunkedVideoAnalyzer:
    """チャンク単位での動画解析機能のテスト"""

    @pytest.fixture
    def analyzer(self):
        """ChunkedVideoAnalyzerインスタンス"""
        return ChunkedVideoAnalyzer(api_keys=["test_api_key_12345"], model="gemini-2.5-flash")

    @pytest.fixture
    def single_chunk(self, tmp_path):
        """単一チャンク情報"""
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"\x00" * 100)
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
        video_path.write_bytes(b"\x00" * 100)
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
                "communication": {"score": 75, "observations": ["明瞭な発話（参照: コミュニケーション基準）"], "confidence": "高"},
                "stress_tolerance": {"score": 65, "observations": ["落ち着いている（参照: ストレス耐性基準）"], "confidence": "中"},
                "reliability": {"score": 70, "observations": ["具体的な説明（参照: 信頼性評価基準）"], "confidence": "高"},
                "teamwork": {"score": 70, "observations": ["協調的（参照: チームワーク基準）"], "confidence": "中"},
                "credibility": {"score": 65, "observations": ["検証可能な詳細あり（参照: 信頼度基準）"], "confidence": "中"},
                "professional_demeanor": {"score": 65, "observations": ["敬語適切（参照: 職業的態度基準）"], "confidence": "中"}
            },
            "behavioral_metrics": None,
            "red_flags": [],
            "positive_signals": ["技術力あり"],
            "recommendation": "問題なし",
            "disclaimer": "本評価はAIによる参考情報です。"
        }

    def test_analyze_single_chunk(self, analyzer, single_chunk, mock_gemini_response):
        """正常系: 単一チャンクを解析してJSON評価を取得"""
        mock_client = _make_mock_client(mock_gemini_response)
        analyzer._client = mock_client

        result = analyzer.analyze_chunk(single_chunk)

        assert result["status"] == "success"
        assert result["overall_risk_score"] == 70
        assert result["risk_level"] == "低"
        assert result["chunk_id"] == 0
        assert result["chunk_time_range"]["start"] == 0
        assert result["chunk_time_range"]["end"] == 300
        mock_client.files.upload.assert_called_once()

    def test_analyze_multiple_chunks(self, analyzer, multiple_chunks, mock_gemini_response):
        """正常系: 複数チャンクを順次解析"""
        mock_client = _make_mock_client(mock_gemini_response)
        analyzer._client = mock_client

        results = analyzer.analyze_chunks(multiple_chunks)

        assert len(results) == 3
        assert results[0]["chunk_id"] == 0
        assert results[1]["chunk_id"] == 1
        assert results[2]["chunk_id"] == 2
        assert results[0]["chunk_time_range"]["start"] == 0
        assert results[0]["chunk_time_range"]["end"] == 300
        assert results[1]["chunk_time_range"]["start"] == 300
        assert results[1]["chunk_time_range"]["end"] == 600
        assert mock_client.files.upload.call_count == 3

    def test_analyze_chunk_api_error(self, analyzer, single_chunk, mock_gemini_response):
        """異常系: APIエラー時にエラーdictが返される"""
        mock_client = _make_mock_client(mock_gemini_response)
        # models.list()でAPIエラーを発生させる
        mock_client.models.list.side_effect = Exception("API Error")
        analyzer._client = mock_client

        result = analyzer.analyze_chunk(single_chunk)

        assert result["status"] == "error"
        assert "error_message" in result

    def test_analyze_chunk_corrupted_file(self, analyzer, tmp_path):
        """異常系: チャンクファイルが存在しない場合"""
        corrupted_chunk = ChunkInfo(
            chunk_id=0,
            start_time=0,
            end_time=300,
            duration=300,
            video_path=str(tmp_path / "nonexistent.mp4")
        )

        result = analyzer.analyze_chunk(corrupted_chunk)

        assert result["status"] == "error"
        assert result["error_code"] == "ERR_002_FILE_NOT_FOUND"

    def test_analyze_chunks_parallel(self, analyzer, multiple_chunks, mock_gemini_response):
        """正常系: 複数チャンクを並列解析"""
        mock_client = _make_mock_client(mock_gemini_response)
        analyzer._client = mock_client

        results = analyzer.analyze_chunks(multiple_chunks, parallel=True, max_workers=3)

        assert len(results) == 3
        # 結果の順序が保持されていること（chunk_id順）
        chunk_ids = sorted([r["chunk_id"] for r in results])
        assert chunk_ids == [0, 1, 2]
        assert mock_client.files.upload.call_count == 3

    def test_analyze_chunks_sequential(self, analyzer, multiple_chunks, mock_gemini_response):
        """正常系: 複数チャンクを順次解析（並列処理無効）"""
        mock_client = _make_mock_client(mock_gemini_response)
        analyzer._client = mock_client

        results = analyzer.analyze_chunks(multiple_chunks, parallel=False)

        assert len(results) == 3
        assert results[0]["chunk_id"] == 0
        assert results[1]["chunk_id"] == 1
        assert results[2]["chunk_id"] == 2

    def test_analyze_chunks_parallel_with_error(self, analyzer, multiple_chunks, mock_gemini_response):
        """並列処理中にエラーが発生した場合のハンドリング"""
        mock_client = _make_mock_client(mock_gemini_response)

        # 2番目のチャンクでコンテンツ生成エラーを発生させる
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

        results = analyzer.analyze_chunks(multiple_chunks, parallel=True, max_workers=3)

        assert len(results) == 3
        # エラーが発生したチャンクを確認
        error_results = [r for r in results if r.get("status") == "error"]
        assert len(error_results) >= 1
