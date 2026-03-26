"""
src/components/ui.py
UIヘルパーコンポーネント
"""


def render_page_header(title: str, description: str = "") -> str:
    """
    ページヘッダーをMarkdown形式で生成する

    Args:
        title (str): ページタイトル
        description (str, optional): ページ説明. デフォルトは空文字列.

    Returns:
        str: Markdown形式のページヘッダー

    Raises:
        TypeError: titleがNoneまたは文字列でない場合
    """
    # バリデーション: titleがNoneまたは文字列でない場合はエラー
    if title is None:
        raise TypeError("title must be a string, not None")
    if not isinstance(title, str):
        raise TypeError(f"title must be a string, not {type(title).__name__}")

    header = f"# {title}\n"

    if description:
        header += f"{description}\n"

    header += "\n---\n"

    return header
