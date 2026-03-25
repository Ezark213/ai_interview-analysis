"""HTMLレポート生成モジュール

解析結果JSONからスタンドアロンHTMLレポートを生成する。
外部依存なし（Jinja2不使用）。CSS/SVG埋め込みで単一HTMLファイルとして共有可能。
"""
import math
from datetime import datetime


def _score_color(score: int) -> str:
    """スコアに応じた色を返す"""
    if score >= 85:
        return "#22C55E"  # 緑
    elif score >= 70:
        return "#3B82F6"  # 青
    elif score >= 55:
        return "#EAB308"  # 黄
    elif score >= 40:
        return "#F97316"  # 橙
    else:
        return "#EF4444"  # 赤


def _score_bg_color(score: int) -> str:
    """スコアに応じた薄い背景色を返す"""
    if score >= 85:
        return "#F0FDF4"
    elif score >= 70:
        return "#EFF6FF"
    elif score >= 55:
        return "#FEFCE8"
    elif score >= 40:
        return "#FFF7ED"
    else:
        return "#FEF2F2"


def _risk_badge(risk_level: str) -> str:
    """リスクレベルに応じたバッジHTMLを返す"""
    colors = {
        "低": ("#22C55E", "#F0FDF4"),
        "中": ("#EAB308", "#FEFCE8"),
        "高": ("#EF4444", "#FEF2F2"),
    }
    fg, bg = colors.get(risk_level, ("#6B7280", "#F3F4F6"))
    return f'<span style="display:inline-block;padding:4px 16px;border-radius:20px;font-size:1rem;font-weight:700;color:{fg};background:{bg};border:2px solid {fg};">リスク: {risk_level}</span>'


def _escape(text: str) -> str:
    """HTML特殊文字のエスケープ"""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# --- SVGチャート生成 ---

def _build_radar_svg(evaluation: dict) -> str:
    """6カテゴリのスコアをSVGレーダーチャートで描画"""
    category_labels = {
        "communication": "コミュニケーション",
        "stress_tolerance": "ストレス耐性",
        "reliability": "信頼性",
        "teamwork": "チームワーク",
        "credibility": "信頼度",
        "professional_demeanor": "職業的態度",
    }

    categories = list(category_labels.keys())
    labels = list(category_labels.values())
    n = len(categories)

    # スコア取得（0-100）
    scores = []
    for cat in categories:
        cat_data = evaluation.get(cat, {})
        scores.append(cat_data.get("score", 0) if isinstance(cat_data, dict) else 0)

    cx, cy = 200, 200
    max_r = 150
    angle_offset = -math.pi / 2  # 上から開始

    def polar(i, r):
        angle = angle_offset + (2 * math.pi * i / n)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        return x, y

    # グリッド線（20, 40, 60, 80, 100）
    grid_lines = []
    for level in [20, 40, 60, 80, 100]:
        r = max_r * level / 100
        points = " ".join(f"{polar(i, r)[0]:.1f},{polar(i, r)[1]:.1f}" for i in range(n))
        grid_lines.append(f'<polygon points="{points}" fill="none" stroke="#E2E8F0" stroke-width="1"/>')

    # 軸線
    axis_lines = []
    for i in range(n):
        x, y = polar(i, max_r)
        axis_lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#E2E8F0" stroke-width="1"/>')

    # データポリゴン
    data_points = []
    for i, score in enumerate(scores):
        r = max_r * score / 100
        x, y = polar(i, r)
        data_points.append(f"{x:.1f},{y:.1f}")
    data_polygon = f'<polygon points="{" ".join(data_points)}" fill="rgba(59,130,246,0.2)" stroke="#3B82F6" stroke-width="2.5"/>'

    # データポイントのドット
    dots = []
    for i, score in enumerate(scores):
        r = max_r * score / 100
        x, y = polar(i, r)
        color = _score_color(score)
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="white" stroke-width="2"/>')

    # ラベル
    label_elements = []
    for i, label in enumerate(labels):
        r_label = max_r + 30
        x, y = polar(i, r_label)
        anchor = "middle"
        if x < cx - 10:
            anchor = "end"
        elif x > cx + 10:
            anchor = "start"
        score_val = scores[i]
        color = _score_color(score_val)
        label_elements.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="central" font-size="13" font-weight="600" fill="#334155">'
            f'{_escape(label)}</text>'
        )
        label_elements.append(
            f'<text x="{x:.1f}" y="{y + 18:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="central" font-size="14" font-weight="700" fill="{color}">'
            f'{score_val}</text>'
        )

    svg = f'''<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="max-width:420px;margin:0 auto;display:block;">
    {"".join(grid_lines)}
    {"".join(axis_lines)}
    {data_polygon}
    {"".join(dots)}
    {"".join(label_elements)}
</svg>'''
    return svg


