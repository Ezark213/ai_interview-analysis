"""
統合テスト（エンドツーエンド）

動画読み込み→解析→結果生成の一連の流れをテストする。
API呼び出しはモック化して実行。

更新: IT-11 — 現行API（ChunkedVideoAnalyzer, api_keys, ChunkIntegrator）に合わせて修正
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.chunked_analyzer import ChunkedVideoAnalyzer
from src.video_chunker import VideoChunker, ChunkInfo
from src.chunk_integrator import ChunkIntegrator


@pytest.fixture
def mock_gemini_response():
    """モックGemini APIレスポンス"""
    return {
        "overall_risk_score": 85,
        "risk_level": "低い",
        "evaluation": {
            "communication": {
                "score": 80,
                "observations": ["明瞭な発話（参照: コミュニケーション基準）"],
                "confidence": "高"
            },
            "stress_tolerance": {
                "score": 85,
                "observations": ["冷静な対応（参照: ストレス耐性基準）"],
                "confidence": "高"
            },
            "reliability": {
                "score": 90,
                "observations": ["具体的な実績提示（参照: 信頼性評価基準）"],
                "confidence": "高"
            },
            "teamwork": {
                "score": 85,
                "observations": ["協力的な姿勢（参照: チームワーク基準）"],
                "confidence": "高"
            }
        },
        "behavioral_metrics": None,
        "red_flags": [],
        "positive_signals": ["技術力が高い", "自己学習の習慣"],
        "recommendation": "優秀な候補者。アサインを推奨。",
        "disclaimer": "本評価はAIによる参考情報です。"
    }


def test_video_file_loading(tmp_path):
    """動画ファイルの読み込み確認: VideoChunkerの基本動作"""
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"\x00" * 100)

    chunker = VideoChunker(chunk_duration_seconds=300)
    assert chunker is not None
    assert chunker.chunk_duration == 300

    # split_physically=Falseでチャンク情報を生成できること
    chunks = chunker.create_chunks(str(video_path), 600, split_physically=False)
    assert len(chunks) == 2
    assert chunks[0].start_time == 0
    assert chunks[1].start_time == 300


def test_chunked_analyzer_execution(tmp_path, mock_gemini_response):
    """ChunkedVideoAnalyzerの実行確認（モックAPIレスポンス）"""
    # 実在するダミーファイルを作成
    video_path = tmp_path / "test_video.mp4"
    video_path.write_bytes(b"\x00" * 100)

    analyzer = ChunkedVideoAnalyzer(api_keys=["test_api_key"])

    mock_client = MagicMock()
    mock_file = MagicMock()
    mock_file.name = "test_file"
    mock_file.state = "ACTIVE"
    mock_client.models.list.return_value = iter([])
    mock_client.files.upload.return_value = mock_file
    mock_client.files.get.return_value = mock_file

    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_gemini_response, ensure_ascii=False)
    mock_client.models.generate_content.return_value = mock_response

    analyzer._client = mock_client

    chunk = ChunkInfo(chunk_id=0, start_time=0, end_time=300, duration=300, video_path=str(video_path))
    result = analyzer.analyze_chunk(chunk)

    assert result is not None
    assert result.get("status") == "success"
    assert "overall_risk_score" in result
    assert result["chunk_id"] == 0


def test_chunk_integrator_integration(mock_gemini_response):
    """ChunkIntegratorの統合確認"""
    chunk_results = [
        {
            "chunk_id": 0,
            "chunk_time_range": {"start": 0, "end": 300},
            "status": "success",
            **mock_gemini_response,
        },
        {
            "chunk_id": 1,
            "chunk_time_range": {"start": 300, "end": 600},
            "status": "success",
            **{**mock_gemini_response, "overall_risk_score": 90},
        }
    ]

    integrator = ChunkIntegrator()
    integrated_result = integrator.integrate_chunks(chunk_results)

    assert integrated_result is not None
    assert "overall_risk_score" in integrated_result
    assert "evaluation" in integrated_result
    assert isinstance(integrated_result["overall_risk_score"], (int, float))


def test_result_json_generation(mock_gemini_response):
    """結果JSONの生成確認"""
    import tempfile

    chunk_results = [
        {
            "chunk_id": 0,
            "chunk_time_range": {"start": 0, "end": 300},
            "status": "success",
            **mock_gemini_response,
        }
    ]

    integrator = ChunkIntegrator()
    integrated_result = integrator.integrate_chunks(chunk_results)

    # JSONファイルに保存（Windows対応: encoding='utf-8'を明示）
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(integrated_result, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    temp_file = Path(temp_path)
    assert temp_file.exists()

    with open(temp_file, 'r', encoding='utf-8') as f:
        loaded_result = json.load(f)

    assert loaded_result == integrated_result
    assert "overall_risk_score" in loaded_result

    temp_file.unlink()


def test_end_to_end_flow(tmp_path, mock_gemini_response):
    """エンドツーエンドの統合フロー: 解析→統合→結果検証"""
    # 実在するダミーファイルを作成
    video_path = tmp_path / "test_video.mp4"
    video_path.write_bytes(b"\x00" * 100)

    analyzer = ChunkedVideoAnalyzer(api_keys=["test_api_key"])

    mock_client = MagicMock()
    mock_file = MagicMock()
    mock_file.name = "test_file"
    mock_file.state = "ACTIVE"
    mock_client.models.list.return_value = iter([])
    mock_client.files.upload.return_value = mock_file
    mock_client.files.get.return_value = mock_file

    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_gemini_response, ensure_ascii=False)
    mock_client.models.generate_content.return_value = mock_response

    analyzer._client = mock_client

    # 2チャンクを解析（実在ファイルを使用）
    chunks = [
        ChunkInfo(chunk_id=0, start_time=0, end_time=300, duration=300, video_path=str(video_path)),
        ChunkInfo(chunk_id=1, start_time=300, end_time=600, duration=300, video_path=str(video_path)),
    ]
    chunk_results = analyzer.analyze_chunks(chunks, parallel=False)

    assert len(chunk_results) == 2
    assert all(r.get("status") == "success" for r in chunk_results)

    # ChunkIntegratorで統合
    integrator = ChunkIntegrator()
    integrated_result = integrator.integrate_chunks(chunk_results)

    assert integrated_result is not None
    assert "overall_risk_score" in integrated_result
    assert "evaluation" in integrated_result
    assert "chunk_analysis" in integrated_result
    assert integrated_result["chunk_analysis"]["num_chunks"] == 2
    assert integrated_result["chunk_analysis"]["num_successful"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
