"""構造化データ解析（行動メトリクス）のテスト

behavioral_metricsフィールドのパース・バリデーション・チャンク統合テスト。
テスト対象:
- response_parser.py: behavioral_metricsのパース+バリデーション
- chunk_integrator.py: メトリクスのチャンク間マージ
"""
import pytest
from src.response_parser import parse_response
from src.chunk_integrator import ChunkIntegrator


# テスト用の有効なレスポンスベース（behavioral_metrics付き）
VALID_RESPONSE_WITH_METRICS = """{
    "overall_risk_score": 75,
    "risk_level": "低",
    "evaluation": {
        "communication": {
            "score": 80,
            "observations": ["明瞭な発話（参照: コミュニケーション基準）"],
            "confidence": "高"
        },
        "stress_tolerance": {
            "score": 70,
            "observations": ["適切な対処（参照: ストレス耐性基準）"],
            "confidence": "中"
        },
        "reliability": {
            "score": 75,
            "observations": ["一貫した回答（参照: 信頼性評価基準）"],
            "confidence": "高"
        },
        "teamwork": {
            "score": 72,
            "observations": ["協調性あり（参照: チームワーク基準）"],
            "confidence": "中"
        }
    },
    "behavioral_metrics": {
        "eye_contact_quality": "高",
        "gesture_naturalness": "中",
        "posture_stability": "高",
        "speech_fluency": "高",
        "filler_frequency": "少ない",
        "response_speed": "適切",
        "verbal_nonverbal_consistency": "一致"
    },
    "red_flags": [],
    "positive_signals": ["明瞭なコミュニケーション"],
    "recommendation": "良好な評価です。",
    "disclaimer": "本評価はAIによる参考情報です。最終判断は人間が行ってください。"
}"""

# behavioral_metricsなしのレスポンス（後方互換テスト用）
VALID_RESPONSE_WITHOUT_METRICS = """{
    "overall_risk_score": 75,
    "risk_level": "低",
    "evaluation": {
        "communication": {
            "score": 80,
            "observations": ["明瞭な発話（参照: コミュニケーション基準）"],
            "confidence": "高"
        },
        "stress_tolerance": {
            "score": 70,
            "observations": ["適切な対処（参照: ストレス耐性基準）"],
            "confidence": "中"
        },
        "reliability": {
            "score": 75,
            "observations": ["一貫した回答（参照: 信頼性評価基準）"],
            "confidence": "高"
        },
        "teamwork": {
            "score": 72,
            "observations": ["協調性あり（参照: チームワーク基準）"],
            "confidence": "中"
        }
    },
    "red_flags": [],
    "positive_signals": ["明瞭なコミュニケーション"],
    "recommendation": "良好な評価です。",
    "disclaimer": "本評価はAIによる参考情報です。最終判断は人間が行ってください。"
}"""


