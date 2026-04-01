"""
データビジュアライゼーションコンポーネント

Plotlyを使用した高度なチャート生成機能を提供
- レーダーチャート（Pymetrics風）
- 時系列スコア推移（Weights & Biases風）
- 候補者比較ヒートマップ（Tableau風）
- スコア比較バーチャート
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List


def create_radar_chart(evaluation: dict, title: str = "評価レーダーチャート") -> go.Figure:
    """
    6カテゴリ評価レーダーチャート（Pymetrics風）

    Args:
        evaluation: 評価データ（辞書形式）
        title: チャートタイトル

    Returns:
        Plotly Figure オブジェクト
    """
    categories = [
        "コミュニケーション",
        "ストレス耐性",
        "信頼性",
        "チームワーク",
        "信頼度",
        "職業的態度"
    ]

    # スコア抽出
    scores = []
    for key in evaluation.keys():
        if "score" in evaluation[key]:
            scores.append(evaluation[key]["score"])

    # レーダーチャートを閉じるために最初の値を末尾に追加
    scores_closed = scores + [scores[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(63, 131, 248, 0.3)',
        line=dict(color='#3F83F8', width=2),
        name='スコア'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10),
                gridcolor='#E5E7EB'
            ),
            angularaxis=dict(
                gridcolor='#E5E7EB'
            )
        ),
        showlegend=False,
        title=dict(
            text=title,
            font=dict(size=16, weight=600),
            x=0.5,
            xanchor='center'
        ),
        height=450,
        margin=dict(l=80, r=80, t=60, b=40)
    )

    return fig


def create_score_trend_chart(chunk_results: List[dict]) -> go.Figure:
    """
    チャンク別スコア推移グラフ（Weights & Biases風）

    Args:
        chunk_results: チャンク別評価結果リスト

    Returns:
        Plotly Figure オブジェクト
    """
    if not chunk_results:
        return go.Figure()

    # データ整形
    categories = [
        "コミュニケーション",
        "ストレス耐性",
        "信頼性",
        "チームワーク",
        "信頼度",
        "職業的態度"
    ]

    fig = go.Figure()

    # カテゴリ別の色マップ
    color_map = {
        "コミュニケーション": "#3B82F6",
        "ストレス耐性": "#10B981",
        "信頼性": "#F59E0B",
        "チームワーク": "#EF4444",
        "信頼度": "#8B5CF6",
        "職業的態度": "#EC4899"
    }

    # 各カテゴリの推移を折れ線グラフで表示
    for category_key, category_name in zip(chunk_results[0]['evaluation'].keys(), categories):
        scores = [chunk['evaluation'][category_key]['score'] for chunk in chunk_results]
        chunk_numbers = [i + 1 for i in range(len(chunk_results))]

        fig.add_trace(go.Scatter(
            x=chunk_numbers,
            y=scores,
            mode='lines+markers',
            name=category_name,
            line=dict(color=color_map.get(category_name, '#6B7280'), width=2),
            marker=dict(size=6)
        ))

    fig.update_layout(
        title=dict(
            text="チャンク別スコア推移",
            font=dict(size=16, weight=600),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="チャンク番号",
            gridcolor='#F1F3F5',
            tickmode='linear',
            tick0=1,
            dtick=1
        ),
        yaxis=dict(
            title="スコア",
            range=[0, 100],
            gridcolor='#F1F3F5'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        height=500,
        margin=dict(l=60, r=40, t=60, b=120),
        hovermode='x unified'
    )

    return fig


def create_comparison_heatmap(comparison_df: pd.DataFrame) -> go.Figure:
    """
    候補者比較ヒートマップ（Tableau風）

    Args:
        comparison_df: 比較データフレーム

    Returns:
        Plotly Figure オブジェクト
    """
    category_cols = [
        "コミュニケーション",
        "ストレス耐性",
        "信頼性",
        "チームワーク",
        "信頼度",
        "職業的態度"
    ]

    # カテゴリ列が存在するか確認
    available_cols = [col for col in category_cols if col in comparison_df.columns]

    if not available_cols:
        return go.Figure()

    # ファイル名をインデックスに設定
    heatmap_data = comparison_df[["ファイル名"] + available_cols].set_index("ファイル名")

    # 転置（カテゴリを行、候補者を列にする）
    heatmap_data_t = heatmap_data.T

    fig = px.imshow(
        heatmap_data_t,
        labels=dict(x="候補者", y="評価カテゴリ", color="スコア"),
        color_continuous_scale="RdYlGn",
        aspect="auto",
        text_auto=True,
        color_continuous_midpoint=50
    )

    fig.update_layout(
        title=dict(
            text="候補者評価ヒートマップ",
            font=dict(size=16, weight=600),
            x=0.5,
            xanchor='center'
        ),
        height=500,
        margin=dict(l=150, r=40, t=60, b=100)
    )

    fig.update_xaxes(tickangle=-45)

    return fig


def create_score_comparison_bar(comparison_df: pd.DataFrame) -> go.Figure:
    """
    総合スコア比較バーチャート

    Args:
        comparison_df: 比較データフレーム

    Returns:
        Plotly Figure オブジェクト
    """
    if "総合スコア" not in comparison_df.columns:
        return go.Figure()

    # リスクレベル別の色マップ
    color_map = {
        "低": "#10B981",
        "中": "#F59E0B",
        "高": "#EF4444"
    }

    # スコアでソート
    sorted_df = comparison_df.sort_values("総合スコア", ascending=False)

    fig = px.bar(
        sorted_df,
        x="ファイル名",
        y="総合スコア",
        color="リスクレベル" if "リスクレベル" in sorted_df.columns else None,
        color_discrete_map=color_map,
        title="候補者総合スコア比較",
        text="総合スコア"
    )

    fig.update_layout(
        title=dict(
            text="候補者総合スコア比較",
            font=dict(size=16, weight=600),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="候補者",
            tickangle=-45
        ),
        yaxis=dict(
            title="総合スコア",
            range=[0, 100]
        ),
        height=500,
        margin=dict(l=60, r=40, t=60, b=120)
    )

    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')

    return fig


def create_category_score_bar(evaluation: dict) -> go.Figure:
    """
    カテゴリ別スコアバーチャート（単一候補者用）

    Args:
        evaluation: 評価データ

    Returns:
        Plotly Figure オブジェクト
    """
    categories = [
        "コミュニケーション",
        "ストレス耐性",
        "信頼性",
        "チームワーク",
        "信頼度",
        "職業的態度"
    ]

    scores = [evaluation[key]["score"] for key in evaluation.keys()]

    # カテゴリ別の色
    colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]

    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=scores,
            marker=dict(
                color=colors,
                line=dict(color='#FFFFFF', width=2)
            ),
            text=scores,
            texttemplate='%{text:.0f}',
            textposition='outside'
        )
    ])

    fig.update_layout(
        title=dict(
            text="カテゴリ別評価スコア",
            font=dict(size=16, weight=600),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="評価カテゴリ",
            tickangle=-45
        ),
        yaxis=dict(
            title="スコア",
            range=[0, 110]
        ),
        height=450,
        margin=dict(l=60, r=40, t=60, b=100),
        showlegend=False
    )

    return fig
