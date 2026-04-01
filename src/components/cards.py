"""
メトリクスカード・KPIディスプレイコンポーネント

Stripe、Notion、Datadog風の洗練されたカードコンポーネントを提供
"""

from typing import Optional, Dict, List
import streamlit as st


def render_score_card_large(
    score: int,
    label: str,
    benchmark: Optional[int] = None,
    risk_level: Optional[str] = None
) -> str:
    """
    大型スコアカード（Stripe風）

    Args:
        score: メインスコア
        label: ラベル
        benchmark: 業界平均（オプション）
        risk_level: リスクレベル（低/中/高）

    Returns:
        HTMLマークアップ
    """
    # リスクレベルに応じたグラデーション
    gradient_map = {
        "低": "linear-gradient(135deg, #10B981 0%, #059669 100%)",
        "中": "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
        "高": "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)",
        None: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    }

    gradient = gradient_map.get(risk_level, gradient_map[None])

    # 業界平均比較
    delta_html = ""
    if benchmark:
        delta = score - benchmark
        delta_color = "#FFFFFF" if delta >= 0 else "#FEE2E2"
        delta_icon = "▲" if delta >= 0 else "▼"
        delta_html = f'''
        <div style="
            margin-top: 12px;
            font-size: 0.875rem;
            color: {delta_color};
            opacity: 0.9;
        ">
            {delta_icon} 業界平均比 {delta:+d}点
        </div>
        '''

    html = f"""
    <div style="
        background: {gradient};
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        color: white;
        transition: transform 0.2s;
    ">
        <div style="font-size: 0.875rem; opacity: 0.9; font-weight: 500;">
            {label}
        </div>
        <div style="
            font-size: 3.5rem;
            font-weight: 700;
            margin: 12px 0;
            letter-spacing: -0.02em;
        ">
            {score}
        </div>
        {delta_html}
    </div>
    """
    return html


def render_metric_card_small(
    value: float,
    label: str,
    icon: Optional[str] = None,
    delta: Optional[float] = None,
    format_str: str = "{:.1f}"
) -> str:
    """
    小型メトリクスカード（Notion風）

    Args:
        value: 値
        label: ラベル
        icon: アイコン（絵文字）
        delta: 変化量
        format_str: フォーマット文字列

    Returns:
        HTMLマークアップ
    """
    icon_html = f'<span style="font-size: 1.5rem; margin-right: 8px;">{icon}</span>' if icon else ""

    delta_html = ""
    if delta is not None:
        delta_color = "#10B981" if delta >= 0 else "#EF4444"
        delta_icon = "↑" if delta >= 0 else "↓"
        delta_html = f'''
        <span style="color: {delta_color}; font-size: 0.875rem; margin-left: 8px;">
            {delta_icon} {abs(delta):.1f}
        </span>
        '''

    formatted_value = format_str.format(value)

    html = f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: box-shadow 0.2s;
    ">
        <div style="
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        ">
            {icon_html}
            <span style="
                font-size: 0.875rem;
                color: #6B7280;
                font-weight: 500;
            ">{label}</span>
        </div>
        <div style="
            font-size: 2rem;
            font-weight: 700;
            color: #1F2937;
        ">
            {formatted_value}{delta_html}
        </div>
    </div>
    """
    return html


def render_risk_banner(
    risk_level: str,
    risk_flags: List[str],
    overall_score: int
) -> str:
    """
    リスク評価バナー（Datadog風）

    Args:
        risk_level: リスクレベル（低/中/高）
        risk_flags: リスクフラグリスト
        overall_score: 総合スコア

    Returns:
        HTMLマークアップ
    """
    # リスクレベル別の設定
    risk_config = {
        "低": {
            "background": "#D1FAE5",
            "border": "#10B981",
            "text": "#065F46",
            "icon": "✓",
            "message": "リスクは低いと評価されました"
        },
        "中": {
            "background": "#FEF3C7",
            "border": "#F59E0B",
            "text": "#92400E",
            "icon": "⚠",
            "message": "中程度のリスクが検出されました"
        },
        "高": {
            "background": "#FEE2E2",
            "border": "#EF4444",
            "text": "#991B1B",
            "icon": "✕",
            "message": "高リスクが検出されました"
        }
    }

    config = risk_config.get(risk_level, risk_config["中"])

    # リスクフラグのHTML
    flags_html = ""
    if risk_flags:
        flags_items = "".join([f"<li>{flag}</li>" for flag in risk_flags])
        flags_html = f"""
        <div style="margin-top: 12px;">
            <strong>検出されたリスク:</strong>
            <ul style="margin: 8px 0 0 20px; padding: 0;">
                {flags_items}
            </ul>
        </div>
        """

    html = f"""
    <div style="
        background: {config['background']};
        border-left: 4px solid {config['border']};
        border-radius: 8px;
        padding: 16px 20px;
        margin: 16px 0;
        color: {config['text']};
    ">
        <div style="
            display: flex;
            align-items: center;
            font-weight: 600;
            font-size: 1rem;
        ">
            <span style="font-size: 1.5rem; margin-right: 12px;">{config['icon']}</span>
            <span>リスクレベル: {risk_level}</span>
            <span style="margin-left: auto; font-size: 1.25rem;">{overall_score}点</span>
        </div>
        <div style="margin-top: 8px; font-size: 0.875rem;">
            {config['message']}
        </div>
        {flags_html}
    </div>
    """
    return html


def render_metric_grid(metrics: Dict[str, float], columns: int = 3) -> str:
    """
    メトリクスグリッド（Linear風）

    Args:
        metrics: メトリクス辞書（ラベル: 値）
        columns: カラム数

    Returns:
        HTMLマークアップ
    """
    items_html = ""
    for label, value in metrics.items():
        items_html += f"""
        <div style="
            background: #F9FAFB;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        ">
            <div style="
                font-size: 1.75rem;
                font-weight: 700;
                color: #1F2937;
                margin-bottom: 4px;
            ">{value}</div>
            <div style="
                font-size: 0.75rem;
                color: #6B7280;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            ">{label}</div>
        </div>
        """

    html = f"""
    <div style="
        display: grid;
        grid-template-columns: repeat({columns}, 1fr);
        gap: 16px;
        margin: 20px 0;
    ">
        {items_html}
    </div>
    """
    return html


def render_category_score_card(
    category_name: str,
    score: int,
    confidence: float,
    reason: str
) -> str:
    """
    カテゴリ別スコアカード

    Args:
        category_name: カテゴリ名
        score: スコア
        confidence: 信頼度
        reason: 理由

    Returns:
        HTMLマークアップ
    """
    # スコアに応じた色
    if score >= 70:
        score_color = "#10B981"
    elif score >= 40:
        score_color = "#F59E0B"
    else:
        score_color = "#EF4444"

    html = f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px;
        margin: 12px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        ">
            <h3 style="
                margin: 0;
                font-size: 1.125rem;
                color: #1F2937;
                font-weight: 600;
            ">{category_name}</h3>
            <div style="
                font-size: 2rem;
                font-weight: 700;
                color: {score_color};
            ">{score}</div>
        </div>
        <div style="
            font-size: 0.875rem;
            color: #6B7280;
            margin-bottom: 8px;
        ">
            信頼度: {confidence:.1%}
        </div>
        <div style="
            font-size: 0.875rem;
            color: #374151;
            line-height: 1.6;
            padding: 12px;
            background: #F9FAFB;
            border-radius: 6px;
        ">
            {reason}
        </div>
    </div>
    """
    return html