def _build_bar_svg(evaluation: dict) -> str:
    """各カテゴリスコアの横棒グラフをSVGで描画"""
    category_labels = {
        "communication": "コミュニケーション",
        "stress_tolerance": "ストレス耐性",
        "reliability": "信頼性",
        "teamwork": "チームワーク",
        "credibility": "信頼度",
        "professional_demeanor": "職業的態度",
    }

    categories = list(category_labels.keys())
    labels = list(category_labels.values())

    bar_height = 32
    gap = 14
    label_width = 150
    bar_max_width = 300
    padding_top = 10
    total_height = padding_top + len(categories) * (bar_height + gap) + 10

    bars = []
    for i, cat in enumerate(categories):
        cat_data = evaluation.get(cat, {})
        score = cat_data.get("score", 0) if isinstance(cat_data, dict) else 0
        color = _score_color(score)
        y = padding_top + i * (bar_height + gap)
        bar_width = bar_max_width * score / 100

        # ラベル
        bars.append(
            f'<text x="{label_width - 8}" y="{y + bar_height / 2 + 1}" '
            f'text-anchor="end" dominant-baseline="central" '
            f'font-size="13" font-weight="600" fill="#334155">{_escape(labels[i])}</text>'
        )
        # 背景バー
        bars.append(
            f'<rect x="{label_width}" y="{y}" width="{bar_max_width}" height="{bar_height}" '
            f'rx="4" fill="#F1F5F9"/>'
        )
        # スコアバー
        if bar_width > 0:
            bars.append(
                f'<rect x="{label_width}" y="{y}" width="{bar_width:.1f}" height="{bar_height}" '
                f'rx="4" fill="{color}"/>'
            )
        # スコア数値
        text_x = label_width + bar_width + 8 if bar_width < bar_max_width - 40 else label_width + bar_width - 8
        text_anchor = "start" if bar_width < bar_max_width - 40 else "end"
        text_fill = "#334155" if bar_width < bar_max_width - 40 else "white"
        bars.append(
            f'<text x="{text_x:.1f}" y="{y + bar_height / 2 + 1}" '
            f'text-anchor="{text_anchor}" dominant-baseline="central" '
            f'font-size="13" font-weight="700" fill="{text_fill}">{score}</text>'
        )

    svg = f'''<svg viewBox="0 0 500 {total_height}" xmlns="http://www.w3.org/2000/svg" style="max-width:520px;width:100%;">
    {"".join(bars)}
</svg>'''
    return svg


# --- メインHTML生成 ---

