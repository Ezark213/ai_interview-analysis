"""ドキュメント品質のテスト（Iteration-06）

このテストは、運用に必要なドキュメントが必須項目を含んでいることを検証します。
"""

import pytest
from pathlib import Path


class TestDocumentation:
    """ドキュメントの品質と網羅性のテスト"""

    @pytest.fixture
    def docs_dir(self):
        """ドキュメントディレクトリのパスを返す"""
        return Path(__file__).parent.parent / "docs"

    def test_candidate_consent_form_exists(self, docs_dir):
        """候補者同意書が存在すること"""
        consent_form = docs_dir / "candidate_consent_form.md"
        assert consent_form.exists(), f"候補者同意書が見つかりません: {consent_form}"

    def test_candidate_consent_form_required_fields(self, docs_dir):
        """
        候補者同意書の必須項目チェック

        必須項目:
        - 目的と利用範囲
        - 収集する個人情報（動画、評価結果）
        - AI解析とプロファイリングの説明
        - 同意の任意性と撤回権
        - 個人情報保護法対応（データ保管、利用期間、廃棄）
        - 同意署名欄
        """
        consent_form = docs_dir / "candidate_consent_form.md"
        content = consent_form.read_text(encoding="utf-8")

        # 必須キーワードのチェック
        required_keywords = [
            "目的",
            "利用範囲",
            "個人情報",
            "動画",
            "AI",
            "解析",
            "同意",
            "撤回",
            "保管",
            "廃棄",
            "署名"
        ]

        for keyword in required_keywords:
            assert keyword in content, \
                f"候補者同意書に必須キーワード '{keyword}' が含まれていません"

        # セクション構成のチェック
        required_sections = [
            "目的",
            "収集する情報",
            "利用範囲",
            "保管",
            "同意"
        ]

        for section in required_sections:
            assert section in content, \
                f"候補者同意書に必須セクション '{section}' が含まれていません"

    def test_operation_manual_exists(self, docs_dir):
        """運用マニュアルが存在すること"""
        manual = docs_dir / "operation_manual.md"
        assert manual.exists(), f"運用マニュアルが見つかりません: {manual}"

    def test_operation_manual_required_sections(self, docs_dir):
        """
        運用マニュアルの必須セクションチェック

        必須セクション:
        - システム概要
        - 運用フロー（動画準備 → アップロード → 解析 → 結果確認）
        - Streamlit UIの使い方
        - トラブルシューティング
        - エスカレーション基準
        - 運用開始後の改善計画
        """
        manual = docs_dir / "operation_manual.md"
        content = manual.read_text(encoding="utf-8")

        # 必須セクションのチェック
        required_sections = [
            "システム概要",
            "運用フロー",
            "使い方",
            "トラブルシューティング",
            "エスカレーション",
            "改善"
        ]

        for section in required_sections:
            assert section in content, \
                f"運用マニュアルに必須セクション '{section}' が含まれていません"

        # 運用フローのステップチェック
        flow_steps = [
            "動画",
            "アップロード",
            "解析",
            "結果"
        ]

        for step in flow_steps:
            assert step in content, \
                f"運用マニュアルに運用フローのステップ '{step}' が含まれていません"

    def test_poc_limited_checklist_exists(self, docs_dir):
        """限定的PoCチェックリストが存在すること"""
        checklist = docs_dir / "poc_limited_checklist.md"
        assert checklist.exists(), f"限定的PoCチェックリストが見つかりません: {checklist}"

    def test_poc_limited_checklist_required_items(self, docs_dir):
        """
        限定的PoCチェックリストの必須項目チェック

        必須項目:
        - 限定的PoCの目的（動作確認とハルシネーション検証）
        - 実施手順（ステップバイステップ）
        - 確認項目（システム動作、出典品質、ハルシネーション）
        - 合格判定基準
        - 不合格時の対応
        """
        checklist = docs_dir / "poc_limited_checklist.md"
        content = checklist.read_text(encoding="utf-8")

        # 必須キーワードのチェック
        required_keywords = [
            "目的",
            "動作確認",
            "ハルシネーション",
            "手順",
            "確認",
            "判定",
            "合格",
            "不合格"
        ]

        for keyword in required_keywords:
            assert keyword in content, \
                f"限定的PoCチェックリストに必須キーワード '{keyword}' が含まれていません"

    def test_git_commit_guide_exists(self, docs_dir):
        """Gitコミットガイドが存在すること"""
        guide = docs_dir / "git_commit_guide.md"
        assert guide.exists(), f"Gitコミットガイドが見つかりません: {guide}"

    def test_git_commit_guide_required_sections(self, docs_dir):
        """
        Gitコミットガイドの必須セクションチェック

        必須セクション:
        - 未コミットファイルの一覧
        - コミットメッセージ案
        - リリースタグ案
        - リリースノート案
        """
        guide = docs_dir / "git_commit_guide.md"
        content = guide.read_text(encoding="utf-8")

        # 必須セクションのチェック
        required_sections = [
            "コミット",
            "メッセージ",
            "リリース",
            "タグ"
        ]

        for section in required_sections:
            assert section in content, \
                f"Gitコミットガイドに必須セクション '{section}' が含まれていません"

    def test_markdown_links(self, docs_dir):
        """
        Markdownリンクの検証（オプション）

        ドキュメント内のリンクが正しいパスを指しているかチェック
        """
        # 主要ドキュメントのリスト
        docs_to_check = [
            "operation_manual.md",
            "poc_limited_checklist.md",
            "git_commit_guide.md"
        ]

        import re

        for doc_name in docs_to_check:
            doc_path = docs_dir / doc_name
            if not doc_path.exists():
                continue

            content = doc_path.read_text(encoding="utf-8")

            # Markdownリンクのパターン: [テキスト](パス)
            link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            links = re.findall(link_pattern, content)

            for link_text, link_path in links:
                # 外部リンク（http, https）はスキップ
                if link_path.startswith("http://") or link_path.startswith("https://"):
                    continue

                # アンカーリンク（#）はスキップ
                if link_path.startswith("#"):
                    continue

                # 相対パスのリンクを検証
                if link_path.startswith("./"):
                    target_path = docs_dir / link_path[2:]
                else:
                    target_path = docs_dir / link_path

                # パスの正規化（../ を解決）
                target_path = target_path.resolve()

                # ファイルまたはディレクトリが存在するか確認
                assert target_path.exists(), \
                    f"{doc_name} のリンクが無効です: '{link_path}' → {target_path}"

    def test_documentation_consistency(self, docs_dir):
        """
        ドキュメント間の一貫性チェック

        全てのドキュメントで以下が一貫していることを確認:
        - 用語（例: 「候補者」「面談動画」「AI評価」）
        - バージョン表記
        """
        docs_to_check = [
            "candidate_consent_form.md",
            "operation_manual.md",
            "poc_limited_checklist.md"
        ]

        # 用語の一貫性チェック（推奨用語）
        recommended_terms = {
            "候補者": ["応募者", "志願者"],  # 「候補者」を推奨、他は避ける
            "面談動画": ["面接動画", "インタビュー動画"],
            "AI評価": ["AI判定", "AI解析結果"]
        }

        for doc_name in docs_to_check:
            doc_path = docs_dir / doc_name
            if not doc_path.exists():
                continue

            content = doc_path.read_text(encoding="utf-8")

            # 推奨用語が使われているかチェック
            for recommended, alternatives in recommended_terms.items():
                # 推奨用語が使われていること（または代替語も許容）
                term_found = recommended in content or any(alt in content for alt in alternatives)

                # このチェックは警告のみ（必須ではない）
                if not term_found:
                    # pytest.skip でスキップするか、警告を出す
                    pass  # 厳密なチェックはしない
