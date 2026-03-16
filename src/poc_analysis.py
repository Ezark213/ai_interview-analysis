"""PoC（Proof of Concept）分析モジュール（Iteration-05）

このモジュールは、AI評価結果と人間評価結果を比較し、以下を算出します:
- 相関係数（Pearson, Spearman）
- 混同行列
- 偽陽性率・偽陰性率
- ハルシネーション検証
- PoC分析レポート生成
"""

import json
from typing import Dict, List, Any, Tuple
from pathlib import Path

# 統計計算ライブラリ
try:
    import numpy as np
    from scipy import stats
    from sklearn.metrics import confusion_matrix as sklearn_confusion_matrix
    import pandas as pd
except ImportError:
    print("Warning: scipy, scikit-learn, or pandas not installed.")
    print("Install with: pip install scipy scikit-learn pandas")
    raise


# 定数（PoC合格基準）
CORRELATION_THRESHOLD = 0.7  # 相関係数の閾値
FALSE_POSITIVE_RATE_THRESHOLD = 0.20  # 偽陽性率の閾値（20%）
FALSE_NEGATIVE_RATE_THRESHOLD = 0.10  # 偽陰性率の閾値（10%）
AI_SCORE_THRESHOLD = 70  # AIスコアの採用推奨閾値


def calculate_correlation(ai_scores: List[float], human_scores: List[float]) -> Dict[str, float]:
    """
    AI評価スコアと人間評価スコアの相関係数を計算

    Args:
        ai_scores: AI評価スコアのリスト
        human_scores: 人間評価スコアのリスト

    Returns:
        Dict: {
            "pearson": Pearson相関係数,
            "p_value_pearson": p値,
            "spearman": Spearman相関係数,
            "p_value_spearman": p値
        }

    仮定:
        - スコアは両方とも0-100の範囲
        - リストの長さは同じ
        - 最低3サンプル以上

    参考:
        - Pearson: 線形相関を測定（正規分布を仮定）
        - Spearman: 順位相関を測定（非線形でも対応可）
    """
    if len(ai_scores) != len(human_scores):
        raise ValueError("AI scores and human scores must have the same length")

    if len(ai_scores) < 3:
        raise ValueError("At least 3 samples are required for correlation calculation")

    # Pearson相関係数
    pearson_r, pearson_p = stats.pearsonr(ai_scores, human_scores)

    # Spearman相関係数
    spearman_r, spearman_p = stats.spearmanr(ai_scores, human_scores)

    return {
        "pearson": float(pearson_r),
        "p_value_pearson": float(pearson_p),
        "spearman": float(spearman_r),
        "p_value_spearman": float(spearman_p)
    }


def calculate_confusion_matrix(
    ai_results: List[Dict[str, Any]],
    human_evaluations: pd.DataFrame
) -> Dict[str, int]:
    """
    混同行列を計算

    Args:
        ai_results: AI評価結果のリスト
        human_evaluations: 人間評価結果（pandas DataFrame）

    Returns:
        Dict: {
            "true_positive": TP（AIが採用推奨 & 実際に成功）,
            "false_positive": FP（AIが採用推奨 & 実際に失敗）,
            "true_negative": TN（AIが見送り推奨 & 実際に問題あり）,
            "false_negative": FN（AIが見送り推奨 & 実際に成功）
        }

    仮定:
        - AI判定: overall_risk_score >= 70 → 「採用推奨」
        - 人間判定: actual_outcome == "成功" → 「成功」
                   actual_outcome == "失敗" → 「失敗」
                   actual_outcome == "該当なし" → 除外（見送りのため未アサイン）
    """
    # AI判定と実際の結果を抽出
    ai_predictions = []
    actual_outcomes = []

    for ai_result in ai_results:
        candidate_id = ai_result["candidate_id"]

        # 人間評価結果を取得
        human_row = human_evaluations[human_evaluations["candidate_id"] == candidate_id]

        if len(human_row) == 0:
            continue

        human_row = human_row.iloc[0]
        actual_outcome = human_row["actual_outcome"]

        # 見送りのケース（actual_outcome == "該当なし"）は除外
        if actual_outcome == "該当なし":
            continue

        # AI判定: スコア >= 70 → 1（採用推奨）、< 70 → 0（見送り推奨）
        ai_score = ai_result["overall_risk_score"]
        ai_prediction = 1 if ai_score >= AI_SCORE_THRESHOLD else 0

        # 実際の結果: "成功" → 1、"失敗" → 0
        actual = 1 if actual_outcome == "成功" else 0

        ai_predictions.append(ai_prediction)
        actual_outcomes.append(actual)

    # scikit-learnで混同行列を計算
    # [[TN, FP],
    #  [FN, TP]]
    cm = sklearn_confusion_matrix(actual_outcomes, ai_predictions, labels=[0, 1])

    return {
        "true_negative": int(cm[0, 0]),
        "false_positive": int(cm[0, 1]),
        "false_negative": int(cm[1, 0]),
        "true_positive": int(cm[1, 1])
    }