def generate_html_report(result: dict, filename: str = "", analysis_date: str = "") -> str:
    """結果JSONからスタンドアロンHTMLレポートを生成

    Args:
        result: 解析結果の辞書
        filename: 解析対象のファイル名
        analysis_date: 解析日時の文字列（未指定時は現在日時）

    Returns:
        str: スタンドアロンHTML文字列
    """
    if not analysis_date:
        analysis_date = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    score = result.get("overall_risk_score", 0)
    risk_level = result.get("risk_level", "不明")
    evaluation = result.get("evaluation", {})
    red_flags = result.get("red_flags", [])
    positive_signals = result.get("positive_signals", [])
    recommendation = result.get("recommendation", "")
    disclaimer = result.get("disclaimer", "")
    metrics = result.get("behavioral_metrics", {})

    category_labels = {
        "communication": "コミュニケーション",
        "stress_tolerance": "ストレス耐性",
        "reliability": "信頼性",
        "teamwork": "チームワーク",
        "credibility": "信頼度",
        "professional_demeanor": "職業的態度",
    }

    # --- チャートSVG ---
    radar_svg = _build_radar_svg(evaluation) if evaluation else ""
    bar_svg = _build_bar_svg(evaluation) if evaluation else ""

    # --- 詳細評価セクション ---
    detail_sections = []
    for cat_key, cat_label in category_labels.items():
        cat_data = evaluation.get(cat_key, {})
        if not isinstance(cat_data, dict):
            continue
        cat_score = cat_data.get("score", 0)
        cat_color = _score_color(cat_score)
        observations = cat_data.get("observations", [])
        confidence = cat_data.get("confidence", "不明")

        obs_html = ""
        for obs in observations:
            obs_html += f"<li>{_escape(obs)}</li>"
        if not obs_html:
            obs_html = "<li>観察事項なし</li>"

        detail_sections.append(f'''
        <div class="detail-card">
            <div class="detail-header">
                <span class="detail-label">{_escape(cat_label)}</span>
                <span class="detail-score" style="color:{cat_color};">{cat_score}<span class="detail-max">/100</span></span>
            </div>
            <div class="score-bar-container">
                <div class="score-bar" style="width:{cat_score}%;background:{cat_color};"></div>
            </div>
            <div class="detail-body">
                <p class="detail-sub">観察事項</p>
                <ul>{obs_html}</ul>
                <p class="confidence">確信度: <strong>{_escape(confidence)}</strong></p>
            </div>
        </div>''')

    details_html = "\n".join(detail_sections)

    # --- 行動メトリクステーブル ---
    metrics_html = ""
    if metrics and isinstance(metrics, dict):
        metrics_labels = {
            "eye_contact_quality": "アイコンタクトの質",
            "gesture_naturalness": "ジェスチャーの自然さ",
            "posture_stability": "姿勢の安定性",
            "speech_fluency": "発話の流暢さ",
            "filler_frequency": "フィラーの頻度",
            "response_speed": "応答速度",
            "verbal_nonverbal_consistency": "言語-非言語の一致度",
        }
        rows = ""
        for key, label in metrics_labels.items():
            val = metrics.get(key, "-")
            rows += f"<tr><td>{_escape(label)}</td><td>{_escape(str(val))}</td></tr>"

        metrics_html = f'''
        <section class="section">
            <h2>行動メトリクス</h2>
            <table class="metrics-table">
                <thead><tr><th>指標</th><th>評価</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </section>'''

    # --- リスクシグナル ---
    red_flags_html = ""
    if red_flags:
        items = "".join(f'<li class="signal-red">{_escape(f)}</li>' for f in red_flags)
        red_flags_html = f'''
        <section class="section">
            <h2>リスクシグナル</h2>
            <ul class="signal-list">{items}</ul>
        </section>'''
    else:
        red_flags_html = '''
        <section class="section">
            <h2>リスクシグナル</h2>
            <p class="no-signal good">重大なリスクシグナルは検出されませんでした</p>
        </section>'''

    # --- ポジティブシグナル ---
    positive_html = ""
    if positive_signals:
        items = "".join(f'<li class="signal-green">{_escape(s)}</li>' for s in positive_signals)
        positive_html = f'''
        <section class="section">
            <h2>ポジティブシグナル</h2>
            <ul class="signal-list">{items}</ul>
        </section>'''
    else:
        positive_html = '''
        <section class="section">
            <h2>ポジティブシグナル</h2>
            <p class="no-signal neutral">特筆すべきポジティブシグナルはありませんでした</p>
        </section>'''

    # --- 推奨事項 ---
    rec_html = ""
    if recommendation:
        rec_html = f'''
        <section class="section">
            <h2>推奨事項</h2>
            <div class="recommendation">{_escape(recommendation)}</div>
        </section>'''

    # --- 免責事項 ---
    disclaimer_html = ""
    if disclaimer:
        disclaimer_html = f'<div class="disclaimer-body">{_escape(disclaimer)}</div>'

    # --- HTML組み立て ---
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>面談解析レポート - {_escape(filename)}</title>
<style>
/* === ベーススタイル === */
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic", "Meiryo", sans-serif;
    color: #1E293B;
    background: #F8FAFC;
    line-height: 1.6;
}}
.container {{
    max-width: 900px;
    margin: 0 auto;
    padding: 24px;
}}

