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
            "score": 75,
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
        },
        "credibility": {
            "score": 70,
            "observations": ["検証可能な詳細あり（参照: 信頼度基準）"],
            "confidence": "中"
        },
        "professional_demeanor": {
            "score": 70,
            "observations": ["敬語が適切（参照: 職業的態度基準）"],
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
            "score": 75,
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
        },
        "credibility": {
            "score": 70,
            "observations": ["検証可能な詳細あり（参照: 信頼度基準）"],
            "confidence": "中"
        },
        "professional_demeanor": {
            "score": 70,
            "observations": ["敬語が適切（参照: 職業的態度基準）"],
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
                "communication": {"score": 75, "observations": ["テスト（参照: 基準）"], "confidence": "高"},
                "stress_tolerance": {"score": 70, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                "reliability": {"score": 75, "observations": ["テスト（参照: 基準）"], "confidence": "高"},
                "teamwork": {"score": 72, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                "credibility": {"score": 70, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                "professional_demeanor": {"score": 70, "observations": ["テスト（参照: 基準）"], "confidence": "中"}
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

    def test_validate_behavioral_metrics_none(self):
        """behavioral_metricsがNoneの場合のバリデーション（IT-11追加）"""
        from src.response_parser import validate_behavioral_metrics

        # Noneを渡しても例外を投げず、空リストを返すこと
        warnings = validate_behavioral_metrics(None)
        assert isinstance(warnings, list)
        assert len(warnings) == 0

    def test_merge_behavioral_metrics_no_valid_chunks(self):
        """有効チャンクが0件の場合のメトリクスマージ（IT-11追加）"""
        integrator = ChunkIntegrator()

        # behavioral_metricsがNoneのチャンクのみ
        chunk_results = [
            {
                "chunk_id": 0,
                "chunk_time_range": {"start": 0, "end": 300},
                "status": "success",
                "overall_risk_score": 75,
                "risk_level": "低",
                "evaluation": {
                    "communication": {"score": 75, "observations": ["テスト（参照: 基準）"], "confidence": "高"},
                    "stress_tolerance": {"score": 70, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                    "reliability": {"score": 75, "observations": ["テスト（参照: 基準）"], "confidence": "高"},
                    "teamwork": {"score": 72, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                    "credibility": {"score": 70, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                    "professional_demeanor": {"score": 70, "observations": ["テスト（参照: 基準）"], "confidence": "中"},
                },
                "behavioral_metrics": None,
                "red_flags": [],
                "positive_signals": ["テスト"],
                "recommendation": "テスト",
                "disclaimer": "テスト",
            },
        ]

        result = integrator.integrate_chunks(chunk_results)

        # 単一チャンクの場合はそのまま返されるが、metricsはNoneのまま
        assert result.get("behavioral_metrics") is None

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
                    "communication": {"score": 75, "observations": ["テスト1（参照: 基準）"], "confidence": "高"},
                    "stress_tolerance": {"score": 70, "observations": ["テスト1（参照: 基準）"], "confidence": "中"},
                    "reliability": {"score": 75, "observations": ["テスト1（参照: 基準）"], "confidence": "高"},
                    "teamwork": {"score": 72, "observations": ["テスト1（参照: 基準）"], "confidence": "中"},
                    "credibility": {"score": 70, "observations": ["テスト1（参照: 基準）"], "confidence": "中"},
                    "professional_demeanor": {"score": 70, "observations": ["テスト1（参照: 基準）"], "confidence": "中"},
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
                    "communication": {"score": 65, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
                    "stress_tolerance": {"score": 65, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
                    "reliability": {"score": 70, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
                    "teamwork": {"score": 68, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
                    "credibility": {"score": 65, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
                    "professional_demeanor": {"score": 65, "observations": ["テスト2（参照: 基準）"], "confidence": "中"},
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
                    "communication": {"score": 75, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
                    "stress_tolerance": {"score": 75, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
                    "reliability": {"score": 80, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
                    "teamwork": {"score": 78, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
                    "credibility": {"score": 75, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
                    "professional_demeanor": {"score": 75, "observations": ["テスト3（参照: 基準）"], "confidence": "高"},
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


# ===== Iteration-03: 境界値・異常系テスト (T03-01) + end-to-end (T03-03) =====

class TestBehavioralMetricsEdgeCases:
    """validate_behavioral_metrics() の境界値・異常系テスト（T03-01）"""

    def test_mixed_old_new_metrics(self):
        """旧フィールドと新フィールドが混在する入力"""
        from src.response_parser import validate_behavioral_metrics
        mixed = {
            # 旧スキーマ
            "eye_contact_quality": "高",
            "posture_stability": "高",
            # 新スキーマ
            "deliberate_eye_contact": "なし",
            "illustrator_frequency": "豊富",
        }
        warnings = validate_behavioral_metrics(mixed)
        old_key_warnings = [w for w in warnings if "eye_contact_quality" in w or "posture_stability" in w]
        assert len(old_key_warnings) >= 2, f"旧フィールド2つに対して警告が出るべき: {warnings}"
        new_key_warnings = [w for w in warnings if "deliberate_eye_contact" in w or "illustrator_frequency" in w]
        assert len(new_key_warnings) == 0, f"新フィールドに対して警告が出てはいけない: {warnings}"

    def test_null_metrics_values(self):
        """値がNoneの新フィールドがあっても警告なし"""
        from src.response_parser import validate_behavioral_metrics
        metrics = {
            "deliberate_eye_contact": None,
            "illustrator_frequency": "豊富",
            "cognitive_load_signs": None,
        }
        warnings = validate_behavioral_metrics(metrics)
        none_warnings = [w for w in warnings if "None" in str(w)]
        assert len(none_warnings) == 0, f"None値に対して警告が出てはいけない: {warnings}"

    def test_wrong_type_metrics(self):
        """int型やlist型など不正な型の値"""
        from src.response_parser import validate_behavioral_metrics
        metrics = {
            "deliberate_eye_contact": 123,
            "illustrator_frequency": ["豊富", "普通"],
            "speech_fluency": True,
        }
        warnings = validate_behavioral_metrics(metrics)
        assert len(warnings) >= 3, f"型異常の3フィールドに対して警告が出るべき: {warnings}"

    def test_only_unknown_keys(self):
        """全て未知キーのみの入力"""
        from src.response_parser import validate_behavioral_metrics
        metrics = {
            "totally_made_up": "value",
            "another_fake_key": "test",
        }
        warnings = validate_behavioral_metrics(metrics)
        assert len(warnings) >= 2, f"未知キー2つに対して警告が出るべき: {warnings}"

    def test_empty_metrics_dict(self):
        """空辞書で警告なし"""
        from src.response_parser import validate_behavioral_metrics
        warnings = validate_behavioral_metrics({})
        assert warnings == [], f"空辞書に対して警告が出てはいけない: {warnings}"


class TestEndToEndPipeline:
    """end-to-endパイプラインテスト（T03-03）"""

    def test_end_to_end_gemini_response_simulation(self):
        """新スキーマ準拠の完全なJSONがparse→validate→metricsの全パイプラインを通ること"""
        import json
        from src.response_parser import parse_response, validate_response, validate_behavioral_metrics
        sample_response = json.dumps({
            "overall_risk_score": 62,
            "risk_level": "低",
            "evaluation": {
                "communication": {
                    "score": 65,
                    "observations": [
                        "質問に対して論理的に回答している（参照: communication BARSレベル4）",
                        "専門用語を適切に噛み砕いて説明（参照: communication BARSレベル4）"
                    ],
                    "confidence": "高"
                },
                "stress_tolerance": {
                    "score": 55,
                    "observations": ["圧迫質問に対して一定の落ち着きを保った（参照: stress_tolerance BARSレベル3）"],
                    "confidence": "中"
                },
                "reliability": {
                    "score": 70,
                    "observations": [
                        "プロジェクト名と期間を具体的に述べた（参照: reliability BARSレベル4）",
                        "数値を用いた成果説明（参照: reliability BARSレベル4）"
                    ],
                    "confidence": "高"
                },
                "teamwork": {
                    "score": 55,
                    "observations": ["チーム作業の言及あり（参照: teamwork BARSレベル3）"],
                    "confidence": "中"
                },
                "credibility": {
                    "score": 60,
                    "observations": ["検証可能な詳細が一部含まれる（参照: credibility CBCA指標）"],
                    "confidence": "中"
                },
                "professional_demeanor": {
                    "score": 60,
                    "observations": ["適切な敬語使用（参照: professional_demeanor BARSレベル3）"],
                    "confidence": "中"
                }
            },
            "behavioral_metrics": {
                "deliberate_eye_contact": "なし",
                "illustrator_frequency": "普通",
                "speech_fluency": "中",
                "response_speed": "適切",
                "verbal_nonverbal_consistency": "一致",
                "immediacy_level": "高",
                "cognitive_load_signs": "なし",
                "micro_expression_detected": "検出不能",
                "dark_triad_indicators": "なし",
                "cwb_risk_signals": "なし"
            },
            "red_flags": [],
            "positive_signals": ["具体的なプロジェクト経験を述べた", "言語と非言語の一致度が高い"],
            "recommendation": "技術面の信頼性は概ね良好。チームワークの具体的エピソードを追加確認することを推奨。",
            "disclaimer": "本評価はAIによる参考情報です。最終判断は人間が行ってください。"
        }, ensure_ascii=False)

        # Step 1: parse_response
        parsed = parse_response(sample_response)
        assert parsed is not None
        assert parsed["overall_risk_score"] == 62

        # Step 2: validate_response（ハルシネーションチェック）
        hal_warnings = validate_response(parsed)
        assert isinstance(hal_warnings, list)

        # Step 3: validate_behavioral_metrics
        metrics = parsed.get("behavioral_metrics")
        assert metrics is not None
        metric_warnings = validate_behavioral_metrics(metrics)
        assert metric_warnings == [], f"正常な新スキーマで警告が出ました: {metric_warnings}"

        # Step 4: 新スキーマのフィールドが全て存在すること
        expected_keys = {
            "deliberate_eye_contact", "illustrator_frequency", "speech_fluency",
            "response_speed", "verbal_nonverbal_consistency", "immediacy_level",
            "cognitive_load_signs", "micro_expression_detected",
            "dark_triad_indicators", "cwb_risk_signals"
        }
        assert set(metrics.keys()) == expected_keys
