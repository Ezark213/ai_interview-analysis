"""レスポンスパーサーのテスト"""
import json
import pytest
from pathlib import Path
from src.response_parser import parse_response, ResponseValidationError, validate_response


class TestResponseParser:
    """AIレスポンスのJSON抽出・バリデーション機能のテスト"""

    def test_parse_valid_json(self, mock_gemini_response):
        """正常なJSONレスポンスをパースできること"""
        # モックレスポンスをJSON文字列に変換
        response_text = json.dumps(mock_gemini_response, ensure_ascii=False)

        # 実行
        result = parse_response(response_text)

        # 検証
        assert result["overall_risk_score"] == 65
        assert result["risk_level"] == "低"
        assert "communication" in result["evaluation"]
        assert result["evaluation"]["communication"]["score"] == 75

    def test_parse_json_in_code_block(self, mock_gemini_response):
        """```json```ブロック内のJSONを抽出できること"""
        # JSONをコードブロックで囲む
        json_str = json.dumps(mock_gemini_response, ensure_ascii=False, indent=2)
        response_text = f"以下が評価結果です:\n\n```json\n{json_str}\n```\n"

        # 実行
        result = parse_response(response_text)

        # 検証
        assert result["overall_risk_score"] == 65
        assert result["risk_level"] == "低"

    def test_parse_json_in_markdown_code_block(self, mock_gemini_response):
        """複数のコードブロックがある場合、最初のJSONブロックを抽出"""
        json_str = json.dumps(mock_gemini_response, ensure_ascii=False, indent=2)
        response_text = f"""
ここに説明があります。

```python
# サンプルコード
print("test")
```

評価結果:
```json
{json_str}
```

補足説明があります。
"""

        # 実行
        result = parse_response(response_text)

        # 検証
        assert result["overall_risk_score"] == 65

    def test_parse_invalid_json(self):
        """JSON不正の場合にパースエラー"""
        # ケース1: 閉じ括弧がない不正なJSON
        invalid_json1 = "{invalid json content"
        with pytest.raises(ResponseValidationError, match="No JSON content found"):
            parse_response(invalid_json1)

        # ケース2: 構文的に不正なJSON（閉じ括弧はあるが構文エラー）
        invalid_json2 = '{"key": invalid_value}'
        with pytest.raises(ResponseValidationError, match="Failed to parse JSON"):
            parse_response(invalid_json2)

    def test_validate_required_fields(self):
        """必須フィールド（overall_risk_score等）の存在確認"""
        # 必須フィールドが欠けたJSON
        incomplete_json = json.dumps({
            "overall_risk_score": 70
            # evaluation, red_flags等が欠けている
        })

        # 実行と検証
        with pytest.raises(ResponseValidationError, match="Missing required field"):
            parse_response(incomplete_json)

    def test_validate_score_range(self):
        """スコアが0-100の範囲内であること"""
        # スコアが範囲外のJSON
        invalid_score_json = json.dumps({
            "overall_risk_score": 150,  # 範囲外
            "risk_level": "低",
            "evaluation": {
                "communication": {"score": 75, "observations": [], "confidence": "高"},
                "stress_tolerance": {"score": 60, "observations": [], "confidence": "中"},
                "reliability": {"score": 70, "observations": [], "confidence": "高"},
                "teamwork": {"score": 65, "observations": [], "confidence": "中"}
            },
            "red_flags": [],
            "positive_signals": [],
            "recommendation": "test",
            "disclaimer": "test"
        })

        # 実行と検証
        with pytest.raises(ResponseValidationError, match="Score out of range"):
            parse_response(invalid_score_json)

    def test_parse_response_no_json_found(self):
        """JSONが含まれないレスポンス"""
        no_json_text = "これはただのテキストです。JSONは含まれていません。"

        # 実行と検証
        with pytest.raises(ResponseValidationError, match="No JSON content found"):
            parse_response(no_json_text)

    def test_validate_evaluation_categories(self):
        """evaluationに必須カテゴリが含まれていること"""
        # communicationカテゴリが欠けたJSON
        incomplete_eval_json = json.dumps({
            "overall_risk_score": 70,
            "risk_level": "低",
            "evaluation": {
                # "communication"が欠けている
                "stress_tolerance": {"score": 60, "observations": [], "confidence": "中"},
                "reliability": {"score": 70, "observations": [], "confidence": "高"},
                "teamwork": {"score": 65, "observations": [], "confidence": "中"}
            },
            "red_flags": [],
            "positive_signals": [],
            "recommendation": "test",
            "disclaimer": "test"
        })

        # 実行と検証
        with pytest.raises(ResponseValidationError, match="Missing evaluation category"):
            parse_response(incomplete_eval_json)


