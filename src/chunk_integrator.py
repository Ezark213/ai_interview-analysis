"""チャンク評価結果の統合モジュール"""
from typing import List, Dict, Any, Tuple
from statistics import mean, median


class ChunkIntegrator:
    """
    複数のチャンク評価結果を統合して総合評価を生成するクラス

    役割:
        1. チャンク間の一貫性チェック
        2. 時系列パターンの抽出
        3. 総合評価の生成
    """

    def __init__(self):
        """初期化"""
        self.category_keys = ["communication", "stress_tolerance", "reliability", "teamwork"]

    def integrate_chunks(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        複数のチャンク評価結果を統合して総合評価を生成

        Args:
            chunk_results: 各チャンクの評価結果のリスト
                各要素は以下の形式:
                {
                    "chunk_id": 0,
                    "chunk_time_range": {"start": 0, "end": 300},
                    "overall_risk_score": 85,
                    "evaluation": {...},
                    "red_flags": [...],
                    "positive_signals": [...]
                }

        Returns:
            Dict[str, Any]: 統合された総合評価

        Raises:
            ValueError: chunk_resultsが空の場合、または全チャンクがエラーの場合
        """
        if not chunk_results:
            raise ValueError("chunk_results cannot be empty")

        # エラーステータスのチャンクをフィルタリング
        successful_chunks = [
            chunk for chunk in chunk_results
            if chunk.get("status") != "error" and "evaluation" in chunk
        ]

        if not successful_chunks:
            raise ValueError("All chunks failed with errors. Cannot generate overall evaluation.")

        # 単一チャンクの場合はそのまま返す（時間範囲情報は削除）
        if len(successful_chunks) == 1:
            result = successful_chunks[0].copy()
            result.pop("chunk_id", None)
            result.pop("chunk_time_range", None)
            result.pop("status", None)
            result.pop("error_code", None)
            result.pop("processing_info", None)
            return result

        # 1. 一貫性チェック
        consistency_issues = self._check_consistency(successful_chunks)

        # 2. 時系列パターン抽出
        patterns = self._extract_patterns(successful_chunks)

        # 3. 総合評価生成
        overall_evaluation = self._generate_overall_evaluation(successful_chunks)

        # 4. 統合結果を構築
        integrated_result = {
            "overall_risk_score": overall_evaluation["overall_risk_score"],
            "risk_level": overall_evaluation["risk_level"],
            "evaluation": overall_evaluation["evaluation"],
            "red_flags": overall_evaluation["red_flags"],
            "positive_signals": overall_evaluation["positive_signals"],
            "recommendation": overall_evaluation["recommendation"],
            "disclaimer": "本評価はAIによる参考情報です。最終判断は人間が行ってください。",
            "chunk_analysis": {
                "num_chunks": len(chunk_results),
                "num_successful": len(successful_chunks),
                "num_failed": len(chunk_results) - len(successful_chunks),
                "consistency_issues": consistency_issues,
                "temporal_patterns": patterns
            }
        }

        return integrated_result

    def _check_consistency(self, chunk_results: List[Dict[str, Any]]) -> List[str]:
        """
        チャンク間の一貫性をチェック

        Args:
            chunk_results: 各チャンクの評価結果

        Returns:
            List[str]: 一貫性の問題点（なければ空リスト）
        """
        issues = []

        # 各カテゴリーのスコアの標準偏差をチェック
        for category in self.category_keys:
            scores = []
            for chunk in chunk_results:
                evaluation = chunk.get("evaluation", {})
                if category in evaluation:
                    scores.append(evaluation[category].get("score", 0))

            if len(scores) >= 2:
                # 標準偏差を計算（簡易版）
                avg = mean(scores)
                variance = sum((x - avg) ** 2 for x in scores) / len(scores)
                std_dev = variance ** 0.5

                # 標準偏差が20以上の場合は不一致とみなす
                if std_dev > 20:
                    issues.append(
                        f"{category}のスコアがチャンク間で大きく変動しています "
                        f"(標準偏差: {std_dev:.1f})"
                    )

        return issues

    def _extract_patterns(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        時系列パターンを抽出

        Args:
            chunk_results: 各チャンクの評価結果（時系列順）

        Returns:
            Dict[str, Any]: 検出されたパターン
        """
        patterns = {
            "score_trend": None,  # "improving", "declining", "stable"
            "notable_moments": []  # 特筆すべき時間帯
        }

        # 総合スコアの推移を分析
        scores = [chunk.get("overall_risk_score", 0) for chunk in chunk_results]

        if len(scores) >= 2:
            # 前半と後半の平均を比較
            mid_point = len(scores) // 2
            first_half_avg = mean(scores[:mid_point])
            second_half_avg = mean(scores[mid_point:])

            diff = second_half_avg - first_half_avg

            if diff > 10:
                patterns["score_trend"] = "improving"
            elif diff < -10:
                patterns["score_trend"] = "declining"
            else:
                patterns["score_trend"] = "stable"

        # レッドフラグが検出された時間帯を記録
        for chunk in chunk_results:
            red_flags = chunk.get("red_flags", [])
            if red_flags:
                time_range = chunk.get("chunk_time_range", {})
                start_min = time_range.get("start", 0) // 60
                end_min = time_range.get("end", 0) // 60

                patterns["notable_moments"].append({
                    "time_range": f"{start_min}-{end_min}分",
                    "type": "red_flag",
                    "details": red_flags
                })

        return patterns

    def _generate_overall_evaluation(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        総合評価を生成

        Args:
            chunk_results: 各チャンクの評価結果

        Returns:
            Dict[str, Any]: 総合評価
        """
        # 1. 各カテゴリーのスコアを集計（中央値を使用）
        category_scores = {}
        category_observations = {}
        category_confidences = {}

        for category in self.category_keys:
            scores = []
            observations = []
            confidences = []

            for chunk in chunk_results:
                evaluation = chunk.get("evaluation", {})
                if category in evaluation:
                    cat_data = evaluation[category]
                    scores.append(cat_data.get("score", 0))
                    observations.extend(cat_data.get("observations", []))
                    confidences.append(cat_data.get("confidence", "中"))

            # 中央値でスコアを算出（外れ値の影響を減らす）
            category_scores[category] = int(median(scores)) if scores else 0

            # 観察事項は重複を除去して統合
            category_observations[category] = list(set(observations))

            # 確信度は最頻値を採用
            category_confidences[category] = max(set(confidences), key=confidences.count) if confidences else "中"

        # 2. 総合スコアを計算（各カテゴリーの中央値の平均）
        overall_score = int(mean(category_scores.values()))

        # 3. リスクレベルを判定
        if overall_score >= 80:
            risk_level = "非常に低い"
        elif overall_score >= 70:
            risk_level = "低"
        elif overall_score >= 60:
            risk_level = "中"
        elif overall_score >= 50:
            risk_level = "やや高"
        else:
            risk_level = "高"

        # 4. レッドフラグとポジティブシグナルを統合
        all_red_flags = []
        all_positive_signals = []

        for chunk in chunk_results:
            all_red_flags.extend(chunk.get("red_flags", []))
            all_positive_signals.extend(chunk.get("positive_signals", []))

        # 重複除去
        unique_red_flags = list(set(all_red_flags))
        unique_positive_signals = list(set(all_positive_signals))

        # 5. 推奨事項を生成
        recommendation = self._generate_recommendation(
            overall_score,
            risk_level,
            unique_red_flags,
            unique_positive_signals
        )

        # 6. 評価データを構築
        evaluation = {}
        for category in self.category_keys:
            evaluation[category] = {
                "score": category_scores[category],
                "observations": category_observations[category],
                "confidence": category_confidences[category]
            }

        return {
            "overall_risk_score": overall_score,
            "risk_level": risk_level,
            "evaluation": evaluation,
            "red_flags": unique_red_flags,
            "positive_signals": unique_positive_signals,
            "recommendation": recommendation
        }

    def _generate_recommendation(
        self,
        score: int,
        risk_level: str,
        red_flags: List[str],
        positive_signals: List[str]
    ) -> str:
        """
        推奨事項を生成

        Args:
            score: 総合スコア
            risk_level: リスクレベル
            red_flags: レッドフラグのリスト
            positive_signals: ポジティブシグナルのリスト

        Returns:
            str: 推奨事項
        """
        if score >= 80 and not red_flags:
            return "優秀な候補者です。アサインを強く推奨します。"
        elif score >= 70 and len(red_flags) <= 1:
            return "良好な評価です。アサインを推奨しますが、気になる点があれば追加確認を検討してください。"
        elif score >= 60:
            if red_flags:
                return f"中程度の評価です。以下の点について追加面談での確認を推奨します: {', '.join(red_flags[:2])}"
            else:
                return "中程度の評価です。実務経験や技術スキルの追加確認を推奨します。"
        else:
            if red_flags:
                return f"慎重な判断が必要です。特に以下のリスク要因について詳細確認を推奨します: {', '.join(red_flags[:3])}"
            else:
                return "慎重な判断が必要です。複数の面接官による再評価を検討してください。"