class TestBehavioralMetrics:
    """行動メトリクスのテスト"""

    def test_parse_response_with_metrics(self):
        """behavioral_metricsフィールドを含むレスポンスがパースできる"""
        result = parse_response(VALID_RESPONSE_WITH_METRICS)

        assert "behavioral_metrics" in result
        metrics = result["behavioral_metrics"]
        assert metrics["eye_contact_quality"] == "高"
        assert metrics["gesture_naturalness"] == "中"
        assert metrics["posture_stability"] == "高"
        assert metrics["speech_fluency"] == "高"
        assert metrics["filler_frequency"] == "少ない"
        assert metrics["response_speed"] == "適切"
        assert metrics["verbal_nonverbal_consistency"] == "一致"

    def test_parse_response_without_metrics(self):
        """behavioral_metricsなしのレスポンスも後方互換で動作する"""
        result = parse_response(VALID_RESPONSE_WITHOUT_METRICS)

        # パースが成功すること
        assert "overall_risk_score" in result
        assert result["overall_risk_score"] == 75
        # behavioral_metricsはNoneまたは存在しない
        assert result.get("behavioral_metrics") is None

    def test_metrics_validation(self):
        """メトリクスの数値が妥当な範囲内かバリデーション"""
        # 不正な値を含むレスポンス
        invalid_metrics_response = """{
            "overall_risk_score": 75,
            "risk_level": "低",
            "evaluation": {
                "communication": {"score": 80, "observations": ["テスト（参照: 基準）"], "confidence": "高"},
                "stress_tolerance": {"score": 70, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                "reliability": {"score": 75, "observations": ["テスト（参照: 基準）"], "confidence": "高"},
                "teamwork": {"score": 72, "observations": ["テスト（参照: 基準）"], "confidence": "中"}
            },
            "behavioral_metrics": {
                "eye_contact_quality": "不正な値",
                "gesture_naturalness": "中",
                "posture_stability": "高",
                "speech_fluency": "高",
                "filler_frequency": "少ない",
                "response_speed": "適切",
                "verbal_nonverbal_consistency": "一致"
            },
            "red_flags": [],
            "positive_signals": ["テスト"],
            "recommendation": "テスト",
            "disclaimer": "テスト"
        }"""
        from src.response_parser import validate_behavioral_metrics

        result = parse_response(invalid_metrics_response)
        warnings = validate_behavioral_metrics(result.get("behavioral_metrics", {}))

        # 不正な値に対する警告が含まれること
        assert len(warnings) > 0
        assert any("eye_contact_quality" in w for w in warnings)

    def test_chunk_integrator_merges_metrics(self):
        """チャンク統合時にメトリクスが正しくマージされる"""
        integrator = ChunkIntegrator()

        chunk_results = [
            {
                "chunk_id": 0,
                "chunk_time_range": {"start": 0, "end": 300},
                "status": "success",
                "overall_risk_score": 75,
                "risk_level": "低",
                "evaluation": {
                    "communication": {"score": 80, "observations": ["テスト1（参照: 基準）"], "confidence": "高"},
                    "stress_tolerance": {"score": 70, "observations": ["テスト1（参照: 基準）"], "confidence": "中"},
                    "reliability": {"score": 75, "observations": ["テスト1（参照: 基準）"], "confidence": "高"},
                    "teamwork": {"score": 72, "observations": ["テスト1（参照: 基準）"], "confidence": "中"},
                },
                "behavioral_metrics": {
                    "eye_contact_quality": "高",
                    "gesture_naturalness": "中",
                    "posture_stability": "高",
                    "speech_fluency": "高",
                    "filler_frequency": "少ない",
                    "response_speed": "適切",
                    "verbal_nonverbal_consistency": "一致",
                },
                "red_flags": [],
                "positive_signals": ["テスト1"],
                "recommendation": "テスト",
                "disclaimer": "テスト",
            },
            {
                "chunk_id": 1,
                "chunk_time_range": {"start": 300, "end": 600},
                "status": "success",
                "overall_risk_score": 70,
                "risk_level": "低",
                "evaluation": {
                    "communication": {"score": 75, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
                    "stress_tolerance": {"score": 65, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
                    "reliability": {"score": 70, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
                    "teamwork": {"score": 68, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
                },
                "behavioral_metrics": {
                    "eye_contact_quality": "中",
                    "gesture_naturalness": "中",
                    "posture_stability": "中",
                    "speech_fluency": "高",
                    "filler_frequency": "普通",
                    "response_speed": "適切",
                    "verbal_nonverbal_consistency": "部分一致",
                },
                "red_flags": [],
                "positive_signals": ["テスト2"],
                "recommendation": "テスト",
                "disclaimer": "テスト",
            },
            {
                "chunk_id": 2,
                "chunk_time_range": {"start": 600, "end": 900},
                "status": "success",
                "overall_risk_score": 80,
                "risk_level": "低",
                "evaluation": {
                    "communication": {"score": 85, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
                    "stress_tolerance": {"score": 75, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
                    "reliability": {"score": 80, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
                    "teamwork": {"score": 78, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
                },
                "behavioral_metrics": {
                    "eye_contact_quality": "高",
                    "gesture_naturalness": "高",
                    "posture_stability": "高",
                    "speech_fluency": "高",
                    "filler_frequency": "少ない",
                    "response_speed": "速い",
                    "verbal_nonverbal_consistency": "一致",
                },
                "red_flags": [],
                "positive_signals": ["テスト3"],
                "recommendation": "テスト",
                "disclaimer": "テスト",
            },
        ]

        result = integrator.integrate_chunks(chunk_results)

        # behavioral_metricsが統合結果に含まれること
        assert "behavioral_metrics" in result
        metrics = result["behavioral_metrics"]

        # 最頻値でマージされること
        # eye_contact_quality: 高(2) vs 中(1) → 高
        assert metrics["eye_contact_quality"] == "高"
        # speech_fluency: 高(3) → 高
        assert metrics["speech_fluency"] == "高"
        # gesture_naturalness: 中(2) vs 高(1) → 中
        assert metrics["gesture_naturalness"] == "中"
