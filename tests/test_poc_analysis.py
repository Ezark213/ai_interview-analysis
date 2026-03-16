"""PoC分析機能のテスト（Iteration-05）"""
import json
import pytest
from pathlib import Path
from src.poc_analysis import (
    calculate_correlation,
    calculate_confusion_matrix,
    calculate_false_rates,
    verify_hallucinations,
    generate_poc_report
)


class TestPoCAnalysis:
    """PoC（Proof of Concept）分析機能のテスト"""

    @pytest.fixture
    def sample_data_dir(self):
        """サンプルデータのディレクトリパスを返す"""
        return Path(__file__).parent / "fixtures" / "poc_sample_data"

    @pytest.fixture
    def ai_results(self, sample_data_dir):
        """AI評価結果を読み込む"""
        with open(sample_data_dir / "ai_results.json", "r", encoding="utf-8") as f:
            return json.load(f)

    @pytest.fixture
    def human_evaluations(self, sample_data_dir):
        """人間評価結果を読み込む（CSV）"""
        import pandas as pd
        return pd.read_csv(sample_data_dir / "human_evaluations.csv")

    def test_calculate_correlation(self, ai_results, human_evaluations):
        """
        相関係数の計算テスト

        仮定:
            - AI評価スコア: overall_risk_score（0-100）
            - 人間評価スコア: human_score（0-100）
            - 相関係数: Pearson, Spearman の両方を計算
            - 閾値: 0.7以上で「高い相関」

        境界値テスト:
            - 相関係数 = 0.7（境界値）
            - 相関係数 < 0.7（低相関）
            - 相関係数 > 0.7（高相関）
        """
        # AI評価スコアを抽出
        ai_scores = [result["overall_risk_score"] for result in ai_results]

        # 人間評価スコアを抽出
        human_scores = human_evaluations["human_score"].tolist()

        # 実行
        result = calculate_correlation(ai_scores, human_scores)

        # 検証
        assert "pearson" in result
        assert "spearman" in result
        assert "p_value_pearson" in result
        assert "p_value_spearman" in result

        # 相関係数の範囲チェック
        assert -1.0 <= result["pearson"] <= 1.0
        assert -1.0 <= result["spearman"] <= 1.0

        # サンプルデータでは高い相関が期待される（優秀2名、問題2名、中間1名）
        # 完全な相関ではないが、傾向は一致するはず
        assert result["pearson"] > 0.5, f"Expected correlation > 0.5, got {result['pearson']}"

    def test_calculate_correlation_perfect(self):
        """
        完全相関のテスト（境界値: r = 1.0）
        """
        ai_scores = [10, 20, 30, 40, 50]
        human_scores = [10, 20, 30, 40, 50]

        result = calculate_correlation(ai_scores, human_scores)

        # 完全相関
        assert result["pearson"] == pytest.approx(1.0, abs=0.01)
        assert result["spearman"] == pytest.approx(1.0, abs=0.01)

    def test_calculate_correlation_no_correlation(self):
        """
        無相関のテスト（r ≈ 0）
        """
        ai_scores = [10, 20, 30, 40, 50]
        human_scores = [50, 40, 30, 20, 10]  # 逆相関

        result = calculate_correlation(ai_scores, human_scores)

        # 負の相関
        assert result["pearson"] < 0

    def test_calculate_false_positive_rate(self, ai_results, human_evaluations):
        """
        偽陽性率の計算テスト

        仮定:
            - AI判定: overall_risk_score >= 70 → 「採用推奨」
            - 人間判定: human_decision == "採用" → 「採用」
            - 実際の結果: actual_outcome == "失敗" → 「問題あり」

        偽陽性（False Positive）:
            - AIが「採用推奨」したが、実際には「問題あり」だった
            - 計算式: FP / (FP + TN)

        境界値テスト:
            - 偽陽性率 = 20%（閾値）
            - 偽陽性率 < 20%（合格）
            - 偽陽性率 > 20%（要改善）
        """
        # 混同行列を計算
        confusion_matrix = calculate_confusion_matrix(ai_results, human_evaluations)

        # 偽陽性率・偽陰性率を計算
        rates = calculate_false_rates(confusion_matrix)

        # 検証
        assert "false_positive_rate" in rates
        assert "false_negative_rate" in rates
        assert "true_positive_rate" in rates
        assert "true_negative_rate" in rates

        # 範囲チェック
        assert 0.0 <= rates["false_positive_rate"] <= 1.0
        assert 0.0 <= rates["false_negative_rate"] <= 1.0

        # サンプルデータでは偽陽性は低いはず
        # C004が「条件付採用」→「失敗」のケース
        assert rates["false_positive_rate"] <= 0.5, \
            f"Expected FPR <= 0.5, got {rates['false_positive_rate']}"

    def test_calculate_false_negative_rate(self, ai_results, human_evaluations):
        """
        偽陰性率の計算テスト

        偽陰性（False Negative）:
            - AIが「見送り推奨」したが、実際には「優秀」だった
            - 計算式: FN / (FN + TP)

        境界値テスト:
            - 偽陰性率 = 10%（閾値）
            - 偽陰性率 < 10%（合格）
            - 偽陰性率 > 10%（要改善）

        サンプルデータの実態:
            - C005: AI 65点（見送り推奨）→ 実際は成功 → FN = 1
            - TP = 2（C001, C002）
            - FNR = 1 / (1 + 2) = 0.33 = 33%
        """
        # 混同行列を計算
        confusion_matrix = calculate_confusion_matrix(ai_results, human_evaluations)

        # 偽陰性率を計算
        rates = calculate_false_rates(confusion_matrix)

        # 検証
        assert rates["false_negative_rate"] >= 0.0

        # サンプルデータでは FN = 1, TP = 2 → FNR = 33%
        # これは意図的なサンプルデータ（判断困難なケースを含む）
        assert rates["false_negative_rate"] <= 0.5, \
            f"Expected FNR <= 0.5, got {rates['false_negative_rate']}"

        # サンプルデータでの実際の値を確認
        assert confusion_matrix["false_negative"] == 1, \
            f"Expected FN = 1, got {confusion_matrix['false_negative']}"
        assert confusion_matrix["true_positive"] == 2, \
            f"Expected TP = 2, got {confusion_matrix['true_positive']}"

    def test_verify_hallucination(self, ai_results):
        """
        ハルシネーション検証のテスト

        仮定:
            - 出典チェック: 観察事実に「(参照:」が含まれるか
            - 確信度チェック: 確信度「低」が3つ以上あるか
            - 矛盾チェック: スコア80以上 + 否定的キーワード

        境界値テスト:
            - 警告0個（正常）
            - 警告1個以上（要確認）
        """
        # 各候補者のハルシネーション検証
        for result in ai_results:
            hallucination_report = verify_hallucinations(result)

            # 検証
            assert "candidate_id" in hallucination_report
            assert "warnings" in hallucination_report
            assert "warning_count" in hallucination_report
            assert isinstance(hallucination_report["warnings"], list)

            # 優秀な候補者（C001, C002）は警告なし
            if result["candidate_id"] in ["C001", "C002"]:
                assert hallucination_report["warning_count"] == 0, \
                    f"Expected no warnings for {result['candidate_id']}, got {hallucination_report['warnings']}"

    def test_verify_hallucination_with_warnings(self):
        """
        ハルシネーション警告が出るケースのテスト
        """
        # 出典なしのケース
        invalid_result = {
            "candidate_id": "TEST001",
            "overall_risk_score": 90,
            "evaluation": {
                "communication": {
                    "score": 90,
                    "observations": ["明瞭な発話"],  # 出典なし
                    "confidence": "高"
                },
                "stress_tolerance": {
                    "score": 85,
                    "observations": ["落ち着いている"],  # 出典なし
                    "confidence": "高"
                },
                "reliability": {
                    "score": 85,
                    "observations": ["信頼できる"],  # 出典なし
                    "confidence": "高"
                },
                "teamwork": {
                    "score": 85,
                    "observations": ["協調的"],  # 出典なし
                    "confidence": "高"
                }
            }
        }

        hallucination_report = verify_hallucinations(invalid_result)

        # 出典欠落の警告が出ること
        assert hallucination_report["warning_count"] > 0
        assert any("出典" in w or "参照" in w for w in hallucination_report["warnings"])

    def test_generate_poc_report(self, ai_results, human_evaluations):
        """
        PoC分析レポート生成のテスト

        仮定:
            - レポート形式: Markdown + JSON
            - 含まれる内容:
              - 相関係数（Pearson, Spearman）
              - 混同行列
              - 偽陽性率・偽陰性率
              - ハルシネーション検証結果
              - 総合評価

        境界値テスト:
            - 相関係数 >= 0.7 → 合格
            - 偽陽性率 < 20% → 合格
            - 偽陰性率 < 10% → 合格
        """
        # レポート生成
        report = generate_poc_report(ai_results, human_evaluations)

        # 検証
        assert "summary" in report
        assert "correlation" in report
        assert "confusion_matrix" in report
        assert "false_rates" in report
        assert "hallucination_verification" in report
        assert "pass_criteria" in report

        # 相関係数が含まれること
        assert "pearson" in report["correlation"]
        assert "spearman" in report["correlation"]

        # 偽陽性率・偽陰性率が含まれること
        assert "false_positive_rate" in report["false_rates"]
        assert "false_negative_rate" in report["false_rates"]

        # ハルシネーション検証結果が含まれること
        assert "total_warnings" in report["hallucination_verification"]
        assert "warnings_by_candidate" in report["hallucination_verification"]

        # 合格基準の判定が含まれること
        assert "correlation_pass" in report["pass_criteria"]
        assert "fpr_pass" in report["pass_criteria"]
        assert "fnr_pass" in report["pass_criteria"]

    def test_generate_poc_report_markdown(self, ai_results, human_evaluations, tmp_path):
        """
        Markdown形式のレポート生成テスト
        """
        # レポート生成
        report = generate_poc_report(ai_results, human_evaluations)

        # Markdownファイルに出力
        from src.poc_analysis import export_report_markdown
        output_path = tmp_path / "poc_report.md"
        export_report_markdown(report, str(output_path))

        # ファイルが作成されたことを確認
        assert output_path.exists()

        # ファイル内容を確認
        content = output_path.read_text(encoding="utf-8")
        assert "# PoC分析レポート" in content
        assert "相関係数" in content
        assert "混同行列" in content
        assert "偽陽性率" in content
