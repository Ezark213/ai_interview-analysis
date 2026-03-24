"""カスタムナレッジベースのテスト

プリセット選択・カスタムアップロード・組み合わせ機能のテスト。
テスト対象:
- knowledge_loader.py: list_presets(), load_preset(), load_custom_knowledge(), load_combined_knowledge()
"""
import pytest
from pathlib import Path


class TestKnowledgePresets:
    """ナレッジベースプリセット機能のテスト"""

    def test_list_available_presets(self):
        """プリセット一覧が取得できる（最低3種類）"""
        from src.knowledge_loader import list_presets

        presets = list_presets()

        assert isinstance(presets, list)
        assert len(presets) >= 3

        # 各プリセットに必須フィールドがあること
        for preset in presets:
            assert "id" in preset
            assert "name" in preset
            assert "description" in preset

    def test_load_ses_preset(self):
        """SES面談プリセットが読み込める"""
        from src.knowledge_loader import load_preset

        content = load_preset("ses_interview")

        assert isinstance(content, str)
        assert len(content) > 0
        # SES特有のキーワードが含まれること
        assert "SES" in content or "客先常駐" in content or "面談" in content

    def test_load_general_preset(self):
        """一般採用プリセットが読み込める"""
        from src.knowledge_loader import load_preset

        content = load_preset("general_hiring")

        assert isinstance(content, str)
        assert len(content) > 0
        # 一般採用特有のキーワードが含まれること
        assert "採用" in content or "志望動機" in content or "組織" in content

    def test_load_technical_preset(self):
        """技術面接プリセットが読み込める"""
        from src.knowledge_loader import load_preset

        content = load_preset("technical_interview")

        assert isinstance(content, str)
        assert len(content) > 0
        # 技術面接特有のキーワードが含まれること
        assert "技術" in content or "問題解決" in content or "論理" in content

    def test_load_custom_markdown(self):
        """ユーザーがアップロードした.mdを評価基準として読み込める"""
        from src.knowledge_loader import load_custom_knowledge

        custom_md = """# カスタム評価基準

## 評価項目
- 創造性
- チームワーク

## ポジティブシグナル
- 独自のアイデアを提案する
"""
        result = load_custom_knowledge(custom_md)

        assert isinstance(result, str)
        assert "カスタム評価基準" in result
        assert "創造性" in result

    def test_custom_markdown_validation(self):
        """空ファイルや不正な形式でエラーになる"""
        from src.knowledge_loader import load_custom_knowledge

        # 空文字列
        with pytest.raises(ValueError):
            load_custom_knowledge("")

        # 空白のみ
        with pytest.raises(ValueError):
            load_custom_knowledge("   \n  \n  ")

    def test_load_preset_invalid_id_raises_error(self):
        """存在しないプリセットIDでValueErrorになる（レビュー指摘#2対応）"""
        from src.knowledge_loader import load_preset

        with pytest.raises(ValueError):
            load_preset("nonexistent")

    def test_combined_knowledge_default_fallback(self):
        """両方None時にデフォルト基準(core-criteria.md)が読み込まれる（レビュー指摘#3対応）"""
        from src.knowledge_loader import load_combined_knowledge

        result = load_combined_knowledge(preset_id=None, custom_content=None)

        assert isinstance(result, str)
        assert len(result) > 0
        # core-criteria.mdの内容が含まれること
        assert "面談評価ナレッジベース" in result or "行動心理学" in result

    def test_preset_combined_with_custom(self):
        """プリセット+カスタムの両方を組み合わせられる"""
        from src.knowledge_loader import load_combined_knowledge

        custom_md = """# 追加評価基準
## 独自項目
- リーダーシップの発揮
"""
        result = load_combined_knowledge(
            preset_id="ses_interview",
            custom_content=custom_md
        )

        assert isinstance(result, str)
        # プリセットの内容が含まれること
        assert "SES" in result or "客先常駐" in result or "面談" in result
        # カスタムの内容も含まれること
        assert "追加評価基準" in result
        assert "リーダーシップ" in result
