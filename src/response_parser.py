"""AIレスポンスのJSON抽出・バリデーションモジュール"""
import json
import re
from typing import Dict, Any


class ResponseValidationError(Exception):
    """レスポンスのバリデーションエラー"""
    pass


def parse_response(response_text: str) -> Dict[str, Any]:
    """
    AIのレスポンス文字列からJSON部分を抽出し、バリデーションする

    Args:
        response_text: AIからのレスポンステキスト

    Returns:
        Dict[str, Any]: 構造化された評価結果辞書

    Raises:
        ResponseValidationError: JSON解析失敗、バリデーションエラー時

    仮定:
        - JSONは```json```ブロック内にある場合と、生のJSONの場合がある
        - 必須フィールド: overall_risk_score, risk_level, evaluation,
                        red_flags, positive_signals, recommendation, disclaimer
        - evaluationの必須カテゴリ: communication, stress_tolerance,
                                    reliability, teamwork, credibility,
                                    professional_demeanor
        - スコアの範囲: 0-100
    """
    # JSONコンテンツの抽出
    json_content = _extract_json_content(response_text)

    # JSON解析
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        raise ResponseValidationError(f"Failed to parse JSON: {str(e)}")

    # バリデーション
    _validate_structure(data)

    return data


def _extract_json_content(text: str) -> str:
    """
    テキストからJSON部分を抽出する

    優先順位:
    1. ```json```ブロック内のJSON
    2. テキスト全体がJSONかどうかをチェック
    3. ブレースカウンティングで{}の対応を追跡

    Args:
        text: 入力テキスト

    Returns:
        str: 抽出されたJSON文字列

    Raises:
        ResponseValidationError: JSONが見つからない場合
    """
    # パターン1: ```json```ブロックを検索
    json_block_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_block_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # パターン2: テキスト全体がJSONかどうかをチェック
    text_stripped = text.strip()
    if text_stripped.startswith('{') and text_stripped.endswith('}'):
        # 簡易的なバリデーション: json.loads()で解析できるかチェック
        try:
            json.loads(text_stripped)
            return text_stripped
        except json.JSONDecodeError:
            # 全体がJSONではない、次の方法を試す
            pass

    # パターン3: ブレースカウンティングで最初の完全なJSONオブジェクトを抽出
    json_str = _extract_json_by_brace_counting(text)
    if json_str:
        return json_str

    # JSONが見つからない
    raise ResponseValidationError("No JSON content found in response")


def _extract_json_by_brace_counting(text: str) -> str:
    """
    ブレースカウンティングでJSONオブジェクトを抽出

    Args:
        text: 入力テキスト

    Returns:
        str: 抽出されたJSON文字列、見つからない場合は空文字列
    """
    start_index = text.find('{')
    if start_index == -1:
        return ""

    brace_count = 0
    in_string = False
    escape_next = False

    for i in range(start_index, len(text)):
        char = text[i]

        # エスケープ処理
        if escape_next:
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            continue

        # 文字列内かどうかの判定
        if char == '"':
            in_string = not in_string
            continue

        # 文字列内はブレースをカウントしない
        if in_string:
            continue

        # ブレースカウント
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                # 完全なJSONオブジェクトを見つけた
                return text[start_index:i+1]

    return ""


