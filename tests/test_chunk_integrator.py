"""チャンク統合ロジックのテスト"""
import pytest
from src.chunk_integrator import ChunkIntegrator


class TestChunkIntegrator:
    """チャンク評価結果の統合機能のテスト"""

    @pytest.fixture
    def integrator(self):
        """ChunkIntegratorインスタンス"""
        return ChunkIntegrator()

    @pytest.fixture
    def sample_chunk_results(self):
        """サンプルのチャンク評価結果（3チャンク）"""
        return [
            {
                "chunk_id": 0,
                "chunk_time_range": {"start": 0, "end": 300},
                "overall_risk_score": 85,
                "risk_level": "低",
                "evaluation": {
                    "communication": {
                        "score": 80,
                        "observations": ["明瞭な発話"],
                        "confidence": "高"
                    },
                    "stress_tolerance": {
                        "score": 85,
                        "observations": ["冷静に対応"],
                        "confidence": "高"
                    },
                    "reliability": {
                        "score": 90,
                        "observations": ["具体的なエピソード"],
                        "confidence": "高"
                    },
                    "teamwork": {
                        "score": 85,
                        "observations": ["協力的な姿勢"],
                        "confidence": "中"
                    }
                },
                "red_flags": [],
                "positive_signals": ["技術的な深い理解"]
            },
            {
                "chunk_id": 1,
                "chunk_time_range": {"start": 300, "end": 600},
                "overall_risk_score": 80,
                "risk_level": "低",
                "evaluation": {
                    "communication": {
                        "score": 75,
                        "observations": ["質問に的確に回答"],
                        "confidence": "高"
                    },
                    "stress_tolerance": {
                        "score": 80,
                        "observations": ["落ち着いた様子"],
                        "confidence": "中"
                    },
                    "reliability": {
                        "score": 85,
                        "observations": ["誠実な回答"],
                        "confidence": "高"
                    },
                    "teamwork": {
                        "score": 80,
                        "observations": ["チーム経験を説明"],
                        "confidence": "高"
                    }
                },
                "red_flags": [],
                "positive_signals": ["自己学習の習慣"]
            },
            {
                "chunk_id": 2,
                "chunk_time_range": {"start": 600, "end": 900},
                "overall_risk_score": 90,
                "risk_level": "非常に低い",
                "evaluation": {
                    "communication": {
                        "score": 85,
                        "observations": ["明瞭な発話", "具体例を交えた説明"],
                        "confidence": "高"
                    },
                    "stress_tolerance": {
                        "score": 90,
                        "observations": ["難しい質問でも冷静"],
                        "confidence": "高"
                    },
                    "reliability": {
                        "score": 95,
                        "observations": ["過去の実績を明確に説明"],
                        "confidence": "高"
                    },
                    "teamwork": {
                        "score": 90,
                        "observations": ["協力的な姿勢", "リーダーシップも発揮"],
                        "confidence": "高"
                    }
                },
                "red_flags": [],
                "positive_signals": ["技術的な深い理解", "長期的なビジョン"]
            }
        ]

    def test_integrate_single_chunk(self, integrator):
        """単一チャンクの統合（そのまま返す）"""
        single_chunk = [{
            "chunk_id": 0,
            "chunk_time_range": {"start": 0, "end": 300},
            "overall_risk_score": 85,
            "evaluation": {"communication": {"score": 85, "observations": [], "confidence": "高"}},
            "red_flags": [],
            "positive_signals": []
        }]

        result = integrator.integrate_chunks(single_chunk)

        assert result["overall_risk_score"] == 85
        assert "chunk_id" not in result
        assert "chunk_time_range" not in result

    def test_integrate_multiple_chunks(self, integrator, sample_chunk_results):
        """複数チャンクの統合"""
        result = integrator.integrate_chunks(sample_chunk_results)

        # 基本構造の検証
        assert "overall_risk_score" in result
        assert "risk_level" in result
        assert "evaluation" in result
        assert "red_flags" in result
        assert "positive_signals" in result
        assert "recommendation" in result
        assert "disclaimer" in result
        assert "chunk_analysis" in result

        # チャンク分析情報の検証
        assert result["chunk_analysis"]["num_chunks"] == 3

        # 総合スコアは中央値ベース（85, 80, 90の中央値 = 85）
        assert 80 <= result["overall_risk_score"] <= 90

        # 各カテゴリーのスコアを検証
        assert "communication" in result["evaluation"]
        assert "stress_tolerance" in result["evaluation"]
        assert "reliability" in result["evaluation"]
        assert "teamwork" in result["evaluation"]

    def test_check_consistency_stable_scores(self, integrator, sample_chunk_results):
        """一貫性チェック: スコアが安定している場合"""
        issues = integrator._check_consistency(sample_chunk_results)

        # スコアのばらつきが小さい場合は問題なし
        assert len(issues) == 0

    def test_check_consistency_inconsistent_scores(self, integrator):
        """一貫性チェック: スコアが大きく変動している場合"""
        inconsistent_chunks = [
            {
                "evaluation": {
                    "communication": {"score": 90, "observations": [], "confidence": "高"}
                }
            },
            {
                "evaluation": {
                    "communication": {"score": 40, "observations": [], "confidence": "高"}
                }
            }
        ]

        issues = integrator._check_consistency(inconsistent_chunks)

        # 大きな変動があるので問題が検出される
        assert len(issues) > 0
        assert "communication" in issues[0]

    def test_extract_patterns_improving_trend(self, integrator):
        """パターン抽出: スコアが向上している場合"""
        improving_chunks = [
            {"overall_risk_score": 60, "red_flags": [], "chunk_time_range": {"start": 0, "end": 300}},
            {"overall_risk_score": 70, "red_flags": [], "chunk_time_range": {"start": 300, "end": 600}},
            {"overall_risk_score": 85, "red_flags": [], "chunk_time_range": {"start": 600, "end": 900}}
        ]

        patterns = integrator._extract_patterns(improving_chunks)

        assert patterns["score_trend"] == "improving"

    def test_extract_patterns_declining_trend(self, integrator):
        """パターン抽出: スコアが低下している場合"""
        declining_chunks = [
            {"overall_risk_score": 85, "red_flags": [], "chunk_time_range": {"start": 0, "end": 300}},
            {"overall_risk_score": 70, "red_flags": [], "chunk_time_range": {"start": 300, "end": 600}},
            {"overall_risk_score": 60, "red_flags": [], "chunk_time_range": {"start": 600, "end": 900}}
        ]

        patterns = integrator._extract_patterns(declining_chunks)

        assert patterns["score_trend"] == "declining"

    def test_extract_patterns_with_red_flags(self, integrator):
        """パターン抽出: レッドフラグが検出された時間帯"""
        chunks_with_flags = [
            {
                "overall_risk_score": 85,
                "red_flags": [],
                "chunk_time_range": {"start": 0, "end": 300}
            },
            {
                "overall_risk_score": 70,
                "red_flags": ["回答が曖昧"],
                "chunk_time_range": {"start": 300, "end": 600}
            }
        ]

        patterns = integrator._extract_patterns(chunks_with_flags)

        assert len(patterns["notable_moments"]) == 1
        assert patterns["notable_moments"][0]["time_range"] == "5-10分"
        assert patterns["notable_moments"][0]["type"] == "red_flag"

    def test_generate_recommendation_high_score(self, integrator):
        """推奨事項生成: 高得点の場合"""
        recommendation = integrator._generate_recommendation(
            score=85,
            risk_level="非常に低い",
            red_flags=[],
            positive_signals=["優秀"]
        )

        assert "推奨" in recommendation or "強く" in recommendation

    def test_generate_recommendation_with_red_flags(self, integrator):
        """推奨事項生成: レッドフラグがある場合"""
        recommendation = integrator._generate_recommendation(
            score=65,
            risk_level="中",
            red_flags=["回答が曖昧", "視線を避ける"],
            positive_signals=[]
        )

        assert "確認" in recommendation or "慎重" in recommendation

    def test_integrate_empty_list(self, integrator):
        """異常系: 空のリストを渡した場合"""
        with pytest.raises(ValueError, match="cannot be empty"):
            integrator.integrate_chunks([])