/* === ヘッダー === */
.report-header {{
    background: linear-gradient(135deg, #1B3A5C 0%, #264D73 100%);
    color: white;
    padding: 32px;
    border-radius: 12px;
    margin-bottom: 24px;
}}
.report-header h1 {{
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 8px;
}}
.report-meta {{
    display: flex;
    gap: 24px;
    font-size: 0.9rem;
    opacity: 0.85;
    flex-wrap: wrap;
}}
.report-meta span {{ white-space: nowrap; }}

/* === 総合スコアカード === */
.score-card {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 32px;
    padding: 32px;
    background: white;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    margin-bottom: 24px;
    flex-wrap: wrap;
}}
.score-big {{
    font-size: 4.5rem;
    font-weight: 800;
    line-height: 1;
}}
.score-big .max {{ font-size: 1.5rem; font-weight: 400; color: #94A3B8; }}

/* === チャートエリア === */
.charts {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 24px;
}}
.chart-box {{
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 24px;
}}
.chart-box h2 {{
    font-size: 1.1rem;
    color: #1B3A5C;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid #E2E8F0;
}}

/* === セクション === */
.section {{
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
}}
.section h2 {{
    font-size: 1.1rem;
    color: #1B3A5C;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid #E2E8F0;
}}

/* === 詳細評価カード === */
.details-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
}}
.detail-card {{
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 20px;
    transition: box-shadow 0.2s;
}}
.detail-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}}
.detail-label {{ font-weight: 700; font-size: 1rem; color: #1B3A5C; }}
.detail-score {{ font-size: 1.8rem; font-weight: 800; }}
.detail-max {{ font-size: 0.85rem; font-weight: 400; color: #94A3B8; }}
.score-bar-container {{
    height: 6px;
    background: #F1F5F9;
    border-radius: 3px;
    margin-bottom: 12px;
}}
.score-bar {{
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s;
}}
.detail-body {{ font-size: 0.9rem; }}
.detail-body ul {{ padding-left: 1.2em; margin: 4px 0 8px; }}
.detail-body li {{ margin-bottom: 4px; }}
.detail-sub {{ font-weight: 600; color: #475569; margin-bottom: 2px; }}
.confidence {{ color: #64748B; font-size: 0.85rem; margin-top: 4px; }}

/* === メトリクステーブル === */
.metrics-table {{
    width: 100%;
    border-collapse: collapse;
}}
.metrics-table th, .metrics-table td {{
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid #E2E8F0;
    font-size: 0.9rem;
}}
.metrics-table th {{
    background: #F8FAFC;
    font-weight: 700;
    color: #475569;
}}
.metrics-table tr:last-child td {{ border-bottom: none; }}

/* === シグナルリスト === */
.signal-list {{ list-style: none; padding: 0; }}
.signal-list li {{
    padding: 10px 14px;
    border-radius: 6px;
    margin-bottom: 6px;
    font-size: 0.9rem;
}}
.signal-red {{ background: #FEF2F2; color: #991B1B; border-left: 4px solid #EF4444; }}
.signal-green {{ background: #F0FDF4; color: #166534; border-left: 4px solid #22C55E; }}
.no-signal {{ padding: 12px 16px; border-radius: 6px; font-size: 0.9rem; }}
.no-signal.good {{ background: #F0FDF4; color: #166534; }}
.no-signal.neutral {{ background: #F8FAFC; color: #64748B; }}

/* === 推奨事項 === */
.recommendation {{
    background: #EFF6FF;
    border-left: 4px solid #3B82F6;
    padding: 14px 18px;
    border-radius: 0 6px 6px 0;
    font-size: 0.9rem;
    color: #1E40AF;
}}

/* === フッター === */
.report-footer {{
    text-align: center;
    padding: 24px 0;
    color: #94A3B8;
    font-size: 0.8rem;
    border-top: 1px solid #E2E8F0;
    margin-top: 8px;
}}
.disclaimer-body {{
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 0.85rem;
    color: #92400E;
    margin-bottom: 16px;
}}

/* === 印刷対応 === */
@media print {{
    body {{ background: white; font-size: 10pt; }}
    .container {{ max-width: 100%; padding: 0; }}
    .report-header {{
        background: #1B3A5C !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        break-after: avoid;
    }}
    .score-card {{ break-after: avoid; }}
    .charts {{
        grid-template-columns: 1fr 1fr;
        break-inside: avoid;
    }}
    .chart-box {{ break-inside: avoid; }}
    .details-grid {{ grid-template-columns: 1fr 1fr; }}
    .detail-card {{ break-inside: avoid; }}
    .section {{ break-inside: avoid; }}
    .score-bar, .signal-red, .signal-green, .no-signal,
    .recommendation, .disclaimer-body {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}
    @page {{
        size: A4;
        margin: 15mm;
    }}
}}

/* === レスポンシブ === */
@media (max-width: 700px) {{
    .charts {{ grid-template-columns: 1fr; }}
    .details-grid {{ grid-template-columns: 1fr; }}
    .score-card {{ flex-direction: column; gap: 16px; }}
}}
</style>
</head>
<body>
<div class="container">

    <!-- ヘッダー -->
    <div class="report-header">
        <h1>AI面談動画解析レポート</h1>
        <div class="report-meta">
            <span>解析日時: {_escape(analysis_date)}</span>
            {f'<span>ファイル: {_escape(filename)}</span>' if filename else ''}
        </div>
    </div>

    <!-- 総合スコア -->
    <div class="score-card" style="background:{_score_bg_color(score)};">
        <div>
            <div class="score-big" style="color:{_score_color(score)};">{score}<span class="max">/100</span></div>
            <div style="text-align:center;margin-top:4px;color:#475569;font-weight:600;">総合スコア</div>
        </div>
        <div>{_risk_badge(risk_level)}</div>
    </div>

    <!-- チャート -->
    <div class="charts">
        <div class="chart-box">
            <h2>レーダーチャート</h2>
            {radar_svg}
        </div>
        <div class="chart-box">
            <h2>カテゴリ別スコア</h2>
            {bar_svg}
        </div>
    </div>

    <!-- 詳細評価 -->
    <div class="section">
        <h2>詳細評価</h2>
        <div class="details-grid">
            {details_html}
        </div>
    </div>

    <!-- 行動メトリクス -->
    {metrics_html}

    <!-- リスクシグナル -->
    {red_flags_html}

    <!-- ポジティブシグナル -->
    {positive_html}

    <!-- 推奨事項 -->
    {rec_html}

    <!-- フッター -->
    {disclaimer_html}
    <div class="report-footer">
        AI面談動画解析システム v1.1<br>
        本レポートの評価結果は参考情報です。最終的な判断は必ず人間が行ってください。<br>
        Powered by Google Gemini API
    </div>

</div>
</body>
</html>'''

    return html
