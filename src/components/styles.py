"""
src/components/styles.py
カスタムCSSスタイル定義・注入 — ライトテーマ（WCAG準拠）
"""


def inject_custom_css() -> str:
    """
    ライトテーマのカスタムCSSを注入する

    Returns:
        str: <style>タグでラップされたCSS
    """
    css = """<style>
    /* Google Fonts読み込み */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    /* ========== カラーパレット（CSS変数）— ライトテーマ ========== */
    :root {
        --primary:       #2563EB;
        --primary-dark:  #1E40AF;
        --bg-main:       #FFFFFF;
        --bg-section:    #F8FAFC;
        --bg-card:       #FFFFFF;
        --text-main:     #1E293B;
        --text-sub:      #475569;
        --text-muted:    #64748B;
        --border:        #E2E8F0;
        --border-strong: #CBD5E1;
        --accent-green:  #059669;
        --accent-red:    #DC2626;
        --radius-sm:     6px;
        --radius-md:     8px;
        --shadow-sm:     0 1px 3px rgba(0,0,0,0.08);
        --shadow-md:     0 4px 12px rgba(0,0,0,0.08);
    }

    /* ========== グローバル ========== */
    html, body, .stApp, .main {
        font-family: 'Noto Sans JP', 'Inter', sans-serif !important;
        background-color: #FFFFFF !important;
        color: #1E293B !important;
    }

    .stApp {
        background-color: #FFFFFF !important;
    }

    /* ========== 余白削減 ========== */
    .block-container, .main .block-container {
        padding-top: 0.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 100% !important;
    }

    .main, section.main { padding-top: 0 !important; margin-top: 0 !important; }
    .element-container { margin: 0.25rem 0 !important; }

    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeaderSpacer"] { display: none !important; }

    /* ========== タイポグラフィ ========== */
    h1, .stMarkdown h1, [data-testid="stMarkdownContainer"] h1 {
        font-size: 1.75rem !important; font-weight: 700 !important;
        color: #0F172A !important; margin-bottom: 0.75rem !important;
    }
    h2, .stMarkdown h2, [data-testid="stMarkdownContainer"] h2 {
        font-size: 1.375rem !important; font-weight: 600 !important;
        color: #0F172A !important; margin-bottom: 0.75rem !important;
        border-bottom: 2px solid var(--border-strong) !important;
        padding-bottom: 0.5rem !important;
    }
    h3, .stMarkdown h3, [data-testid="stMarkdownContainer"] h3 {
        font-size: 1.125rem !important; font-weight: 600 !important;
        color: #1E293B !important; margin-bottom: 0.5rem !important;
    }
    p, .stMarkdown p, [data-testid="stMarkdownContainer"] p {
        font-size: 0.95rem !important; color: #334155 !important;
        line-height: 1.7 !important;
    }

    /* ========== サイドバー ========== */
    [data-testid="stSidebar"], section[data-testid="stSidebar"], aside {
        background: linear-gradient(180deg, #1B2559 0%, #1E2D6D 100%) !important;
        box-shadow: var(--shadow-md) !important;
    }
    [data-testid="stSidebar"] *, section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* ========== タブ ========== */
    .stTabs { background-color: #FFFFFF !important; margin-bottom: 1rem !important; }

    .stTabs [role="tablist"] {
        position: sticky !important; top: 0 !important; z-index: 999 !important;
        background: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        border-bottom: 1px solid var(--border) !important;
        gap: 0 !important; padding: 0 1rem !important; margin: 0 -1rem !important;
    }

    .stTabs button[role="tab"] {
        background-color: transparent !important;
        color: #64748B !important;
        font-weight: 500 !important; font-size: 0.9rem !important;
        border: none !important; border-bottom: 3px solid transparent !important;
        padding: 0 1.25rem !important; height: 55px !important;
        transition: all 0.2s ease !important;
    }
    .stTabs button[role="tab"]:hover {
        background-color: #F8FAFC !important; color: #1E293B !important;
        border-bottom-color: var(--border-strong) !important;
    }
    .stTabs button[role="tab"][aria-selected="true"] {
        background-color: #EFF6FF !important; color: #1B2559 !important;
        font-weight: 600 !important; border-bottom: 3px solid #1B2559 !important;
    }
    .stTabs [role="tabpanel"] { padding-top: 1rem !important; }

    /* ========== ボタン（紺色ベースに統一・ヘルプボタン除外）========== */
    .stButton > button,
    button[kind="primary"],
    button[data-testid="baseButton-primary"],
    button[data-testid="stFormSubmitButton"] {
        background: #1B2559 !important;
        color: #FFFFFF !important; border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 0.5rem 1.5rem !important; font-weight: 600 !important;
        font-size: 1rem !important; transition: background 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(27,37,89,0.25) !important;
    }
    .stButton > button:hover,
    button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover,
    button[data-testid="stFormSubmitButton"]:hover {
        background: #2A3A7D !important;
        box-shadow: 0 4px 12px rgba(27,37,89,0.35) !important;
    }
    .stButton > button *, button[kind="primary"] * { color: #FFFFFF !important; }

    button[data-testid="stDownloadButton"] {
        background: #059669 !important;
        color: #FFFFFF !important; font-weight: 600 !important;
    }
    button[data-testid="stDownloadButton"]:hover { background: #047857 !important; }
    button[data-testid="stDownloadButton"] * { color: #FFFFFF !important; }

    button[kind="secondary"] { background: #64748B !important; color: #FFFFFF !important; }
    button[kind="secondary"]:hover { background: #475569 !important; }

    /* ヘルプアイコン（?）— 完全リセット後に最小スタイルを適用 */
    button.stTooltipHoverTarget,
    button[data-testid="stTooltipHoverTarget"] {
        all: unset !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: help !important;
        border-radius: 50% !important;
        padding: 2px !important;
        line-height: 0 !important;
    }
    button.stTooltipHoverTarget:hover,
    button[data-testid="stTooltipHoverTarget"]:hover {
        background: #F1F5F9 !important;
    }
    /* SVGアイコンのstrokeを明るいグレーに（fillではなくstrokeを使用） */
    button.stTooltipHoverTarget svg.icon,
    button[data-testid="stTooltipHoverTarget"] svg.icon {
        stroke: #94A3B8 !important;
        stroke-width: 1.5px !important;
    }
    button.stTooltipHoverTarget svg,
    button[data-testid="stTooltipHoverTarget"] svg {
        width: 16px !important;
        height: 16px !important;
    }

    /* ========== テーブル ========== */
    .dataframe { border: 1px solid var(--border-strong); border-radius: var(--radius-sm); overflow: hidden; }
    .dataframe thead th {
        background-color: #F1F5F9; color: #0F172A;
        font-weight: 600; padding: 0.5rem;
        border-bottom: 2px solid var(--border-strong);
    }
    .dataframe tbody tr:nth-child(even) { background-color: #F8FAFC; }
    .dataframe tbody td { padding: 0.5rem; color: #1E293B; border-bottom: 1px solid var(--border); }

    /* ========== メトリクスカード ========== */
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border-radius: var(--radius-md);
        padding: 0.75rem !important;
        box-shadow: var(--shadow-sm); border: 1px solid var(--border);
        margin: 0.25rem 0 !important;
    }
    [data-testid="stMetric"] label { color: #475569 !important; font-size: 0.875rem; font-weight: 600; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0F172A !important; font-size: 1.875rem; font-weight: 700; }

    /* ========== モダンヘッダー ========== */
    .modern-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.75rem 1.5rem; margin: -1rem -1rem 1rem -1rem;
        background: linear-gradient(135deg, #1B2559 0%, #2A3A7D 100%);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .modern-header-left { display: flex; align-items: baseline; gap: 0.75rem; }
    .modern-header-logo { font-size: 1.375rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.02em; }
    .modern-header-version {
        font-size: 0.75rem; font-weight: 500;
        color: rgba(255,255,255,0.7);
        background: rgba(255,255,255,0.1);
        padding: 0.2rem 0.5rem; border-radius: 4px;
    }
    .modern-header-powered { font-size: 0.875rem; color: rgba(255,255,255,0.8); }

    /* ========== Streamlitヘッダー ========== */
    header[data-testid="stHeader"] {
        background: #FFFFFF !important;
        border-bottom: 2px solid var(--border) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    button[data-testid="stAppDeployButton"], button[kind="header"] {
        background-color: #FFFFFF !important; color: #1B2559 !important;
        border: 2px solid #1B2559 !important;
        padding: 0.5rem 1rem !important; font-weight: 600 !important;
        border-radius: var(--radius-md) !important;
    }
    button[data-testid="stAppDeployButton"]:hover, button[kind="header"]:hover {
        background-color: #1B2559 !important; color: #FFFFFF !important;
    }
    button[kind="headerNoPadding"] {
        background-color: #FFFFFF !important; color: #1B2559 !important;
        border: 2px solid #1B2559 !important; border-radius: var(--radius-md) !important;
        padding: 0.4rem !important;
    }
    button[kind="headerNoPadding"]:hover {
        background-color: #1B2559 !important; color: #FFFFFF !important;
    }
    button[kind="headerNoPadding"] svg path { fill: #1B2559 !important; }
    button[kind="headerNoPadding"]:hover svg path { fill: #FFFFFF !important; }
    </style>"""
    return css