def calculate_false_rates(confusion_matrix: Dict[str, int]) -> Dict[str, float]:
    """
    偽陽性率・偽陰性率を計算

    Args:
        confusion_matrix: 混同行列

    Returns:
        Dict: {
            "false_positive_rate": 偽陽性率（FPR = FP / (FP + TN)）,
            "false_negative_rate": 偽陰性率（FNR = FN / (FN + TP)）,
            "true_positive_rate": 真陽性率（TPR = TP / (TP + FN)）,
            "true_negative_rate": 真陰性率（TNR = TN / (TN + FP)）,
            "precision": 適合率（TP / (TP + FP)）,
            "recall": 再現率（TPR）,
            "f1_score": F1スコア
        }

    計算式:
        - FPR = FP / (FP + TN)  # 問題ない候補者のうち、誤って採用推奨した割合
        - FNR = FN / (FN + TP)  # 優秀な候補者のうち、誤って見送った割合
        - TPR = TP / (TP + FN)  # 優秀な候補者のうち、正しく採用推奨した割合
        - TNR = TN / (TN + FP)  # 問題ある候補者のうち、正しく見送った割合
    """
    tp = confusion_matrix["true_positive"]
    fp = confusion_matrix["false_positive"]
    tn = confusion_matrix["true_negative"]
    fn = confusion_matrix["false_negative"]

    # ゼロ除算対策
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    # Precision（適合率）: 採用推奨のうち、実際に成功した割合
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

    # Recall（再現率）: 成功した候補者のうち、正しく採用推奨した割合
    recall = tpr

    # F1 Score
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "false_positive_rate": float(fpr),
        "false_negative_rate": float(fnr),
        "true_positive_rate": float(tpr),
        "true_negative_rate": float(tnr),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1_score)
    }