def _validate_structure(data: Dict[str, Any]) -> None:
    """
    評価結果の構造をバリデーションする

    Args:
        data: 解析されたJSON辞書

    Raises:
        ResponseValidationError: バリデーションエラー時
    """
    # 必須フィールドのチェック
    required_fields = [
        "overall_risk_score",
        "risk_level",
        "evaluation",
        "red_flags",
        "positive_signals",
        "recommendation",
        "disclaimer"
    ]

    for field in required_fields:
        if field not in data:
            raise ResponseValidationError(f"Missing required field: {field}")

    # overall_risk_scoreの範囲チェック
    score = data["overall_risk_score"]
    if not isinstance(score, (int, float)) or score < 0 or score > 100:
        raise ResponseValidationError(
            f"Score out of range (0-100): overall_risk_score={score}"
        )

    # evaluationの構造チェック
    evaluation = data["evaluation"]
    if not isinstance(evaluation, dict):
        raise ResponseValidationError("evaluation must be a dictionary")

    # 必須評価カテゴリ（6カテゴリ）
    required_categories = [
        "communication", "stress_tolerance", "reliability",
        "teamwork", "credibility", "professional_demeanor"
    ]
    for category in required_categories:
        if category not in evaluation:
            raise ResponseValidationError(f"Missing evaluation category: {category}")

        # 各カテゴリのスコアチェック
        category_data = evaluation[category]
        if not isinstance(category_data, dict):
            raise ResponseValidationError(f"Category {category} must be a dictionary")

        if "score" not in category_data:
            raise ResponseValidationError(f"Missing score in category: {category}")

        cat_score = category_data["score"]
        if not isinstance(cat_score, (int, float)) or cat_score < 0 or cat_score > 100:
            raise ResponseValidationError(
                f"Score out of range (0-100) in {category}: {cat_score}"
            )

    # behavioral_metricsは任意フィールド（後方互換: 存在しなければNoneに正規化）
    if "behavioral_metrics" not in data:
        data["behavioral_metrics"] = None


# 行動メトリクスの有効な値定義
_VALID_METRICS = {
    "eye_contact_quality": {"高", "中", "低"},
    "gesture_naturalness": {"高", "中", "低"},
    "posture_stability": {"高", "中", "低"},
    "speech_fluency": {"高", "中", "低"},
    "filler_frequency": {"多い", "普通", "少ない"},
    "response_speed": {"速い", "適切", "遅い"},
    "verbal_nonverbal_consistency": {"一致", "部分一致", "不一致"},
}


def validate_behavioral_metrics(metrics: dict) -> list:
    """
    行動メトリクスのバリデーション（Iteration-10追加）

    Args:
        metrics: behavioral_metricsの辞書（Noneの場合は空リストを返す）

    Returns:
        list: 警告メッセージのリスト
    """
    if not metrics:
        return []

    warnings = []

    for key, valid_values in _VALID_METRICS.items():
        value = metrics.get(key)
        if value is not None and value not in valid_values:
            warnings.append(
                f"behavioral_metrics.{key} の値が不正です: '{value}'（有効値: {valid_values}）"
            )

    return warnings


def validate_response(data: Dict[str, Any]) -> list:
    """
    ハルシネーション対策のための追加バリデーション（Iteration-04）

    Args:
        data: 解析されたJSON辞書

    Returns:
        list: 警告メッセージのリスト（空リスト = 警告なし）

    仮定:
        - 出典形式: 「(参照: <セクション名>)」または「（参照: <セクション名>）」
        - 確信度「低」の閾値: カテゴリの75%以上で警告
        - 矛盾の定義:
          1. スコア70以上なのに否定的な観察事実
          2. スコア70以上なのに確信度「低」
        - スコア分布チェック: 全カテゴリ80点以上の場合に警告
    """
    warnings = []

    # 1. 出典チェック
    reference_warnings = _check_references(data)
    warnings.extend(reference_warnings)

    # 2. 確信度閾値チェック
    confidence_warnings = _check_low_confidence_threshold(data)
    warnings.extend(confidence_warnings)

    # 3. 矛盾検出
    contradiction_warnings = _check_contradictions(data)
    warnings.extend(contradiction_warnings)

    # 4. スコア分布チェック（Iteration-14追加）
    distribution_warnings = _check_score_distribution(data)
    warnings.extend(distribution_warnings)

    return warnings


def _check_references(data: Dict[str, Any]) -> list:
    """
    観察事実に出典が含まれているかチェック

    Args:
        data: 解析されたJSON辞書

    Returns:
        list: 出典関連の警告リスト
    """
    warnings = []
    evaluation = data.get("evaluation", {})

    for category, category_data in evaluation.items():
        observations = category_data.get("observations", [])

        for obs in observations:
            # 出典のパターン: 「(参照:」または「（参照:」
            if "参照:" not in obs and "参照：" not in obs:
                warnings.append(
                    f"出典が欠落している観察事実: カテゴリ'{category}' - '{obs[:50]}...'"
                )

    return warnings


