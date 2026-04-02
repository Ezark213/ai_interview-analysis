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
        /* ========================================
           メインカラー
           ======================================== */
        --primary-dark: #1E3A8A;
        --primary-darker: #1E40AF;
        --primary-accent: #3B82F6;

        /* ========================================
           背景カラー
           ======================================== */
        --background-dark: #0F172A;
        --background-medium: #1E293B;
        --background-light: #334155;

        /* ========================================
           テキストカラー
           ======================================== */
        --text-white: #FFFFFF;
        --text-gray: #E2E8F0;
        --text-muted: #94A3B8;

        /* ========================================
           アクセントカラー（ステータス）
           ======================================== */
        --accent-blue: #3B82F6;
        --accent-green: #10B981;
        --accent-red: #EF4444;
        --accent-yellow: #F59E0B;

        /* ========================================
           データビジュアライゼーション用カラー
           ======================================== */
        --viz-color-1: #3B82F6;
        --viz-color-2: #10B981;
        --viz-color-3: #F59E0B;
        --viz-color-4: #EF4444;
        --viz-color-5: #8B5CF6;
        --viz-color-6: #EC4899;
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

    /* ========== ボタンスタイル（高コントラスト版）========== */

    /* すべてのボタンの基本スタイル - 明るいブルー背景、白文字、高コントラスト */
    button,
    .stButton > button,
    button[kind="primary"],
    button[kind="secondary"],
    button[data-testid="baseButton-primary"],
    button[data-testid="baseButton-secondary"],
    button[data-testid="stFormSubmitButton"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4) !important;
        cursor: pointer !important;
    }

    /* ボタンのホバー状態 - さらに明るく */
    button:hover,
    .stButton > button:hover,
    button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover,
    button[data-testid="stFormSubmitButton"]:hover {
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.5) !important;
        transform: translateY(-2px) !important;
    }

    /* ボタン内のテキスト要素 - 強制的に真っ白・bold */
    button *,
    .stButton > button *,
    button[kind="primary"] *,
    button[data-testid="baseButton-primary"] *,
    button[data-testid="stFormSubmitButton"] * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* フォーム送信ボタンの特別対応 - 明るいブルー、真っ白・bold */
    button[data-testid="stFormSubmitButton"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    button[data-testid="stFormSubmitButton"] > div,
    button[data-testid="stFormSubmitButton"] > div > div,
    button[data-testid="stFormSubmitButton"] p,
    button[data-testid="stFormSubmitButton"] span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* ダウンロードボタン - 明るいグリーン */
    button[data-testid="stDownloadButton"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    button[data-testid="stDownloadButton"] * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    button[data-testid="stDownloadButton"]:hover {
        background: linear-gradient(135deg, #34D399 0%, #10B981 100%) !important;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.5) !important;
    }

    /* セカンダリボタン - グレー */
    button[kind="secondary"] {
        background: #64748B !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    button[kind="secondary"]:hover {
        background: #475569 !important;
    }

    /* ========== タブスタイル（モダンナビゲーションバー風）========== */

    /* タブコンテナ全体 */
    .stTabs {
        background-color: #FFFFFF !important;
        margin-bottom: 1rem !important;
    }

    /* タブリスト（上部固定） */
    .stTabs [role="tablist"] {
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
        background: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
        border-bottom: 1px solid #E2E8F0 !important;
        gap: 0 !important;
        padding: 0 1rem !important;
        margin: 0 -1rem !important;
    }

    /* 個々のタブボタン */
    .stTabs button[role="tab"] {
        background-color: transparent !important;
        color: #64748B !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        border: none !important;
        border-bottom: 3px solid transparent !important;
        padding: 0 1.25rem !important;
        height: 55px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        letter-spacing: 0.01em !important;
    }

    /* タブボタンのホバー状態 */
    .stTabs button[role="tab"]:hover {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
        border-bottom-color: #CBD5E1 !important;
    }

    /* 選択中のタブ */
    .stTabs button[role="tab"][aria-selected="true"] {
        background-color: #EFF6FF !important;
        color: #1B2559 !important;
        font-weight: 600 !important;
        border-bottom: 3px solid #1B2559 !important;
    }

    /* タブパネル（コンテンツエリア） */
    .stTabs [role="tabpanel"] {
        padding-top: 1rem !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    /* レスポンシブ対応（タブレット） */
    @media (max-width: 1024px) {
        .stTabs button[role="tab"] {
            font-size: 0.85rem !important;
            padding: 0 1rem !important;
        }
    }

    /* レスポンシブ対応（モバイル） */
    @media (max-width: 768px) {
        .stTabs button[role="tab"] {
            font-size: 0.8rem !important;
            padding: 0 0.75rem !important;
            height: 50px !important;
        }

        .stTabs [role="tablist"] {
            padding: 0 0.5rem !important;
            margin: 0 -0.5rem !important;
        }
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

    /* ========== グリッドシステム（新規追加）========== */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: var(--spacing-md);
    }

    .grid-col-4 {
        grid-column: span 4;
    }

    .grid-col-6 {
        grid-column: span 6;
    }

    .grid-col-8 {
        grid-column: span 8;
    }

    .grid-col-12 {
        grid-column: span 12;
    }

    /* ========== Plotlyチャートスタイル（新規追加）========== */
    .js-plotly-plot {
        border-radius: var(--radius-md);
        overflow: hidden;
    }

    /* ========== 追加のユーティリティクラス（新規追加）========== */
    .text-center {
        text-align: center;
    }

    .text-right {
        text-align: right;
    }

    .mt-1 {
        margin-top: var(--spacing-sm);
    }

    .mt-2 {
        margin-top: var(--spacing-md);
    }

    .mt-3 {
        margin-top: var(--spacing-lg);
    }

    .mb-1 {
        margin-bottom: var(--spacing-sm);
    }

    .mb-2 {
        margin-bottom: var(--spacing-md);
    }

    .mb-3 {
        margin-bottom: var(--spacing-lg);
    }

    /* ========== モダンヘッダー（Spotify/Portfolio Wise風）========== */
    .modern-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 1.5rem;
        margin: -1rem -1rem 1rem -1rem;
        background: linear-gradient(135deg, #1B2559 0%, #2A3A7D 100%);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-bottom: none;
    }

    .modern-header-left {
        display: flex;
        align-items: baseline;
        gap: 0.75rem;
    }

    .modern-header-logo {
        font-size: 1.5rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }

    .modern-header-version {
        font-size: 0.75rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.6);
        background: rgba(255, 255, 255, 0.1);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
    }

    .modern-header-right {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .modern-header-powered {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.8);
        font-weight: 400;
    }

    /* レスポンシブ対応（モバイル） */
    @media (max-width: 768px) {
        .modern-header {
            padding: 0.75rem 1rem;
            margin: -0.5rem -0.5rem 0.75rem -0.5rem;
        }

        .modern-header-logo {
            font-size: 1.25rem;
        }

        .modern-header-version {
            font-size: 0.65rem;
            padding: 0.2rem 0.4rem;
        }

        .modern-header-powered {
            font-size: 0.75rem;
        }
    }

    /* ========== Streamlitヘッダーのスタイル調整（高コントラスト版） ========== */

    /* ヘッダー全体 */
    header[data-testid="stHeader"] {
        background: #FFFFFF !important;
        padding: 0.5rem 1rem !important;
        border-bottom: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }

    /* Deployボタン - 白背景、ダークテキスト、明確な境界線 */
    button[data-testid="stAppDeployButton"],
    button[kind="header"] {
        background-color: #FFFFFF !important;
        color: #1B2559 !important;
        border: 2px solid #1B2559 !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(27, 37, 89, 0.2) !important;
    }

    button[data-testid="stAppDeployButton"]:hover,
    button[kind="header"]:hover {
        background-color: #1B2559 !important;
        color: #FFFFFF !important;
        border-color: #1B2559 !important;
        box-shadow: 0 4px 12px rgba(27, 37, 89, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* Deployボタン内のすべての要素 */
    button[data-testid="stAppDeployButton"] *,
    button[kind="header"] * {
        color: #1B2559 !important;
        font-weight: 600 !important;
    }

    button[data-testid="stAppDeployButton"]:hover *,
    button[kind="header"]:hover * {
        color: #FFFFFF !important;
    }

    /* メニューボタン（3点リーダー）- 同様のスタイル */
    button[kind="headerNoPadding"] {
        background-color: #FFFFFF !important;
        color: #1B2559 !important;
        border: 2px solid #1B2559 !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(27, 37, 89, 0.2) !important;
    }

    button[kind="headerNoPadding"]:hover {
        background-color: #1B2559 !important;
        color: #FFFFFF !important;
        border-color: #1B2559 !important;
        box-shadow: 0 4px 12px rgba(27, 37, 89, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* メニューボタンのアイコン（SVG） */
    button[kind="headerNoPadding"] svg,
    button[kind="headerNoPadding"] path {
        fill: #1B2559 !important;
        color: #1B2559 !important;
        stroke: #1B2559 !important;
    }

    button[kind="headerNoPadding"]:hover svg,
    button[kind="headerNoPadding"]:hover path {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
        stroke: #FFFFFF !important;
    }

    /* ========== 全体の余白削減（完全版） ========== */

    /* ページ全体の上部余白を完全に0に */
    html, body {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Streamlitアプリ全体の余白を削除 */
    .stApp {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* AppViewContainerの余白を削除 */
    [data-testid="stAppViewContainer"],
    .appview-container,
    div.appview-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* メインコンテンツエリアを上に詰める */
    .main,
    section.main,
    [data-testid="stMain"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* メインコンテンツの最初の子要素の余白削除 */
    .main > div:first-child,
    section.main > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* ブロックコンテナの上部余白削減 */
    .block-container,
    [data-testid="block-container"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* ヘッダー直下の余白削減 */
    header[data-testid="stHeader"] + div,
    header + section {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* modern-headerの上部余白削減 */
    .modern-header {
        margin-top: 0 !important;
        padding-top: 0.5rem !important;
    }

    /* option-menuとの間隔調整 */
    .streamlit-option-menu {
        margin-top: 0.5rem !important;
    }

    /* Streamlitのデフォルトツールバーがある場合の余白削除 */
    [data-testid="stToolbar"] {
        display: none !important;
    }

    /* デコレーション要素の余白削除 */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* ヘッダースペーサーの削除 */
    [data-testid="stHeaderSpacer"] {
        display: none !important;
    }

    /* ========== ヘルプマーク（?）- 高コントラスト版 ========== */

    /* ヘルプアイコンボタン - ダークブルー背景、白アイコン、円形 */
    [data-testid="stMarkdownHelpIcon"],
    .stMarkdownHelpIcon,
    button[title*="Help"],
    button[aria-label*="Help"],
    button[aria-label*="help"] {
        color: #FFFFFF !important;
        background-color: #1B2559 !important;
        border-radius: 50% !important;
        padding: 0.25rem !important;
        border: none !important;
        box-shadow: 0 2px 6px rgba(27, 37, 89, 0.3) !important;
        width: 24px !important;
        height: 24px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* ヘルプアイコン内のSVG要素を白色に */
    [data-testid="stMarkdownHelpIcon"] svg,
    .stMarkdownHelpIcon svg,
    button[title*="Help"] svg,
    button[aria-label*="Help"] svg,
    button[aria-label*="help"] svg,
    [data-testid="stMarkdownHelpIcon"] path,
    .stMarkdownHelpIcon path,
    button[title*="Help"] path,
    button[aria-label*="Help"] path,
    button[aria-label*="help"] path,
    [data-testid="stMarkdownHelpIcon"] circle,
    .stMarkdownHelpIcon circle,
    button[title*="Help"] circle,
    button[aria-label*="Help"] circle,
    button[aria-label*="help"] circle {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
        stroke: #FFFFFF !important;
    }

    /* ヘルプアイコンのホバー時 - 明るいブルーに */
    [data-testid="stMarkdownHelpIcon"]:hover,
    .stMarkdownHelpIcon:hover,
    button[title*="Help"]:hover,
    button[aria-label*="Help"]:hover,
    button[aria-label*="help"]:hover {
        color: #FFFFFF !important;
        background-color: #3B82F6 !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
        transform: scale(1.1) !important;
    }

    [data-testid="stMarkdownHelpIcon"]:hover svg,
    .stMarkdownHelpIcon:hover svg,
    button[title*="Help"]:hover svg,
    button[aria-label*="Help"]:hover svg,
    button[aria-label*="help"]:hover svg,
    [data-testid="stMarkdownHelpIcon"]:hover path,
    .stMarkdownHelpIcon:hover path,
    button[title*="Help"]:hover path,
    button[aria-label*="Help"]:hover path,
    button[aria-label*="help"]:hover path,
    [data-testid="stMarkdownHelpIcon"]:hover circle,
    .stMarkdownHelpIcon:hover circle,
    button[title*="Help"]:hover circle,
    button[aria-label*="Help"]:hover circle,
    button[aria-label*="help"]:hover circle {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
        stroke: #FFFFFF !important;
    }

    /* ========== パスワード表示ボタン（目アイコン）- 高コントラスト版 ========== */

    /* パスワード入力欄の目アイコンボタン */
    input[type="password"] + button,
    button[data-testid="StyledIconButton"],
    .stTextInput button {
        background-color: #F1F5F9 !important;
        color: #475569 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        padding: 0.4rem !important;
        transition: all 0.2s ease !important;
    }

    input[type="password"] + button:hover,
    button[data-testid="StyledIconButton"]:hover,
    .stTextInput button:hover {
        background-color: #E2E8F0 !important;
        color: #334155 !important;
        border-color: #94A3B8 !important;
    }

    /* パスワードボタン内のアイコン */
    input[type="password"] + button svg,
    button[data-testid="StyledIconButton"] svg,
    .stTextInput button svg {
        fill: #475569 !important;
        color: #475569 !important;
        stroke: #475569 !important;
    }

    input[type="password"] + button:hover svg,
    button[data-testid="StyledIconButton"]:hover svg,
    .stTextInput button:hover svg {
        fill: #334155 !important;
        color: #334155 !important;
        stroke: #334155 !important;
    }
    </style>"""
    return css