def verify_hallucinations(ai_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    ハルシネーション検証

    Args:
        ai_result: AI評価結果（1名分）

    Returns:
        Dict: {
            "candidate_id": 候補者ID,
            "warnings": 警告リスト,
            "warning_count": 警告数
        }

    検証項目:
        1. 出典チェック: 観察事実に「(参照:」が含まれるか
        2. 確信度チェック: 確信度「低」が3つ以上あるか
        3. 矛盾チェック: スコア80以上 + 否定的キーワード or 低確信度
    """
    warnings = []
    candidate_id = ai_result.get("candidate_id", "UNKNOWN")
    evaluation = ai_result.get("evaluation", {})

    # 1. 出典チェック
    for category, category_data in evaluation.items():
        observations = category_data.get("observations", [])

        for obs in observations:
            # 出典のパターン: 「(参照:」または「（参照:」
            if "参照:" not in obs and "参照：" not in obs:
                warnings.append(f"出典欠落: カテゴリ'{category}' - '{obs[:30]}...'")

    # 2. 確信度チェック
    low_confidence_count = sum(
        1 for cat_data in evaluation.values()
        if cat_data.get("confidence") == "低"
    )

    if low_confidence_count >= 3:
        warnings.append(
            f"確信度が低い評価が多すぎます: {low_confidence_count}/{len(evaluation)}カテゴリが確信度「低」"
        )

    # 3. 矛盾チェック
    negative_keywords = [
        "不安定", "不明瞭", "矛盾", "避ける", "批判的", "回避",
        "不十分", "欠如", "問題", "困難", "弱い", "乏しい"
    ]

    for category, category_data in evaluation.items():
        score = category_data.get("score", 0)
        observations = category_data.get("observations", [])
        confidence = category_data.get("confidence", "")

        # 矛盾1: 高スコア（80以上）+ 否定的キーワード
        if score >= 80:
            for obs in observations:
                for keyword in negative_keywords:
                    if keyword in obs:
                        warnings.append(
                            f"矛盾検出: カテゴリ'{category}'はスコア{score}（高評価）ですが、"
                            f"否定的な観察事実: '{obs[:30]}...'"
                        )
                        break

        # 矛盾2: 高スコア（80以上）+ 低確信度
        if score >= 80 and confidence == "低":
            warnings.append(
                f"矛盾検出: カテゴリ'{category}'はスコア{score}（高評価）ですが、確信度が「低」"
            )

    return {
        "candidate_id": candidate_id,
        "warnings": warnings,
        "warning_count": len(warnings)
    }


def generate_poc_report(
    ai_results: List[Dict[str, Any]],
    human_evaluations: pd.DataFrame
) -> Dict[str, Any]:
    """
    PoC分析レポートを生成

    Args:
        ai_results: AI評価結果のリスト
        human_evaluations: 人間評価結果（pandas DataFrame）

    Returns:
        Dict: {
            "summary": サマリー,
            "correlation": 相関係数,
            "confusion_matrix": 混同行列,
            "false_rates": 偽陽性率・偽陰性率,
            "hallucination_verification": ハルシネーション検証結果,
            "pass_criteria": 合格基準の判定
        }
    """
    # 1. 相関係数の計算
    ai_scores = [result["overall_risk_score"] for result in ai_results]
    human_scores = human_evaluations["human_score"].tolist()

    correlation = calculate_correlation(ai_scores, human_scores)

    # 2. 混同行列の計算
    confusion_mat = calculate_confusion_matrix(ai_results, human_evaluations)

    # 3. 偽陽性率・偽陰性率の計算
    false_rates = calculate_false_rates(confusion_mat)

    # 4. ハルシネーション検証
    hallucination_results = []
    total_warnings = 0

    for ai_result in ai_results:
        hallucination_report = verify_hallucinations(ai_result)
        hallucination_results.append(hallucination_report)
        total_warnings += hallucination_report["warning_count"]

    # 5. 合格基準の判定
    correlation_pass = correlation["pearson"] >= CORRELATION_THRESHOLD
    fpr_pass = false_rates["false_positive_rate"] < FALSE_POSITIVE_RATE_THRESHOLD
    fnr_pass = false_rates["false_negative_rate"] < FALSE_NEGATIVE_RATE_THRESHOLD

    overall_pass = correlation_pass and fpr_pass and fnr_pass

    # 6. サマリー
    summary = {
        "total_candidates": len(ai_results),
        "ai_score_mean": float(np.mean(ai_scores)),
        "ai_score_std": float(np.std(ai_scores)),
        "human_score_mean": float(np.mean(human_scores)),
        "human_score_std": float(np.std(human_scores))
    }

    return {
        "summary": summary,
        "correlation": correlation,
        "confusion_matrix": confusion_mat,
        "false_rates": false_rates,
        "hallucination_verification": {
            "total_warnings": total_warnings,
            "warnings_by_candidate": hallucination_results
        },
        "pass_criteria": {
            "correlation_pass": correlation_pass,
            "fpr_pass": fpr_pass,
            "fnr_pass": fnr_pass,
            "overall_pass": overall_pass,
            "thresholds": {
                "correlation": CORRELATION_THRESHOLD,
                "false_positive_rate": FALSE_POSITIVE_RATE_THRESHOLD,
                "false_negative_rate": FALSE_NEGATIVE_RATE_THRESHOLD
            }
        }
    }


def export_report_markdown(report: Dict[str, Any], output_path: str) -> None:
    """
    PoC分析レポートをMarkdown形式で出力

    Args:
        report: generate_poc_report()の戻り値
        output_path: 出力ファイルパス
    """
    summary = report["summary"]
    correlation = report["correlation"]
    confusion_mat = report["confusion_matrix"]
    false_rates = report["false_rates"]
    hallucination = report["hallucination_verification"]
    pass_criteria = report["pass_criteria"]

    # Markdown生成
    markdown = f"""# PoC分析レポート

**作成日**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 1. サマリー

- **対象候補者数**: {summary['total_candidates']}名
- **AIスコア平均**: {summary['ai_score_mean']:.1f} ± {summary['ai_score_std']:.1f}
- **人間スコア平均**: {summary['human_score_mean']:.1f} ± {summary['human_score_std']:.1f}

---

## 2. 相関係数

### Pearson相関係数
- **r = {correlation['pearson']:.3f}** (p = {correlation['p_value_pearson']:.4f})
- 判定: {'✅ 合格' if pass_criteria['correlation_pass'] else '❌ 要改善'} (閾値: {pass_criteria['thresholds']['correlation']})

### Spearman相関係数
- **ρ = {correlation['spearman']:.3f}** (p = {correlation['p_value_spearman']:.4f})

**解釈**:
- r > 0.7: 高い相関（AIと人間の評価がよく一致）
- 0.4 < r < 0.7: 中程度の相関
- r < 0.4: 低い相関（AIの精度に問題あり）

---

## 3. 混同行列

|  | 実際: 成功 | 実際: 失敗 |
|---|---|---|
| **AI: 採用推奨** | TP = {confusion_mat['true_positive']} | FP = {confusion_mat['false_positive']} |
| **AI: 見送り推奨** | FN = {confusion_mat['false_negative']} | TN = {confusion_mat['true_negative']} |

---

## 4. 偽陽性率・偽陰性率

### 偽陽性率（False Positive Rate）
- **FPR = {false_rates['false_positive_rate']:.2%}**
- 判定: {'✅ 合格' if pass_criteria['fpr_pass'] else '❌ 要改善'} (閾値: {pass_criteria['thresholds']['false_positive_rate']:.0%})
- 意味: 問題ある候補者のうち、AIが誤って「採用推奨」した割合

### 偽陰性率（False Negative Rate）
- **FNR = {false_rates['false_negative_rate']:.2%}**
- 判定: {'✅ 合格' if pass_criteria['fnr_pass'] else '❌ 要改善'} (閾値: {pass_criteria['thresholds']['false_negative_rate']:.0%})
- 意味: 優秀な候補者のうち、AIが誤って「見送り推奨」した割合

### その他の指標

- **適合率（Precision）**: {false_rates['precision']:.2%}
- **再現率（Recall）**: {false_rates['recall']:.2%}
- **F1スコア**: {false_rates['f1_score']:.3f}

---

## 5. ハルシネーション検証

- **総警告数**: {hallucination['total_warnings']}件

### 候補者別の警告
"""

    for candidate_report in hallucination["warnings_by_candidate"]:
        markdown += f"\n#### {candidate_report['candidate_id']}\n"
        if candidate_report["warning_count"] == 0:
            markdown += "- ✅ 警告なし\n"
        else:
            for warning in candidate_report["warnings"]:
                markdown += f"- ⚠️ {warning}\n"

    markdown += f"""
---

## 6. 総合判定

{'🎉 **PoC合格**' if pass_criteria['overall_pass'] else '⚠️ **PoC要改善**'}

### 合格基準

| 項目 | 結果 | 閾値 | 判定 |
|---|---|---|---|
| 相関係数（Pearson） | {correlation['pearson']:.3f} | ≥ {pass_criteria['thresholds']['correlation']} | {'✅' if pass_criteria['correlation_pass'] else '❌'} |
| 偽陽性率 | {false_rates['false_positive_rate']:.2%} | < {pass_criteria['thresholds']['false_positive_rate']:.0%} | {'✅' if pass_criteria['fpr_pass'] else '❌'} |
| 偽陰性率 | {false_rates['false_negative_rate']:.2%} | < {pass_criteria['thresholds']['false_negative_rate']:.0%} | {'✅' if pass_criteria['fnr_pass'] else '❌'} |

---

## 7. 推奨事項

"""

    if pass_criteria['overall_pass']:
        markdown += """
- ✅ AIの精度は十分です。実運用への移行を推奨します。
- 継続的な精度モニタリングを実施してください。
"""
    else:
        if not pass_criteria['correlation_pass']:
            markdown += f"- ❌ 相関係数が低い（{correlation['pearson']:.3f} < {pass_criteria['thresholds']['correlation']}）: プロンプト・ナレッジベースの改善が必要です。\n"

        if not pass_criteria['fpr_pass']:
            markdown += f"- ❌ 偽陽性率が高い（{false_rates['false_positive_rate']:.2%} > {pass_criteria['thresholds']['false_positive_rate']:.0%}）: 問題ある候補者を見逃すリスクがあります。基準を厳格化してください。\n"

        if not pass_criteria['fnr_pass']:
            markdown += f"- ❌ 偽陰性率が高い（{false_rates['false_negative_rate']:.2%} > {pass_criteria['thresholds']['false_negative_rate']:.0%}）: 優秀な候補者を見送るリスクがあります。基準を緩和してください。\n"

    markdown += "\n---\n\n**Generated by AI Interview Analysis System - Iteration-05**\n"

    # ファイル出力
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)


def main():
    """CLI エントリーポイント（サンプルデータでのドライラン）"""
    import argparse

    parser = argparse.ArgumentParser(description="PoC分析ツール")
    parser.add_argument("--sample", action="store_true", help="サンプルデータで分析")
    parser.add_argument("--ai-results", help="AI評価結果JSONファイル")
    parser.add_argument("--human-evals", help="人間評価結果CSVファイル")
    parser.add_argument("--output", default="poc_report.md", help="出力ファイル名")

    args = parser.parse_args()

    if args.sample:
        # サンプルデータで分析
        print("[PoC Analysis] Running with sample data...")

        sample_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "poc_sample_data"

        with open(sample_dir / "ai_results.json", "r", encoding="utf-8") as f:
            ai_results = json.load(f)

        human_evaluations = pd.read_csv(sample_dir / "human_evaluations.csv")

    else:
        if not args.ai_results or not args.human_evals:
            print("Error: --ai-results and --human-evals are required (or use --sample)")
            return

        with open(args.ai_results, "r", encoding="utf-8") as f:
            ai_results = json.load(f)

        human_evaluations = pd.read_csv(args.human_evals)

    # レポート生成
    print("[PoC Analysis] Generating report...")
    report = generate_poc_report(ai_results, human_evaluations)

    # JSON出力
    json_output = args.output.replace(".md", ".json")
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[OK] JSON output: {json_output}")

    # Markdown出力
    export_report_markdown(report, args.output)
    print(f"[OK] Markdown output: {args.output}")

    # 結果サマリーを表示
    print("\n[PoC Analysis] Results Summary")
    print(f"  Correlation (Pearson): {report['correlation']['pearson']:.3f}")
    print(f"  False Positive Rate: {report['false_rates']['false_positive_rate']:.2%}")
    print(f"  False Negative Rate: {report['false_rates']['false_negative_rate']:.2%}")
    print(f"  Overall: {'PASS' if report['pass_criteria']['overall_pass'] else 'NEEDS IMPROVEMENT'}")


if __name__ == "__main__":
    main()
