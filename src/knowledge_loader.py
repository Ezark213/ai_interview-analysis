"""ナレッジベース読み込みモジュール"""
import os
from pathlib import Path
from typing import List


def load_knowledge_base(knowledge_dir: str = None) -> str:
    """
    指定ディレクトリ内の全.mdファイルを読み込み、結合したテキストを返す

    Args:
        knowledge_dir: ナレッジベースのディレクトリパス（デフォルト: プロジェクトルート/knowledge-base）

    Returns:
        str: 全.mdファイルの内容を結合したテキスト

    Raises:
        FileNotFoundError: ディレクトリが存在しない場合

    仮定:
        - .md拡張子のファイルのみを対象とする
        - ファイルはUTF-8エンコーディングで読み込む
        - ファイルの読み込み順序は保証されない（ソート順）
    """
    # デフォルト値の設定（プロジェクトルート/knowledge-base）
    if knowledge_dir is None:
        # このファイル（knowledge_loader.py）の親の親ディレクトリ = プロジェクトルート
        project_root = Path(__file__).parent.parent
        kb_path = project_root / "knowledge-base"
    else:
        kb_path = Path(knowledge_dir)
    if not kb_path.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {knowledge_dir}")

    if not kb_path.is_dir():
        raise FileNotFoundError(f"Path is not a directory: {knowledge_dir}")

    # .mdファイルを検索
    md_files = sorted(kb_path.glob("*.md"))

    # ファイルが見つからない場合は空文字列を返す
    if not md_files:
        return ""

    # 全ファイルの内容を結合
    contents: List[str] = []
    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                contents.append(content)
        except Exception as e:
            # ファイル読み込みエラーは警告として記録（テストでは無視）
            print(f"Warning: Failed to read {md_file}: {e}")
            continue

    return "\n\n".join(contents)
