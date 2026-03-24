"""プロンプト構築モジュール"""
import os
from pathlib import Path


# 文字起こしテキストがある場合に挿入するセクション
TRANSCRIPT_SECTION_TEMPLATE = """## 文字起こしテキスト（Whisper APIによる音声認識結果）
{transcript}

## 文字起こしがある場合の追加指示
- 文字起こしテキストと動画の非言語行動を照合し、言行一致・不一致を評価する
- 発言内容の具体性（抽象的な回答 vs 具体的なエピソード）を分析する
- 発言のタイミングと非言語行動（目線の動き、姿勢変化など）の対応関係に注目する
- 回答の長さ・速度・フィラー（えーと、あのー等）のパターンも評価対象とする"""


def build_prompt(knowledge_text: str, transcript: str = None) -> str:
    """
    ナレッジベーステキストとシステムプロンプトテンプレートを組み合わせ、
    完全なプロンプトを生成する

    Args:
        knowledge_text: ナレッジベースの内容（Markdown形式）
        transcript: 文字起こしテキスト（Noneの場合は文字起こしセクションを省略）

    Returns:
        str: プレースホルダーが埋め込まれた完全なプロンプト

    仮定:
        - システムプロンプトテンプレートはsrc/prompts/system.txtに存在
        - テンプレート内の{knowledge_base}を置換する
        - 空ナレッジの場合でもプロンプトは生成される（デフォルト値なし）
        - transcriptがNone/空の場合、文字起こしセクションは丸ごと省略する
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

    # 文字起こしセクションを処理
    if transcript:
        transcript_section = TRANSCRIPT_SECTION_TEMPLATE.replace("{transcript}", transcript)
        prompt = prompt.replace("{transcript_section}", transcript_section)
    else:
        # 文字起こしなし: セクションプレースホルダーを空行に置換
        prompt = prompt.replace("\n{transcript_section}\n", "\n")

    return prompt