def _check_low_confidence_threshold(data: Dict[str, Any]) -> list:
    """
    確信度「低」が閾値を超えていないかチェック

    Args:
        data: 解析されたJSON辞書

    Returns:
        list: 確信度関連の警告リスト

    仮定:
        - カテゴリの75%以上が確信度「低」の場合、警告
    """
    warnings = []
    evaluation = data.get("evaluation", {})

    # 確信度「低」のカウント
    low_confidence_count = 0
    total_categories = 0

    for category, category_data in evaluation.items():
        total_categories += 1
        confidence = category_data.get("confidence", "")

        if confidence == "低":
            low_confidence_count += 1

    # 閾値チェック: 75%以上で警告
    threshold = max(3, int(total_categories * 0.75))
    if low_confidence_count >= threshold:
        warnings.append(
            f"確信度が低い評価が多すぎます: {low_confidence_count}/{total_categories}カテゴリが確信度「低」。"
            f"評価の信頼性に問題がある可能性があります。"
        )

    return warnings


def _check_contradictions(data: Dict[str, Any]) -> list:
    """
    矛盾した評価がないかチェック

    Args:
        data: 解析されたJSON辞書

    Returns:
        list: 矛盾関連の警告リスト

    仮定:
        - 矛盾1: スコア70以上（高評価）なのに否定的キーワードを含む観察事実
        - 矛盾2: スコア70以上（高評価）なのに確信度「低」
        - 否定的キーワード: 不安定、不明瞭、矛盾、避ける、批判的、回避、不十分、欠如
    """
    warnings = []
    evaluation = data.get("evaluation", {})

    # 否定的キーワードリスト
    negative_keywords = [
        "不安定", "不明瞭", "矛盾", "避ける", "批判的", "回避",
        "不十分", "欠如", "問題", "困難", "弱い", "乏しい"
    ]

    for category, category_data in evaluation.items():
        score = category_data.get("score", 0)
        observations = category_data.get("observations", [])
        confidence = category_data.get("confidence", "")

        # 矛盾1: 高スコア（70以上）なのに否定的な観察事実
        if score >= 70:
            for obs in observations:
                for keyword in negative_keywords:
                    if keyword in obs:
                        warnings.append(
                            f"矛盾を検出: カテゴリ'{category}'はスコア{score}（高評価）ですが、"
                            f"否定的な観察事実が含まれています: '{obs[:50]}...'"
                        )
                        break  # 同じ観察事実で複数警告を出さない

        # 矛盾2: 高スコア（70以上）なのに確信度「低」
        if score >= 70 and confidence == "低":
            warnings.append(
                f"矛盾を検出: カテゴリ'{category}'はスコア{score}（高評価）ですが、"
                f"確信度が「低」となっています。評価の整合性を確認してください。"
            )

    return warnings


def _check_score_distribution(data: Dict[str, Any]) -> list:
    """
    スコア分布チェック（Iteration-14追加）

    全カテゴリが80点以上の場合、スコアの偏りを警告する。
    BARSベースの評価では全カテゴリ高スコアは稀であり、
    甘め評価の兆候として警告する。

    Args:
        data: 解析されたJSON辞書

    Returns:
        list: スコア分布関連の警告リスト
    """
    warnings = []
    evaluation = data.get("evaluation", {})

    if not evaluation:
        return warnings

    scores = []
    for category, category_data in evaluation.items():
        score = category_data.get("score", 0)
        scores.append(score)

    # 全カテゴリが80点以上の場合に警告
    if scores and all(s >= 80 for s in scores):
        avg_score = sum(scores) / len(scores)
        warnings.append(
            f"スコア分布の偏り: 全{len(scores)}カテゴリが80点以上（平均{avg_score:.0f}点）です。"
            f"BARSレベル5の行動証拠が各カテゴリで十分に確認されているか再検証してください。"
        )

    return warnings
