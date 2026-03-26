"""
src/components/styles.py
カスタムCSSスタイル定義・注入
"""


def inject_custom_css() -> str:
    """
    企業向けSaaS風のカスタムCSSを注入する

    Returns:
        str: <style>タグでラップされたCSS
    """
    css = """<style>
    /* Google Fonts読み込み */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    /* ========== カラーパレット（CSS変数） ========== */
    :root {
        /* プライマリカラー */
        --primary-dark-navy: #1B2559;
        --primary-blue: #4F6AF0;
        --primary-light-blue: #6B84FF;

        /* セマンティックカラー */
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;

        /* ニュートラルカラー */
        --background: #F8FAFC;
        --card-bg: #FFFFFF;
        --text-primary: #1E293B;
        --text-secondary: #64748B;
        --border-color: #E2E8F0;

        /* スペーシング */
        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;

        /* ボーダーRadius */
        --radius-sm: 6px;
        --radius-md: 12px;
        --radius-lg: 16px;

        /* シャドウ */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }

    /* ========== グローバルスタイル（強化版）========== */
    html, body, .stApp, .main {
        font-family: 'Noto Sans JP', 'Inter', sans-serif !important;
        background-color: var(--background) !important;
        color: var(--text-primary) !important;
    }

    /* メインコンテンツエリアの余白を最小化 */
    .block-container,
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 100% !important;
    }

    /* Streamlit のデフォルトヘッダー余白を削減 */
    .main {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    /* 全ての要素の余白を削減 */
    .element-container {
        margin: 0.25rem 0 !important;
    }

    /* ツールバー（Deploy, メニュー）の後の余白を削減 */
    header[data-testid="stHeader"] + div {
        padding-top: 0 !important;
    }

    /* 見出しの余白を削減 */
    h1, .stMarkdown h1 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    h2, .stMarkdown h2 {
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }

    h3, .stMarkdown h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.25rem !important;
    }

    /* 段落の余白を削減 */
    p, .stMarkdown p {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }

    /* Streamlit全体の背景 */
    .stApp {
        background-color: var(--background) !important;
    }

    /* タイポグラフィ（強化版）*/
    h1, .stMarkdown h1, [data-testid="stMarkdownContainer"] h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #1B2559 !important;
        margin-bottom: 1rem !important;
        letter-spacing: -0.02em !important;
    }

    h2, .stMarkdown h2, [data-testid="stMarkdownContainer"] h2 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #1B2559 !important;
        margin-bottom: 0.75rem !important;
        border-bottom: 2px solid #E2E8F0 !important;
        padding-bottom: 0.5rem !important;
    }

    h3, .stMarkdown h3, [data-testid="stMarkdownContainer"] h3 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        margin-bottom: 0.5rem !important;
    }

    p, .stMarkdown p, [data-testid="stMarkdownContainer"] p {
        font-size: 0.95rem !important;
        color: #64748B !important;
        line-height: 1.7 !important;
    }

    /* ========== サイドバースタイル（複数セレクタで対応）========== */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    .css-1d391kg,
    aside {
        background: linear-gradient(180deg, #1B2559 0%, #1E2D6D 100%) !important;
        box-shadow: var(--shadow-lg) !important;
    }

    [data-testid="stSidebar"] *,
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* サイドバーナビゲーションボタン */
    [data-testid="stSidebar"] [role="radiogroup"] label,
    section[data-testid="stSidebar"] [role="radiogroup"] label {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: var(--radius-sm) !important;
        padding: var(--spacing-sm) var(--spacing-md) !important;
        margin-bottom: var(--spacing-xs) !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover,
    section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.15) !important;
        transform: translateX(4px) !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"],
    section[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] {
        background-color: var(--primary-blue) !important;
        font-weight: 600 !important;
    }

    /* ========== カード型レイアウト（コンパクト版）========== */
    .stCard {
        background-color: var(--card-bg);
        border-radius: var(--radius-md);
        padding: 0.75rem !important;
        box-shadow: var(--shadow-sm);
        margin-bottom: 0.5rem !important;
    }

    /* ========== ボタンスタイル（プライマリ）========== */
    .stButton > button,
    button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #4F6AF0 0%, #6C63FF 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(79,106,240,0.3) !important;
        cursor: pointer !important;
    }

    .stButton > button:hover,
    button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #6C63FF 0%, #8B7FFF 100%) !important;
        box-shadow: 0 4px 12px rgba(79,106,240,0.4) !important;
        transform: translateY(-1px) !important;
    }

    /* ========== タブスタイル（シンプル＆確実版）========== */
    /* タブコンテナ全体 */
    .stTabs {
        background-color: #FFFFFF !important;
        border-bottom: 2px solid #E2E8F0 !important;
    }

    /* タブリスト */
    .stTabs [role="tablist"] {
        gap: 0 !important;
        border-bottom: 2px solid #E2E8F0 !important;
    }

    /* 個々のタブボタン */
    .stTabs button[role="tab"] {
        background-color: transparent !important;
        color: #64748B !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        border-bottom: 3px solid transparent !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }

    /* タブボタンのホバー状態 */
    .stTabs button[role="tab"]:hover {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
        border-bottom-color: #94A3B8 !important;
    }

    /* 選択中のタブ */
    .stTabs button[role="tab"][aria-selected="true"] {
        background-color: #EFF6FF !important;
        color: #1B2559 !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #1B2559 !important;
    }

    /* タブパネル（コンテンツエリア）- コンパクト */
    .stTabs [role="tabpanel"] {
        padding-top: 0.75rem !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    /* ========== テーブルスタイル ========== */
    .dataframe {
        border: 1px solid var(--border-color);
        border-radius: var(--radius-sm);
        overflow: hidden;
    }

    .dataframe thead th {
        background-color: var(--primary-dark-navy);
        color: #FFFFFF;
        font-weight: 600;
        padding: var(--spacing-sm);
    }

    .dataframe tbody tr:nth-child(even) {
        background-color: #F9FAFB;
    }

    .dataframe tbody td {
        padding: var(--spacing-sm);
        color: var(--text-primary);
    }

    /* ========== メトリクスカード（コンパクト版）========== */
    [data-testid="stMetric"] {
        background-color: var(--card-bg);
        border-radius: var(--radius-md);
        padding: 0.5rem !important;
        box-shadow: var(--shadow-sm);
        margin: 0.25rem 0 !important;
    }

    [data-testid="stMetric"] label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--primary-dark-navy);
        font-size: 1.875rem;
        font-weight: 700;
    }
    </style>"""
    return css
