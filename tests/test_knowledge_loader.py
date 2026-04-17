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


# ===== Iteration-02: 研究知識スコアリング統合テスト =====

class TestIteration02ResearchIntegration:
    """Iteration-02: 研究知識をスコアリングに統合するためのテスト"""

    def test_load_combined_knowledge_includes_research(self):
        """load_combined_knowledge がresearchファイルの内容を含むこと"""
        from src.knowledge_loader import load_combined_knowledge
        result = load_combined_knowledge(preset_id="ses_interview")
        # research/05_integrated_scoring_rubric.md の冒頭テキストが含まれること
        assert "統合評価スコアリングルーブリック" in result or "Axis 1" in result

    def test_system_prompt_has_weight_instruction(self):
        """system.txt がウェイト指示を含むこと"""
        system_txt = (project_root / "src" / "prompts" / "system.txt").read_text(encoding="utf-8")
        assert "70%" in system_txt or "研究ベース" in system_txt

    def test_default_score_is_50(self):
        """system.txt のデフォルトスコアが50点であること（厳格化）"""
        system_txt = (project_root / "src" / "prompts" / "system.txt").read_text(encoding="utf-8")
        assert "デフォルト" in system_txt and "50点" in system_txt


# ===== Iteration-02: save_reference_doc / load_reference_docs カバレッジ向上 =====

class TestReferenceDocOperations:
    """save_reference_doc と load_reference_docs の異常系・境界値テスト"""

    def test_save_reference_doc_invalid_extension(self, tmp_path):
        """.md以外の拡張子でValueError"""
        import src.knowledge_loader as kl
        original = kl._REFERENCE_DIR
        kl._REFERENCE_DIR = tmp_path / "reference"
        try:
            with pytest.raises(ValueError, match=".md"):
                kl.save_reference_doc("test.txt", "some content")
        finally:
            kl._REFERENCE_DIR = original

    def test_save_reference_doc_empty_content(self, tmp_path):
        """空コンテンツでValueError"""
        import src.knowledge_loader as kl
        original = kl._REFERENCE_DIR
        kl._REFERENCE_DIR = tmp_path / "reference"
        try:
            with pytest.raises(ValueError):
                kl.save_reference_doc("test.md", "")
            with pytest.raises(ValueError):
                kl.save_reference_doc("test.md", "   \n  ")
        finally:
            kl._REFERENCE_DIR = original

    def test_save_reference_doc_creates_file(self, tmp_path):
        """正常系: ファイルが保存されパスが返る"""
        import src.knowledge_loader as kl
        original = kl._REFERENCE_DIR
        kl._REFERENCE_DIR = tmp_path / "reference"
        try:
            path = kl.save_reference_doc("doc.md", "# テスト\n内容")
            assert Path(path).exists()
            assert Path(path).read_text(encoding="utf-8") == "# テスト\n内容"
        finally:
            kl._REFERENCE_DIR = original

    def test_load_reference_docs_empty_dir(self, tmp_path):
        """reference/ が空の場合、空リストを返す"""
        import src.knowledge_loader as kl
        original = kl._REFERENCE_DIR
        ref_dir = tmp_path / "reference"
        ref_dir.mkdir()
        kl._REFERENCE_DIR = ref_dir
        try:
            result = kl.load_reference_docs()
            assert result == []
        finally:
            kl._REFERENCE_DIR = original

    def test_load_reference_docs_nonexistent_dir(self, tmp_path):
        """reference/ が存在しない場合、空リストを返す"""
        import src.knowledge_loader as kl
        original = kl._REFERENCE_DIR
        kl._REFERENCE_DIR = tmp_path / "nonexistent"
        try:
            result = kl.load_reference_docs()
            assert result == []
        finally:
            kl._REFERENCE_DIR = original

    def test_load_reference_docs_returns_correct_structure(self, tmp_path):
        """ファイルがある場合、filename/path/content を持つ辞書リストを返す"""
        import src.knowledge_loader as kl
        original = kl._REFERENCE_DIR
        ref_dir = tmp_path / "reference"
        ref_dir.mkdir()
        (ref_dir / "sample.md").write_text("# サンプル", encoding="utf-8")
        kl._REFERENCE_DIR = ref_dir
        try:
            result = kl.load_reference_docs()
            assert len(result) == 1
            assert result[0]["filename"] == "sample.md"
            assert "# サンプル" in result[0]["content"]
            assert "path" in result[0]
        finally:
            kl._REFERENCE_DIR = original

    def test_load_preset_file_not_found(self, tmp_path):
        """プリセットIDは有効だがファイルが存在しない場合 FileNotFoundError"""
        import src.knowledge_loader as kl
        original = kl._PRESETS_DIR
        (tmp_path / "presets").mkdir()
        kl._PRESETS_DIR = tmp_path / "presets"  # ファイルなしの空ディレクトリ
        try:
            with pytest.raises(FileNotFoundError):
                kl.load_preset("ses_interview")  # IDは有効だがファイルなし
        finally:
            kl._PRESETS_DIR = original


# ===== Iteration-03: 統合知識の量・構造検証テスト =====

class TestIteration03KnowledgeIntegrity:
    """Iteration-03: 統合後ナレッジの量・6軸構造の整合性検証"""

    def test_combined_knowledge_word_count(self):
        """研究統合後のナレッジが十分な量を持つこと（5000文字以上）"""
        from src.knowledge_loader import load_combined_knowledge
        result = load_combined_knowledge(preset_id="ses_interview")
        assert len(result) >= 5000

    def test_research_axes_in_knowledge(self):
        """研究6軸（Axis 1〜6）が全てナレッジに含まれること"""
        from src.knowledge_loader import load_combined_knowledge
        result = load_combined_knowledge(preset_id="ses_interview")
        for axis in ["Axis 1", "Axis 2", "Axis 3", "Axis 4", "Axis 5", "Axis 6"]:
            assert axis in result, f"{axis}がナレッジに含まれていない"
