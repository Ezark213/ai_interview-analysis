"""Whisper統合パイプラインのテスト

WhisperTranscriber自体はモック化し、統合パイプライン
（文字起こし→プロンプト→解析）の接続をテストする。

テスト対象:
- analyzer.py: transcript引数の受け入れ
- prompt_builder.py: transcript引数によるプロンプト構築
- chunked_analyzer.py: extract_transcript_for_chunk()
- config.py: OpenAI APIキーの3番目の戻り値
"""
import inspect
import os
import pytest
from unittest.mock import patch, MagicMock


# テスト用のモックtranscript
MOCK_TRANSCRIPT = {
    "text": "はい、前職ではプロジェクトリーダーとして5名のチームを管理していました。",
    "segments": [
        {"start": 0.0, "end": 3.5, "text": "はい、前職では"},
        {"start": 3.5, "end": 8.2, "text": "プロジェクトリーダーとして5名のチームを管理していました。"},
        {"start": 10.0, "end": 15.0, "text": "具体的には、要件定義からテストまで担当しました。"},
        {"start": 60.0, "end": 65.0, "text": "チーム間のコミュニケーションを重視していました。"},
        {"start": 120.0, "end": 125.0, "text": "困難な状況でも冷静に対応するよう心がけていました。"},
    ]
}


class TestWhisperIntegration:
    """Whisper統合パイプラインのテスト"""

    def test_analyzer_accepts_transcript_param(self):
        """VideoAnalyzer.analyze()がtranscriptパラメータを受け取れる"""
        from src.analyzer import VideoAnalyzer
        sig = inspect.signature(VideoAnalyzer.analyze)
        assert "transcript" in sig.parameters, \
            "analyze()にtranscriptパラメータがありません"

    def test_transcript_added_to_prompt(self):
        """文字起こしテキストがプロンプトに含まれる"""
        from src.prompt_builder import build_prompt

        transcript_text = "はい、前職ではプロジェクトリーダーとして管理していました。"
        result = build_prompt("テストナレッジ", transcript=transcript_text)

        # 文字起こしテキストがプロンプトに含まれること
        assert transcript_text in result
        # マルチモーダル解析の指示が含まれること
        assert "照合" in result or "言行一致" in result

    def test_analysis_without_whisper_still_works(self):
        """Whisper無効時も従来通り動作する（後方互換性）"""
        from src.prompt_builder import build_prompt

        # transcript=Noneで呼び出し
        result = build_prompt("テストナレッジ", transcript=None)

        # プロンプトが生成されること
        assert len(result) > 0
        # ナレッジベースが含まれること
        assert "テストナレッジ" in result
        # 文字起こしセクションが含まれないこと
        assert "文字起こしテキスト" not in result

    def test_chunked_analysis_with_transcript(self):
        """チャンク解析時に各チャンクに対応する文字起こしが渡される"""
        from src.chunked_analyzer import extract_transcript_for_chunk

        # 0〜60秒のチャンクに対応するセグメントを抽出
        chunk_transcript = extract_transcript_for_chunk(
            MOCK_TRANSCRIPT, start_time=0, end_time=60
        )

        # 0〜60秒に含まれるセグメントのみが抽出されること
        assert "前職では" in chunk_transcript
        assert "プロジェクトリーダー" in chunk_transcript
        assert "要件定義" in chunk_transcript
        # 60秒以降のセグメントは含まれないこと
        assert "コミュニケーション" not in chunk_transcript
        assert "冷静に対応" not in chunk_transcript

    def test_openai_key_missing_returns_empty_string(self):
        """OpenAI APIキーが未設定の場合、3番目の戻り値が空文字列"""
        from src.config import load_api_keys

        with patch("src.config.load_dotenv"), \
             patch.dict(os.environ, {
                 "GEMINI_API_KEY_1": "gem-key-1",
                 "GEMINI_API_KEY_2": "gem-key-2",
             }, clear=True):
            result = load_api_keys()

        # 3要素のタプルが返ること
        assert len(result) == 3, \
            f"load_api_keys()は3要素を返すべき（実際: {len(result)}要素）"
        # 3番目の要素（openai_key）が空文字列
        assert result[2] == ""


class TestExtractTranscriptEdgeCases:
    """extract_transcript_for_chunk()のエッジケーステスト（レビュー指摘#2対応）"""

    def test_none_transcript_returns_empty_string(self):
        """full_transcript=Noneの場合、空文字列を返す"""
        from src.chunked_analyzer import extract_transcript_for_chunk

        result = extract_transcript_for_chunk(None, start_time=0, end_time=60)
        assert result == ""

    def test_empty_segments_returns_empty_string(self):
        """full_transcript={"segments": []}の場合、空文字列を返す"""
        from src.chunked_analyzer import extract_transcript_for_chunk

        result = extract_transcript_for_chunk(
            {"text": "", "segments": []}, start_time=0, end_time=60
        )
        assert result == ""

    def test_boundary_crossing_segment_excluded(self):
        """境界にまたがるセグメント（start=55, end=65）がchunk end_time=60で除外される"""
        from src.chunked_analyzer import extract_transcript_for_chunk

        transcript = {
            "text": "test",
            "segments": [
                {"start": 10.0, "end": 20.0, "text": "含まれるべき"},
                {"start": 55.0, "end": 65.0, "text": "境界またぎ除外"},
                {"start": 70.0, "end": 80.0, "text": "範囲外除外"},
            ]
        }
        result = extract_transcript_for_chunk(transcript, start_time=0, end_time=60)

        assert "含まれるべき" in result
        assert "境界またぎ除外" not in result
        assert "範囲外除外" not in result
