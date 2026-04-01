"""
レイアウトコンポーネント

モダンなHR Tech/SaaSアプリのレイアウトパターンを提供
"""

import streamlit as st
from typing import Optional, List, Dict


def render_hero_header(
    title: str,
    subtitle: str,
    status_items: Optional[List[Dict[str, str]]] = None
) -> None:
    """
    ヒーローヘッダー（Stripe/Linear風）

    Args:
        title: メインタイトル
        subtitle: サブタイトル
        status_items: ステータス項目リスト [{"label": "...", "value": "...", "status": "success|warning|error"}]
    """
    status_html = ""
    if status_items:
        status_badges = ""
        for item in status_items:
            status_color_map = {
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#EF4444",
                "info": "#3B82F6"
            }
            color = status_color_map.get(item.get("status", "info"), "#6B7280")
            status_badges += f"""
            <div style="
                display: inline-block;
                padding: 6px 12px;
                background: {color}15;
                border: 1px solid {color}40;
                border-radius: 8px;
                margin-right: 8px;
                font-size: 0.875rem;
            ">
                <span style="color: {color}; font-weight: 600;">{item['label']}:</span>
                <span style="color: {color}; margin-left: 4px;">{item['value']}</span>
            </div>
            """
        status_html = f"""
        <div style="margin-top: 16px;">
            {status_badges}
        </div>
        """

    html = f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 48px 32px;
        margin-bottom: 32px;
        color: white;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    ">
        <div style="max-width: 900px;">
            <h1 style="
                font-size: 2.5rem;
                font-weight: 700;
                margin: 0 0 12px 0;
                letter-spacing: -0.02em;
                color: white;
            ">{title}</h1>
            <p style="
                font-size: 1.125rem;
                margin: 0;
                opacity: 0.95;
                line-height: 1.6;
                color: white;
            ">{subtitle}</p>
            {status_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_upload_zone(
    mode: str = "single",
    accepted_formats: List[str] = ["mp4", "mov", "avi", "webm"],
    max_size_mb: int = 200
) -> str:
    """
    大型アップロードゾーン（Notion/Dropbox風）

    Args:
        mode: "single" or "batch"
        accepted_formats: 受け入れ形式リスト
        max_size_mb: 最大サイズ（MB）

    Returns:
        HTMLマークアップ
    """
    mode_text = "動画ファイル" if mode == "single" else "複数の動画ファイル"
    mode_icon = "📹" if mode == "single" else "📁"
    formats_text = ", ".join([f.upper() for f in accepted_formats])

    html = f"""
    <div style="
        border: 2px dashed #CBD5E0;
        border-radius: 16px;
        padding: 48px 32px;
        text-align: center;
        background: linear-gradient(to bottom, #F9FAFB 0%, #FFFFFF 100%);
        transition: all 0.3s ease;
        margin: 24px 0;
    ">
        <div style="font-size: 4rem; margin-bottom: 16px;">{mode_icon}</div>
        <h3 style="
            font-size: 1.5rem;
            font-weight: 600;
            color: #1F2937;
            margin: 0 0 8px 0;
        ">
            {mode_text}をドラッグ&ドロップ
        </h3>
        <p style="
            font-size: 1rem;
            color: #6B7280;
            margin: 0 0 16px 0;
        ">
            または、クリックしてファイルを選択
        </p>
        <div style="
            display: inline-flex;
            gap: 24px;
            font-size: 0.875rem;
            color: #9CA3AF;
        ">
            <div>📎 対応形式: {formats_text}</div>
            <div>💾 最大サイズ: {max_size_mb}MB</div>
        </div>
    </div>
    """
    return html


def render_section_card(
    title: str,
    content: str,
    icon: Optional[str] = None,
    collapsible: bool = False
) -> str:
    """
    セクションカード（Linear/Notion風）

    Args:
        title: セクションタイトル
        content: コンテンツ
        icon: アイコン（絵文字）
        collapsible: 折りたたみ可能か

    Returns:
        HTMLマークアップ
    """
    icon_html = f'<span style="font-size: 1.5rem; margin-right: 12px;">{icon}</span>' if icon else ""

    html = f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    ">
        <h3 style="
            font-size: 1.25rem;
            font-weight: 600;
            color: #1F2937;
            margin: 0 0 16px 0;
            display: flex;
            align-items: center;
        ">
            {icon_html}{title}
        </h3>
        <div style="
            color: #374151;
            line-height: 1.6;
        ">
            {content}
        </div>
    </div>
    """
    return html


def render_mode_selector(current_mode: str = "single") -> str:
    """
    モード選択カード（単一/バッチ）

    Args:
        current_mode: 現在のモード

    Returns:
        HTMLマークアップ
    """
    single_selected = current_mode == "single"
    batch_selected = current_mode == "batch"

    single_style = """
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: 2px solid #667eea;
    """ if single_selected else """
        background: #FFFFFF;
        color: #6B7280;
        border: 2px solid #E5E7EB;
    """

    batch_style = """
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: 2px solid #667eea;
    """ if batch_selected else """
        background: #FFFFFF;
        color: #6B7280;
        border: 2px solid #E5E7EB;
    """

    html = f"""
    <div style="
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin: 24px 0;
    ">
        <div style="
            {single_style}
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 12px;">📹</div>
            <h3 style="font-size: 1.125rem; font-weight: 600; margin: 0 0 8px 0;">単一動画解析</h3>
            <p style="font-size: 0.875rem; margin: 0; opacity: 0.9;">
                1つの面談動画を詳細に解析
            </p>
        </div>
        <div style="
            {batch_style}
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 12px;">📁</div>
            <h3 style="font-size: 1.125rem; font-weight: 600; margin: 0 0 8px 0;">バッチ処理</h3>
            <p style="font-size: 0.875rem; margin: 0; opacity: 0.9;">
                複数の候補者を一括で比較分析
            </p>
        </div>
    </div>
    """
    return html


def render_step_indicator(steps: List[Dict[str, str]], current_step: int = 0) -> str:
    """
    ステップインジケータ（Stripe風）

    Args:
        steps: ステップリスト [{"number": "1", "label": "アップロード", "status": "completed|current|pending"}]
        current_step: 現在のステップ（0始まり）

    Returns:
        HTMLマークアップ
    """
    steps_html = ""
    for idx, step in enumerate(steps):
        status = step.get("status", "pending")
        if idx < current_step:
            status = "completed"
        elif idx == current_step:
            status = "current"
        else:
            status = "pending"

        status_styles = {
            "completed": {
                "bg": "#10B981",
                "text": "#FFFFFF",
                "border": "#10B981"
            },
            "current": {
                "bg": "#3B82F6",
                "text": "#FFFFFF",
                "border": "#3B82F6"
            },
            "pending": {
                "bg": "#F3F4F6",
                "text": "#9CA3AF",
                "border": "#E5E7EB"
            }
        }

        style = status_styles[status]
        connector = """
        <div style="
            flex: 1;
            height: 2px;
            background: #E5E7EB;
            margin: 0 8px;
        "></div>
        """ if idx < len(steps) - 1 else ""

        steps_html += f"""
        <div style="display: flex; align-items: center;">
            <div style="text-align: center;">
                <div style="
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: {style['bg']};
                    border: 2px solid {style['border']};
                    color: {style['text']};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 600;
                    font-size: 1rem;
                    margin: 0 auto 8px auto;
                ">
                    {step['number']}
                </div>
                <div style="
                    font-size: 0.75rem;
                    color: {style['text']};
                    font-weight: 500;
                ">
                    {step['label']}
                </div>
            </div>
            {connector}
        </div>
        """

    html = f"""
    <div style="
        display: flex;
        align-items: center;
        padding: 24px;
        background: #FFFFFF;
        border-radius: 12px;
        margin: 24px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    ">
        {steps_html}
    </div>
    """
    return html


def render_info_banner(
    message: str,
    banner_type: str = "info",
    icon: Optional[str] = None,
    dismissible: bool = False
) -> str:
    """
    情報バナー（Datadog/GitHub風）

    Args:
        message: メッセージ
        banner_type: "info" | "success" | "warning" | "error"
        icon: カスタムアイコン
        dismissible: 閉じるボタンを表示

    Returns:
        HTMLマークアップ
    """
    config = {
        "info": {
            "bg": "#EFF6FF",
            "border": "#3B82F6",
            "text": "#1E40AF",
            "icon": icon or "ℹ️"
        },
        "success": {
            "bg": "#D1FAE5",
            "border": "#10B981",
            "text": "#065F46",
            "icon": icon or "✅"
        },
        "warning": {
            "bg": "#FEF3C7",
            "border": "#F59E0B",
            "text": "#92400E",
            "icon": icon or "⚠️"
        },
        "error": {
            "bg": "#FEE2E2",
            "border": "#EF4444",
            "text": "#991B1B",
            "icon": icon or "❌"
        }
    }

    style = config.get(banner_type, config["info"])

    html = f"""
    <div style="
        background: {style['bg']};
        border-left: 4px solid {style['border']};
        border-radius: 8px;
        padding: 16px 20px;
        margin: 16px 0;
        color: {style['text']};
        display: flex;
        align-items: center;
        gap: 12px;
    ">
        <span style="font-size: 1.5rem;">{style['icon']}</span>
        <div style="flex: 1; font-size: 0.9375rem; line-height: 1.5;">
            {message}
        </div>
    </div>
    """
    return html


def render_footer(
    version: str = "1.0.0",
    github_url: Optional[str] = None,
    show_status: bool = True,
    custom_links: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    フッター（Stripe/Linear/Notion風）

    Args:
        version: バージョン番号
        github_url: GitHubリポジトリURL
        show_status: ステータス表示
        custom_links: カスタムリンク [{"label": "...", "url": "..."}]

    Returns:
        HTMLマークアップ
    """
    from datetime import datetime
    current_year = datetime.now().year

    # ステータスインジケータ
    status_html = ""
    if show_status:
        status_html = """
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #10B981;
                box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
            "></div>
            <span style="font-size: 0.875rem; color: #10B981; font-weight: 500;">
                All Systems Operational
            </span>
        </div>
        """

    # GitHubリンク
    github_html = ""
    if github_url:
        github_html = f"""
        <a href="{github_url}" target="_blank" style="
            color: #6B7280;
            text-decoration: none;
            font-size: 0.875rem;
            transition: color 0.2s;
        ">
            <span style="margin-right: 4px;">⭐</span>GitHub
        </a>
        """

    # カスタムリンク
    custom_links_html = ""
    if custom_links:
        links_list = []
        for link in custom_links:
            links_list.append(f"""
            <a href="{link['url']}" target="_blank" style="
                color: #6B7280;
                text-decoration: none;
                font-size: 0.875rem;
                transition: color 0.2s;
            ">{link['label']}</a>
            """)
        custom_links_html = " • ".join(links_list)

    html = f"""
    <div style="
        margin-top: 64px;
        padding: 32px 0;
        border-top: 1px solid #E5E7EB;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        ">
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="
                    font-size: 0.875rem;
                    color: #6B7280;
                ">
                    © {current_year} AI面談動画解析システム v{version}
                </div>
                <div style="
                    font-size: 0.75rem;
                    color: #9CA3AF;
                ">
                    Powered by Gemini AI • Built with Streamlit & Plotly
                </div>
            </div>
            <div style="
                display: flex;
                align-items: center;
                gap: 24px;
                flex-wrap: wrap;
            ">
                {status_html}
                {github_html}
                {custom_links_html if custom_links_html else ""}
            </div>
        </div>
    </div>
    """
    return html


def render_sidebar_nav(
    current_page: str,
    pages: List[Dict[str, str]]
) -> None:
    """
    サイドバーナビゲーション（Linear風）

    Args:
        current_page: 現在のページID
        pages: ページリスト [{"id": "...", "label": "...", "icon": "..."}]
    """
    import streamlit as st

    st.sidebar.markdown("""
    <style>
    .nav-item {
        padding: 12px 16px;
        border-radius: 8px;
        margin: 4px 0;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 0.9375rem;
        font-weight: 500;
    }
    .nav-item:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    .nav-item.active {
        background: rgba(255, 255, 255, 0.15);
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    for page in pages:
        is_active = page['id'] == current_page
        class_name = "nav-item active" if is_active else "nav-item"
        icon = page.get('icon', '•')

        if st.sidebar.button(
            f"{icon} {page['label']}",
            key=f"nav_{page['id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state['current_page'] = page['id']
            st.rerun()


def render_empty_state(
    title: str,
    description: str,
    icon: str = "📭",
    action_label: Optional[str] = None
) -> str:
    """
    空状態表示（Notion/Linear風）

    Args:
        title: タイトル
        description: 説明文
        icon: アイコン
        action_label: アクションボタンラベル

    Returns:
        HTMLマークアップ
    """
    action_html = ""
    if action_label:
        action_html = f"""
        <div style="margin-top: 24px;">
            <button style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            ">
                {action_label}
            </button>
        </div>
        """

    html = f"""
    <div style="
        text-align: center;
        padding: 80px 32px;
        background: #F9FAFB;
        border-radius: 16px;
        margin: 32px 0;
    ">
        <div style="font-size: 4rem; margin-bottom: 24px;">{icon}</div>
        <h3 style="
            font-size: 1.5rem;
            font-weight: 600;
            color: #1F2937;
            margin: 0 0 12px 0;
        ">{title}</h3>
        <p style="
            font-size: 1rem;
            color: #6B7280;
            margin: 0;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        ">{description}</p>
        {action_html}
    </div>
    """
    return html