class TestHallucinationPrevention:
    """ハルシネーション対策のバリデーション機能のテスト（Iteration-04）"""

    def test_validate_reference_missing(self):
        """
        観察事実（observations）に出典が欠落している場合、警告を返すこと

        仮定:
            - 出典形式: 「(参照: <セクション名>)」
            - 観察事実の末尾に出典がない場合、警告リストに追加
        """
        # 出典なしのレスポンスを読み込み
        fixture_path = Path(__file__).parent / "fixtures" / "response_no_reference.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            response_data = json.load(f)

        # バリデーション実行
        warnings = validate_response(response_data)

        # 検証: 出典欠落の警告が含まれること
        assert len(warnings) > 0
        assert any("出典" in w or "参照" in w for w in warnings), \
            f"Expected reference warning, got: {warnings}"

    def test_validate_reference_present(self):
        """
        観察事実に出典が含まれている場合、出典関連の警告が出ないこと

        仮定:
            - 出典形式: 「(参照: <セクション名>)」
        """
        # 出典ありのレスポンスを読み込み
        fixture_path = Path(__file__).parent / "fixtures" / "response_with_references.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            response_data = json.load(f)

        # バリデーション実行
        warnings = validate_response(response_data)

        # 検証: 出典関連の警告がないこと（他の警告はあっても良い）
        reference_warnings = [w for w in warnings if "出典" in w or "参照" in w]
        assert len(reference_warnings) == 0, \
            f"Unexpected reference warnings: {reference_warnings}"

    def test_validate_low_confidence_threshold(self):
        """
        確信度「低」が閾値を超える場合、警告を返すこと

        仮定:
            - 4カテゴリ中3つ以上が確信度「低」の場合、警告
            - 警告メッセージに「確信度が低い」または「低確信度」を含む
        """
        # 確信度「低」が4つ（全て）のレスポンスを読み込み
        fixture_path = Path(__file__).parent / "fixtures" / "response_low_confidence.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            response_data = json.load(f)

        # バリデーション実行
        warnings = validate_response(response_data)

        # 検証: 確信度低の警告が含まれること
        assert len(warnings) > 0
        assert any("確信度" in w and "低" in w for w in warnings), \
            f"Expected low confidence warning, got: {warnings}"

    def test_validate_low_confidence_below_threshold(self):
        """
        確信度「低」が閾値未満の場合、確信度関連の警告が出ないこと

        境界値テスト: 2つまでは警告なし、3つ以上で警告
        """
        # 確信度「低」が0個のレスポンス
        response_data = {
            "overall_risk_score": 75,
            "risk_level": "低",
            "evaluation": {
                "communication": {"score": 80, "observations": ["test（参照: test）"], "confidence": "高"},
                "stress_tolerance": {"score": 75, "observations": ["test（参照: test）"], "confidence": "高"},
                "reliability": {"score": 70, "observations": ["test（参照: test）"], "confidence": "中"},
                "teamwork": {"score": 75, "observations": ["test（参照: test）"], "confidence": "中"}
            },
            "red_flags": [],
            "positive_signals": [],
            "recommendation": "test",
            "disclaimer": "test"
        }

        # バリデーション実行
        warnings = validate_response(response_data)

        # 検証: 確信度関連の警告がないこと
        confidence_warnings = [w for w in warnings if "確信度" in w and "低" in w]
        assert len(confidence_warnings) == 0, \
            f"Unexpected confidence warnings: {confidence_warnings}"

    def test_validate_contradictory_observations(self):
        """
        矛盾した観察事実がある場合、警告を返すこと

        仮定:
            - 矛盾の定義1: スコアが高い（80以上）のに観察事実が否定的
            - 矛盾の定義2: スコアが高いのに確信度が「低」
            - 否定的キーワード: 「不安定」「不明瞭」「矛盾」「避ける」「批判的」等
        """
        # 矛盾のあるレスポンスを読み込み
        fixture_path = Path(__file__).parent / "fixtures" / "response_contradictory.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            response_data = json.load(f)

        # バリデーション実行
        warnings = validate_response(response_data)

        # 検証: 矛盾の警告が含まれること
        assert len(warnings) > 0
        assert any("矛盾" in w or "不一致" in w or "整合性" in w for w in warnings), \
            f"Expected contradiction warning, got: {warnings}"

    def test_validate_no_warnings_for_valid_response(self):
        """
        正常なレスポンス（出典あり、確信度適切、矛盾なし）では警告が出ないこと
        """
        # 正常なレスポンスを読み込み
        fixture_path = Path(__file__).parent / "fixtures" / "response_with_references.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            response_data = json.load(f)

        # バリデーション実行
        warnings = validate_response(response_data)

        # 検証: 警告が空リストであること
        assert warnings == [], f"Expected no warnings, got: {warnings}"
