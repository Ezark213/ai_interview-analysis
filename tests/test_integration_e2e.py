"""
統合テスト（エンドツーエンド）

動画読み込み→解析→結果生成の一連の流れをテストする。
API呼び出しはモック化して実行。
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def sample_video_path():
    """テスト用のサンプル動画パス（存在する必要はない、モックで対応）"""
    return "tests/fixtures/sample_interview.mp4"


@pytest.fixture
def mock_gemini_response():
    """モックGemini APIレスポンス"""
    return {
        "overall_risk_score": 85,
        "risk_level": "低い",
        "evaluation": {
            "communication": {
                "score": 80,
                "observations": ["明瞭な発話", "適切なアイコンタクト"],
                "confidence": "高"
            },
            "stress_tolerance": {
                "score": 85,
                "observations": ["冷静な対応", "プレッシャー下でも安定"],
                "confidence": "高"
            },
            "reliability": {
                "score": 90,
                "observations": ["具体的な実績提示", "誠実な回答"],
                "confidence": "高"
            },
            "teamwork": {
                "score": 85,
                "observations": ["協力的な姿勢", "チーム経験豊富"],
                "confidence": "高"
            }
        },
        "red_flags": [],
        "positive_signals": ["技術力が高い", "自己学習の習慣"],
        "recommendation": "優秀な候補者。アサインを推奨。",
        "disclaimer": "本評価はAIによる参考情報です。"
    }


def test_video_file_loading():
    """動画ファイルの読み込み確認"""
    # VideoChunkerが動画を認識できることを確認
    # 実際のファイルは不要（モック化）
    from src.video_chunker import VideoChunker

    # モック化してテスト
    with patch('src.video_chunker.ffmpeg.probe') as mock_probe:
        mock_probe.return_value = {
            'format': {'duration': '300.0'}
        }

        chunker = VideoChunker(chunk_duration_minutes=5)
        # 実際に動画を処理しない、インスタンス化のみ確認
        assert chunker is not None
        assert chunker.chunk_duration_minutes == 5


def test_chunked_analyzer_execution(mocker, mock_gemini_response):
    """ChunkedAnalyzerの実行確認（モックAPIレスポンス）"""
    from src.chunked_analyzer import ChunkedAnalyzer

    # Gemini API呼び出しをモック化
    mock_client = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    mock_response.text = json.dumps(mock_gemini_response)
    mock_client.models.generate_content.return_value = mock_response

    # VideoChunkerもモック化
    mock_chunks = [
        {"chunk_id": 0, "start_time": 0, "end_time": 300, "video_file": "chunk_0.mp4"}
    ]

    with patch('src.chunked_analyzer.genai.Client', return_value=mock_client):
        with patch('src.video_chunker.VideoChunker.chunk_video', return_value=mock_chunks):
            analyzer = ChunkedAnalyzer(api_key="test_api_key")

            # analyze_videoメソッドが正常に動作することを確認
            # 実際のファイルは不要
            result = analyzer.analyze_video("fake_video.mp4")

            assert result is not None
            assert "overall_risk_score" in result or "chunks" in result


def test_chunk_integrator_integration(mocker, mock_gemini_response):
    """ChunkIntegratorの統合確認"""
    from src.chunk_integrator import ChunkIntegrator

    # サンプルチャンク結果
    chunk_results = [
        {
            "chunk_id": 0,
            "analysis": mock_gemini_response
        },
        {
            "chunk_id": 1,
            "analysis": {
                **mock_gemini_response,
                "overall_risk_score": 90
            }
        }
    ]

    integrator = ChunkIntegrator()

    # 統合処理の実行
    integrated_result = integrator.integrate_chunks(chunk_results)

    # 結果の検証
    assert integrated_result is not None
    assert "overall_risk_score" in integrated_result
    assert "evaluation" in integrated_result
    assert isinstance(integrated_result["overall_risk_score"], (int, float))


def test_result_json_generation(mocker, mock_gemini_response):
    """結果JSONの生成確認"""
    from src.chunk_integrator import ChunkIntegrator
    import tempfile

    # ChunkIntegratorを使って結果を生成
    chunk_results = [
        {
            "chunk_id": 0,
            "analysis": mock_gemini_response
        }
    ]

    integrator = ChunkIntegrator()
    integrated_result = integrator.integrate_chunks(chunk_results)

    # JSONファイルに保存
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(integrated_result, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    # ファイルが生成されたことを確認
    temp_file = Path(temp_path)
    assert temp_file.exists()

    # JSONを読み込んで検証
    with open(temp_file, 'r', encoding='utf-8') as f:
        loaded_result = json.load(f)

    assert loaded_result == integrated_result
    assert "overall_risk_score" in loaded_result

    # クリーンアップ
    temp_file.unlink()


def test_end_to_end_flow(mocker, mock_gemini_response):
    """エンドツーエンドの統合フロー"""
    from src.chunked_analyzer import ChunkedAnalyzer
    from src.chunk_integrator import ChunkIntegrator

    # Gemini API呼び出しをモック化
    mock_client = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    mock_response.text = json.dumps(mock_gemini_response)
    mock_client.models.generate_content.return_value = mock_response

    # VideoChunkerもモック化
    mock_chunks = [
        {"chunk_id": 0, "start_time": 0, "end_time": 300, "video_file": "chunk_0.mp4"}
    ]

    with patch('src.chunked_analyzer.genai.Client', return_value=mock_client):
        with patch('src.video_chunker.VideoChunker.chunk_video', return_value=mock_chunks):
            # 1. 動画を解析
            analyzer = ChunkedAnalyzer(api_key="test_api_key")
            chunk_results = analyzer.analyze_video("fake_video.mp4")

            # 2. 結果を統合
            integrator = ChunkIntegrator()

            # chunk_resultsの構造を確認して適切に処理
            if isinstance(chunk_results, dict) and "chunks" in chunk_results:
                integrated_result = integrator.integrate_chunks(chunk_results["chunks"])
            elif isinstance(chunk_results, list):
                integrated_result = integrator.integrate_chunks(chunk_results)
            else:
                integrated_result = chunk_results

            # 3. 結果を検証
            assert integrated_result is not None
            assert "overall_risk_score" in integrated_result or "evaluation" in integrated_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
