"""ナレッジローダーのテスト"""
import os
import pytest
import sys
from pathlib import Path
from src.knowledge_loader import load_knowledge_base

# プロジェクトルート
project_root = Path(__file__).parent.parent


class TestKnowledgeLoader:
    """ナレッジベース読み込み機能のテスト"""

    def test_load_knowledge_from_directory(self, tmp_path):
        """正常系: knowledge-base/内の.mdを読み込み、テキストが返ること"""
        # テスト用のknowledge-baseディレクトリを作成
        kb_dir = tmp_path / "knowledge-base"
        kb_dir.mkdir()

        # テスト用のMarkdownファイルを作成
        file1 = kb_dir / "criteria1.md"
        file1.write_text("# 評価基準1\n内容1", encoding="utf-8")

        file2 = kb_dir / "criteria2.md"
        file2.write_text("# 評価基準2\n内容2", encoding="utf-8")

        # 実行
        result = load_knowledge_base(str(kb_dir))

        # 検証
        assert "評価基準1" in result
        assert "評価基準2" in result
        assert "内容1" in result
        assert "内容2" in result

    def test_load_knowledge_empty_directory(self, tmp_path):
        """空ディレクトリの場合、空文字列+警告"""
        # 空のディレクトリを作成
        kb_dir = tmp_path / "empty-knowledge"
        kb_dir.mkdir()

        # 実行
        result = load_knowledge_base(str(kb_dir))

        # 検証: 空文字列が返ること
        assert result == ""

    def test_load_knowledge_nonexistent_directory(self):
        """存在しないディレクトリでFileNotFoundError"""
        nonexistent_dir = "/nonexistent/directory/path"

        # 実行と検証
        with pytest.raises(FileNotFoundError):
            load_knowledge_base(nonexistent_dir)

    def test_load_knowledge_with_non_md_files(self, tmp_path):
        """.md以外のファイルは無視されること"""
        kb_dir = tmp_path / "knowledge-base"
        kb_dir.mkdir()

        # .mdファイル
        md_file = kb_dir / "valid.md"
        md_file.write_text("# 有効な内容", encoding="utf-8")

        # .txtファイル（無視されるべき）
        txt_file = kb_dir / "invalid.txt"
        txt_file.write_text("無効な内容", encoding="utf-8")

        # 実行
        result = load_knowledge_base(str(kb_dir))

        # 検証: .mdのみが含まれること
        assert "有効な内容" in result
        assert "無効な内容" not in result


class TestProjectKnowledgeBase:
    """プロジェクトの実際の知識ベース読み込みテスト（Iteration-07-bugfix）"""

    def test_knowledge_base_directory_exists(self):
        """知識ベースディレクトリが存在することを確認"""
        kb_dir = project_root / "knowledge-base"
        assert kb_dir.exists(), f"Knowledge base directory not found: {kb_dir}"
        assert kb_dir.is_dir(), f"Knowledge base path is not a directory: {kb_dir}"

    def test_core_criteria_file_exists(self):
        """core-criteria.mdファイルが存在することを確認"""
        core_criteria = project_root / "knowledge-base" / "core-criteria.md"
        assert core_criteria.exists(), f"core-criteria.md not found: {core_criteria}"
        assert core_criteria.is_file(), f"core-criteria.md is not a file: {core_criteria}"

    def test_load_project_knowledge_base(self):
        """プロジェクトの知識ベースが正しく読み込めることを確認"""
        # プロジェクトルートからの絶対パスで指定
        kb_dir = project_root / "knowledge-base"
        knowledge_base = load_knowledge_base(str(kb_dir))

        # 空でないことを確認
        assert knowledge_base is not None, "Knowledge base is None"
        assert len(knowledge_base) > 0, "Knowledge base is empty"

        # 最低限の内容が含まれていることを確認（例: "評価基準"等のキーワード）
        assert "評価" in knowledge_base or "基準" in knowledge_base, \
            "Knowledge base does not contain expected content"

    # ===== Iteration-01: 論文ベース知識統合テスト =====

    def test_research_directory_exists(self):
        """research/ディレクトリが存在することを確認"""
        research_dir = project_root / "knowledge-base" / "research"
        assert research_dir.exists(), "knowledge-base/research/ が存在しません"

    def test_research_files_loadable(self):
        """5つの論文MDファイルが読み込めることを確認"""
        from src.knowledge_loader import load_research_knowledge
        content = load_research_knowledge()
        assert "認知的負荷" in content
        assert "微表情" in content
        assert "CWB" in content
        assert "レッドフラグ" in content
        assert "スコアリング" in content

    def test_research_knowledge_contains_all_files(self):
        """5本分のキーワードが結合結果に存在することを検証"""
        from src.knowledge_loader import load_research_knowledge
        content = load_research_knowledge()
        # 各ファイルの代表キーワードを確認
        assert "非言語" in content        # 01_nonverbal_risk_checklist
        assert "認知的負荷" in content    # 02_cognitive_load_signs
        assert "CWB" in content           # 03_cwb_risk_profile
        assert "微表情" in content        # 04_micro_expression_guide
        assert "スコアリング" in content  # 05_integrated_scoring_rubric

    def test_research_knowledge_file_count(self):
        """research/ディレクトリのMDファイル数が5であることを検証"""
        research_dir = project_root / "knowledge-base" / "research"
        md_files = list(research_dir.glob("*.md"))
        assert len(md_files) == 5, f"Expected 5 files, got {len(md_files)}: {[f.name for f in md_files]}"

    def test_research_knowledge_empty_dir_returns_empty_string(self, tmp_path):
        """research/が空ディレクトリの場合、空文字列を返すことを検証"""
        import importlib
        import src.knowledge_loader as kl
        # _PROJECT_ROOTをtmp_pathに差し替えて空research/を作成
        (tmp_path / "knowledge-base" / "research").mkdir(parents=True)
        original_root = kl._PROJECT_ROOT
        kl._PROJECT_ROOT = tmp_path
        try:
            result = kl.load_research_knowledge()
            assert result == "", f"Expected empty string for empty dir, got: {result!r}"
        finally:
            kl._PROJECT_ROOT = original_root

    def test_core_criteria_includes_research_supplement(self):
        """core-criteria.mdに論文ベース評価補足が含まれることを確認"""
        core_criteria = project_root / "knowledge-base" / "core-criteria.md"
        content = core_criteria.read_text(encoding="utf-8")
        assert "論文ベース評価補足" in content
        assert "認知的負荷" in content
        assert "Immediacy" in content

    def test_load_knowledge_base_from_src_directory(self):
        """srcディレクトリから実行した場合でも正しく読み込めることを確認"""
        # カレントディレクトリをsrcに変更
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root / "src")

            # デフォルト引数でload_knowledge_base()を呼び出す
            # これが失敗する = パス解決の問題
            knowledge_base = load_knowledge_base()

            # 正しく読み込めることを確認
            assert knowledge_base is not None, "Knowledge base is None"
            assert len(knowledge_base) > 0, "Knowledge base is empty"
            assert "評価" in knowledge_base or "基準" in knowledge_base
        finally:
            # カレントディレクトリを元に戻す
            os.chdir(original_cwd)
