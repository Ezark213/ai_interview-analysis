"""バッチ処理のテスト

複数動画の一括解析パイプライン、CSV/JSONエクスポートのテスト。
テスト対象:
- batch_processor.py: BatchProcessor.process_batch(), export_to_csv(), export_to_json()
"""
import json
import pytest
from unittest.mock import MagicMock
from src.batch_processor import BatchProcessor


# テスト用のモック解析結果
def _make_mock_result(filename, score=75, risk_level="低"):
    return {
        "filename": filename,
        "status": "success",
        "overall_risk_score": score,
        "risk_level": risk_level,
        "evaluation": {
            "communication": {"score": score, "observations": ["テスト"], "confidence": "高"},
            "stress_tolerance": {"score": score - 5, "observations": ["テスト"], "confidence": "中"},
            "reliability": {"score": score, "observations": ["テスト"], "confidence": "高"},
            "teamwork": {"score": score - 3, "observations": ["テスト"], "confidence": "中"},
        },
        "behavioral_metrics": None,
        "red_flags": [],
        "positive_signals": ["テスト"],
        "recommendation": "テスト推奨事項",
        "disclaimer": "テスト免責事項",
    }


class TestBatchProcessor:
    """バッチ処理のテスト"""

    def test_process_single_video(self, tmp_path):
        """1動画のバッチ処理が正常に動作する"""
        # ダミー動画ファイル作成
        video = tmp_path / "video1.mp4"
        video.write_bytes(b"\x00" * 100)

        # モックアナライザー
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "overall_risk_score": 80,
            "risk_level": "低",
            "evaluation": {
                "communication": {"score": 80, "observations": [], "confidence": "高"},
                "stress_tolerance": {"score": 75, "observations": [], "confidence": "中"},
                "reliability": {"score": 80, "observations": [], "confidence": "高"},
                "teamwork": {"score": 77, "observations": [], "confidence": "中"},
            },
            "behavioral_metrics": None,
            "red_flags": [],
            "positive_signals": [],
            "recommendation": "良好",
            "disclaimer": "テスト",
        }

        processor = BatchProcessor(
            analyzer_factory=lambda: mock_analyzer
        )
        results = processor.process_batch(
            video_paths=[str(video)],
            video_names=["video1.mp4"],
            wait_seconds=0
        )

        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert results[0]["overall_risk_score"] == 80

    def test_process_multiple_videos(self, tmp_path):
        """3動画のバッチ処理が順次実行される"""
        videos = []
        names = []
        for i in range(3):
            v = tmp_path / f"video{i}.mp4"
            v.write_bytes(b"\x00" * 100)
            videos.append(str(v))
            names.append(f"video{i}.mp4")

        call_count = 0

        def mock_analyze(video_path, **kwargs):
            nonlocal call_count
            call_count += 1
            return {
                "overall_risk_score": 70 + call_count * 5,
                "risk_level": "低",
                "evaluation": {
                    "communication": {"score": 75, "observations": [], "confidence": "高"},
                    "stress_tolerance": {"score": 70, "observations": [], "confidence": "中"},
                    "reliability": {"score": 75, "observations": [], "confidence": "高"},
                    "teamwork": {"score": 72, "observations": [], "confidence": "中"},
                },
                "behavioral_metrics": None,
                "red_flags": [],
                "positive_signals": [],
                "recommendation": "テスト",
                "disclaimer": "テスト",
            }

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = mock_analyze

        processor = BatchProcessor(analyzer_factory=lambda: mock_analyzer)
        results = processor.process_batch(videos, names, wait_seconds=0)

        assert len(results) == 3
        assert call_count == 3

    def test_partial_failure_continues(self, tmp_path):
        """1動画が失敗しても残りは処理される"""
        videos = []
        names = []
        for i in range(3):
            v = tmp_path / f"video{i}.mp4"
            v.write_bytes(b"\x00" * 100)
            videos.append(str(v))
            names.append(f"video{i}.mp4")

        call_idx = 0

        def mock_analyze(video_path, **kwargs):
            nonlocal call_idx
            call_idx += 1
            if call_idx == 2:
                raise Exception("API error on video 2")
            return {
                "overall_risk_score": 75,
                "risk_level": "低",
                "evaluation": {
                    "communication": {"score": 75, "observations": [], "confidence": "高"},
                    "stress_tolerance": {"score": 70, "observations": [], "confidence": "中"},
                    "reliability": {"score": 75, "observations": [], "confidence": "高"},
                    "teamwork": {"score": 72, "observations": [], "confidence": "中"},
                },
                "behavioral_metrics": None,
                "red_flags": [],
                "positive_signals": [],
                "recommendation": "テスト",
                "disclaimer": "テスト",
            }

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = mock_analyze

        processor = BatchProcessor(analyzer_factory=lambda: mock_analyzer)
        results = processor.process_batch(videos, names, wait_seconds=0)

        assert len(results) == 3
        # 2番目はエラー
        assert results[1]["status"] == "error"
        assert "error" in results[1]
        # 1番目と3番目は成功
        assert results[0]["status"] == "success"
        assert results[2]["status"] == "success"

    def test_results_contain_all_videos(self, tmp_path):
        """結果リストに全動画の結果が含まれる"""
        videos = []
        names = ["alice.mp4", "bob.mp4", "charlie.mp4"]
        for name in names:
            v = tmp_path / name
            v.write_bytes(b"\x00" * 100)
            videos.append(str(v))

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "overall_risk_score": 75,
            "risk_level": "低",
            "evaluation": {
                "communication": {"score": 75, "observations": [], "confidence": "高"},
                "stress_tolerance": {"score": 70, "observations": [], "confidence": "中"},
                "reliability": {"score": 75, "observations": [], "confidence": "高"},
                "teamwork": {"score": 72, "observations": [], "confidence": "中"},
            },
            "behavioral_metrics": None,
            "red_flags": [],
            "positive_signals": [],
            "recommendation": "テスト",
            "disclaimer": "テスト",
        }

        processor = BatchProcessor(analyzer_factory=lambda: mock_analyzer)
        results = processor.process_batch(videos, names, wait_seconds=0)

        filenames = [r["filename"] for r in results]
        assert "alice.mp4" in filenames
        assert "bob.mp4" in filenames
        assert "charlie.mp4" in filenames

    def test_export_results_to_csv(self):
        """結果をCSV形式でエクスポートできる"""
        results = [
            _make_mock_result("video1.mp4", score=80, risk_level="低"),
            _make_mock_result("video2.mp4", score=60, risk_level="中"),
        ]

        processor = BatchProcessor(analyzer_factory=lambda: None)
        csv_str = processor.export_to_csv(results)

        assert isinstance(csv_str, str)
        assert "video1.mp4" in csv_str
        assert "video2.mp4" in csv_str
        # ヘッダーが含まれること
        assert "ファイル名" in csv_str or "filename" in csv_str

    def test_export_results_to_json(self):
        """結果をJSON形式でエクスポートできる"""
        results = [
            _make_mock_result("video1.mp4", score=80),
            _make_mock_result("video2.mp4", score=60),
        ]

        processor = BatchProcessor(analyzer_factory=lambda: None)
        json_str = processor.export_to_json(results)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert len(parsed) == 2
        assert parsed[0]["filename"] == "video1.mp4"

    def test_empty_batch_raises_error(self):
        """空のバッチでエラーが返る"""
        processor = BatchProcessor(analyzer_factory=lambda: None)

        with pytest.raises(ValueError):
            processor.process_batch(
                video_paths=[],
                video_names=[],
                wait_seconds=0
            )

    def test_max_batch_size_exceeded_raises_error(self):
        """MAX_BATCH_SIZE超過でValueErrorが返る"""
        processor = BatchProcessor(analyzer_factory=lambda: None)

        with pytest.raises(ValueError, match="exceeds maximum"):
            processor.process_batch(
                video_paths=["dummy.mp4"] * 11,
                video_names=["dummy.mp4"] * 11,
                wait_seconds=0
            )
