"""ナレッジベース読み込みモジュール"""
import os
from pathlib import Path
from typing import List


# プロジェクトルート
_PROJECT_ROOT = Path(__file__).parent.parent
_PRESETS_DIR = _PROJECT_ROOT / "knowledge-base" / "presets"
_REFERENCE_DIR = _PROJECT_ROOT / "knowledge-base" / "reference"

# プリセット定義
_PRESET_REGISTRY = [
    {
        "id": "ses_interview",
        "name": "SES面談",
        "description": "SES業界のエンジニア面談向け。客先常駐適応力・早期離職リスクなどを重視",
    },
]


def list_presets() -> list:
    """
    利用可能なプリセット一覧を返す

    Returns:
        list[dict]: 各プリセットの情報（id, name, description）
    """
    return [p.copy() for p in _PRESET_REGISTRY]


def load_preset(preset_id: str) -> str:
    """
    プリセットIDに基づきナレッジベースを読み込む

    Args:
        preset_id: プリセットID（例: "ses_interview"）

    Returns:
        str: プリセットの内容

    Raises:
        ValueError: 存在しないプリセットIDの場合
    """
    valid_ids = {p["id"] for p in _PRESET_REGISTRY}
    if preset_id not in valid_ids:
        raise ValueError(f"Unknown preset: {preset_id}. Available: {valid_ids}")

    preset_path = _PRESETS_DIR / f"{preset_id}.md"
    if not preset_path.exists():
        raise FileNotFoundError(f"Preset file not found: {preset_path}")

    with open(preset_path, "r", encoding="utf-8") as f:
        return f.read()


def load_custom_knowledge(content: str) -> str:
    """
    ユーザーアップロードのMarkdownテキストをバリデーション+返却

    Args:
        content: ユーザーがアップロードしたMarkdownテキスト

    Returns:
        str: バリデーション済みのテキスト

    Raises:
        ValueError: 空または空白のみの場合
    """
    if not content or not content.strip():
        raise ValueError("カスタムナレッジベースが空です。Markdown形式のテキストを入力してください。")

    return content.strip()


def load_combined_knowledge(preset_id: str = None, custom_content: str = None) -> str:
    """
    プリセットとカスタムを組み合わせて返す。両方Noneならデフォルト(core-criteria.md)

    Args:
        preset_id: プリセットID（Noneならプリセット未使用）
        custom_content: ユーザーアップロードのMarkdownテキスト（Noneならカスタム未使用）

    Returns:
        str: 結合されたナレッジベーステキスト
    """
    parts = []

    if preset_id:
        parts.append(load_preset(preset_id))

    if custom_content:
        parts.append(load_custom_knowledge(custom_content))

    if parts:
        return "\n\n---\n\n".join(parts)

    # 両方Noneの場合はデフォルト（既存のcore-criteria.md）
    return load_knowledge_base()


def load_reference_docs() -> list:
    """
    reference/ 内のMarkdownファイル一覧と内容を返す（UI一覧表示用）

    Returns:
        list[dict]: 各ドキュメントの情報
            - filename: ファイル名
            - path: フルパス
            - content: ファイル内容
    """
    if not _REFERENCE_DIR.exists():
        return []

    docs = []
    for md_file in sorted(_REFERENCE_DIR.glob("*.md")):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            docs.append({
                "filename": md_file.name,
                "path": str(md_file),
                "content": content,
            })
        except Exception:
            continue

    return docs


def save_reference_doc(filename: str, content: str) -> str:
    """
    参考資料をreference/ディレクトリに保存する

    Args:
        filename: 保存するファイル名（.md拡張子）
        content: Markdownテキスト

    Returns:
        str: 保存先のパス

    Raises:
        ValueError: ファイル名またはコンテンツが不正な場合
    """
    if not filename or not filename.endswith(".md"):
        raise ValueError("ファイル名は.md拡張子である必要があります")
    if not content or not content.strip():
        raise ValueError("コンテンツが空です")

    _REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    save_path = _REFERENCE_DIR / filename
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(save_path)


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
