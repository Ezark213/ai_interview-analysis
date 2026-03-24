"""プロンプトビルダーのテスト"""
import pytest
from src.prompt_builder import build_prompt


class TestPromptBuilder:
    """プロンプト構築機能のテスト"""

    def test_build_prompt_with_knowledge(self):
        """ナレッジが埋め込まれたプロンプトが生成されること"""
        knowledge_text = "# テスト評価基準\n- 観察項目1\n- 観察項目2"

        # 実行
        result = build_prompt(knowledge_text)

        # 検証: ナレッジベースが含まれていること
        assert "テスト評価基準" in result
        assert "観察項目1" in result
        assert "観察項目2" in result

    def test_build_prompt_empty_knowledge(self):
        """空ナレッジでもデフォルトプロンプトが生成されること"""
        # 実行
        result = build_prompt("")

        # 検証: 空でもプロンプトが返ること
        assert result != ""
        assert len(result) > 0

    def test_prompt_contains_required_sections(self):
        """出力形式指定・バイアス防止指示が含まれること"""
        knowledge_text = "テストナレッジ"

        # 実行
        result = build_prompt(knowledge_text)

        # 検証: 重要なセクションが含まれていること
        # 役割定義
        assert "面談評価" in result or "評価アシスタント" in result or "行動心理学" in result

        # バイアス防止
        assert "バイアス" in result or "文化" in result or "性別" in result or "観察" in result

        # 出力形式指定（JSON関連）
        assert "JSON" in result or "json" in result or "出力" in result

    def test_prompt_contains_output_schema(self):
        """JSONスキーマが含まれていること"""
        knowledge_text = "テストナレッジ"

        # 実行
        result = build_prompt(knowledge_text)

        # 検証: 必須フィールドがスキーマに含まれること
        assert "overall_risk_score" in result
        assert "evaluation" in result
        assert "communication" in result
        assert "stress_tolerance" in result
        assert "reliability" in result
        assert "teamwork" in result

    def test_prompt_structure_is_consistent(self):
        """プロンプトの構造が一貫していること"""
        knowledge1 = "ナレッジ1"
        knowledge2 = "ナレッジ2"

        # 実行
        result1 = build_prompt(knowledge1)
        result2 = build_prompt(knowledge2)

        # 検証: ナレッジ部分以外は同じ構造であること
        # （ナレッジが異なっても、テンプレート部分は同じ）
        assert result1.replace("ナレッジ1", "X") == result2.replace("ナレッジ2", "X")


class TestPromptBuilderWithTranscript:
    """文字起こしテキスト付きプロンプト構築のテスト（Iteration-09追加）"""

    def test_build_prompt_with_transcript(self):
        """文字起こしテキスト付きプロンプトが正しく構築される"""
        knowledge_text = "テスト評価基準"
        transcript_text = "[0.0s] はい、前職ではプロジェクトリーダーでした。\n[3.5s] 5名のチームを管理していました。"

        result = build_prompt(knowledge_text, transcript=transcript_text)

        # ナレッジベースが含まれること
        assert "テスト評価基準" in result
        # 文字起こしテキストが含まれること
        assert "プロジェクトリーダー" in result
        assert "5名のチーム" in result
        # マルチモーダル解析の指示が含まれること
        assert "照合" in result or "言行一致" in result

    def test_build_prompt_without_transcript(self):
        """文字起こしなしでも従来通り動作する（後方互換性）"""
        knowledge_text = "テスト評価基準"

        result = build_prompt(knowledge_text, transcript=None)

        # ナレッジベースが含まれること
        assert "テスト評価基準" in result
        # プロンプトが正常に生成されること
        assert len(result) > 0
        # 文字起こしセクションのヘッダーが含まれないこと
        assert "文字起こしテキスト" not in result
