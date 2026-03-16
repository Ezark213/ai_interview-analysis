"""プロンプト構築モジュール"""
import os
from pathlib import Path


def build_prompt(knowledge_text: str) -> str:
    """
    ナレッジベーステキストとシステムプロンプトテンプレートを組み合わせ、
    完全なプロンプトを生成する

    Args:
        knowledge_text: ナレッジベースの内容（Markdown形式）

    Returns:
        str: {knowledge_base}が埋め込まれた完全なプロンプト

    仮定:
        - システムプロンプトテンプレートはsrc/prompts/system.txtに存在
        - テンプレート内の{knowledge_base}を置換する
        - 空ナレッジの場合でもプロンプトは生成される（デフォルト値なし）
    """
    # システムプロンプトテンプレートのパスを取得
    current_dir = Path(__file__).parent
    template_path = current_dir / "prompts" / "system.txt"

    # テンプレートが存在しない場合のフォールバック
    if not template_path.exists():
        raise FileNotFoundError(f"System prompt template not found: {template_path}")

    # テンプレートを読み込む
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # ナレッジベースを埋め込む
    prompt = template.replace("{knowledge_base}", knowledge_text)

    return prompt
