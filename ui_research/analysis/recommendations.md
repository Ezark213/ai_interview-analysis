# AI面談動画解析システム - UI/UX改善推奨事項

**作成日**: 2026-03-30
**ベースライン**: 現行バージョン（Streamlit標準デザイン）
**目標**: エンタープライズグレードHR Techツール

---

## エグゼクティブサマリー

### 現状の課題
1. **デザイン品質**: 基本的なStreamlit標準デザインにとどまる
2. **データ可視化**: テーブルとメトリクスのみ、視覚的比較機能が不十分
3. **ユーザー体験**: 静的表示が中心、インタラクティブ性に欠ける
4. **競合優位性**: HireVue、Pymetrics等の競合と比較してUI品質が劣る

### 改善の方向性
- **ベンチマーク対象**: Linear、Stripe、Notion（モダンSaaS）+ Pymetrics、HireVue（HR Tech）
- **重点領域**: カラーパレット、データビジュアライゼーション、メトリクスカード
- **実装方針**: 4フェーズで段階的改善（48時間/6営業日）

### 期待される成果
- ユーザー満足度向上（第一印象改善）
- 意思決定支援強化（視覚的比較による効率化）
- 競合優位性確立（同等以上のUI品質）

---

## フェーズ別推奨事項

### フェーズ2: 基礎UI改善（18時間）

#### 2.1 カラーパレット刷新
**現状**:
- Primary: `#1B2559`（濃紺）
- Secondary: `#4F6AF0`（ブルー）
- 2色のみの限定的パレット

**推奨**:
```css
:root {
    /* 既存維持 */
    --primary-dark-navy: #1B2559;
    --primary-blue: #4F6AF0;

    /* 新規追加（Notion/Linear風） */
    --surface-primary: #FFFFFF;
    --surface-secondary: #F8F9FA;
    --surface-tertiary: #F1F3F5;
    --text-heading: #1F2937;
    --text-body: #6B7280;
    --text-muted: #9CA3AF;

    /* データビジュアライゼーション用（Tableau風） */
    --chart-color-1: #3B82F6;  /* ブルー */
    --chart-color-2: #10B981;  /* グリーン */
    --chart-color-3: #F59E0B;  /* オレンジ */
    --chart-color-4: #EF4444;  /* レッド */
    --chart-color-5: #8B5CF6;  /* パープル */
    --chart-color-6: #EC4899;  /* ピンク */

    /* ステータスカラー（Datadog風） */
    --status-success: #10B981;
    --status-warning: #F59E0B;
    --status-error: #EF4444;
    --status-info: #3B82F6;
}
```

**根拠**:
- [スクリーンショット分析後に詳細化]
- 20サイト中XX%がニュートラルグレー系背景を採用
- データビズ用6色パレットは業界標準

**実装優先度**: 高（他の改善の基盤）

---

#### 2.2 タイポグラフィ階層強化
**現状**:
- Noto Sans JP + Inter
- サイズ階層が不明確

**推奨**:
```css
/* フォントサイズ階層（Linear風） */
--font-size-h1: 2.5rem;   /* 40px */
--font-size-h2: 2rem;     /* 32px */
--font-size-h3: 1.5rem;   /* 24px */
--font-size-body: 1rem;   /* 16px */
--font-size-small: 0.875rem; /* 14px */
--font-size-caption: 0.75rem; /* 12px */

/* フォントウェイト */
--font-weight-bold: 700;
--font-weight-semibold: 600;
--font-weight-medium: 500;
--font-weight-normal: 400;

/* 行間 */
--line-height-tight: 1.25;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
```

**実装優先度**: 高

---

#### 2.3 メトリクスカード刷新
**現状**:
- `st.metric()` の標準デザイン
- 2カラムレイアウト

**推奨パターンA（Stripe風 - ヒーローメトリクス用）**:
```python
def render_score_card_large(score: int, label: str, benchmark: int = None) -> str:
    """大型スコアカード（総合スコア用）"""
    delta_html = ""
    if benchmark:
        delta = score - benchmark
        delta_color = "#10B981" if delta >= 0 else "#EF4444"
        delta_html = f'<div style="color: {delta_color};">業界平均比 {delta:+d}点</div>'

    html = f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 32px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        color: white;
    ">
        <div style="font-size: 0.875rem; opacity: 0.9;">{label}</div>
        <div style="font-size: 3rem; font-weight: 700; margin: 8px 0;">{score}</div>
        {delta_html}
    </div>
    """
    return html
```

**推奨パターンB（Notion風 - カテゴリスコア用）**:
```python
def render_metric_grid(metrics: dict) -> str:
    """メトリクスグリッド（6カテゴリ用）"""
    # 実装詳細はスクリーンショット分析後に追加
    pass
```

**実装優先度**: 高

---

#### 2.4 レーダーチャート実装
**現状**:
- カテゴリ評価はタブ表示のみ

**推奨**:
- Plotlyによるレーダーチャート（Pymetrics風）
- 6カテゴリを一目で比較可能

**実装コード**:
```python
import plotly.graph_objects as go

def create_radar_chart(evaluation: dict) -> go.Figure:
    """6カテゴリレーダーチャート"""
    categories = ["コミュニケーション", "ストレス耐性", "信頼性",
                  "チームワーク", "信頼度", "職業的態度"]
    scores = [evaluation[k]["score"] for k in evaluation.keys()]

    fig = go.Figure(data=go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        fillcolor='rgba(63, 131, 248, 0.3)',
        line=dict(color='#3F83F8', width=2)
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10)
            )
        ),
        showlegend=False,
        height=400
    )

    return fig
```

**適用箇所**: `src/app.py` 行526-544付近

**実装優先度**: 高

---

### フェーズ3: 高度なビジュアライゼーション（14時間）

#### 3.1 バッチ処理比較ヒートマップ
**現状**:
- 比較表のみ（テーブル表示）

**推奨**:
- Plotly heatmap（Amplitude/Tableau風）
- 候補者（行） × 評価カテゴリ（列）
- 色グラデーション（赤-黄-緑）

**実装コード**:
```python
import plotly.express as px

def create_comparison_heatmap(comparison_df: pd.DataFrame) -> go.Figure:
    """候補者比較ヒートマップ"""
    category_cols = ["コミュニケーション", "ストレス耐性", "信頼性",
                     "チームワーク", "信頼度", "職業的態度"]
    heatmap_data = comparison_df[["ファイル名"] + category_cols].set_index("ファイル名")

    fig = px.imshow(
        heatmap_data.T,
        labels=dict(x="候補者", y="評価カテゴリ", color="スコア"),
        color_continuous_scale="RdYlGn",
        aspect="auto",
        text_auto=True
    )

    fig.update_layout(
        title="候補者評価ヒートマップ",
        height=500
    )

    return fig
```

**適用箇所**: `src/app.py` 行817-836付近

**実装優先度**: 高

---

#### 3.2 スコア比較バーチャート
**現状**:
- テーブルのみ

**推奨**:
- Plotly bar chart
- リスクレベル別色分け
- ソート機能

**実装コード**:
```python
def create_score_comparison_bar(comparison_df: pd.DataFrame) -> go.Figure:
    """総合スコア比較バーチャート"""
    color_map = {
        "低": "#10B981",
        "中": "#F59E0B",
        "高": "#EF4444"
    }

    fig = px.bar(
        comparison_df.sort_values("総合スコア", ascending=False),
        x="ファイル名",
        y="総合スコア",
        color="リスクレベル",
        color_discrete_map=color_map,
        title="候補者総合スコア比較"
    )

    fig.update_layout(
        xaxis_title="候補者",
        yaxis_title="総合スコア",
        height=400
    )

    return fig
```

**実装優先度**: 高

---

#### 3.3 時系列スコア推移グラフ
**現状**:
- チャンク別表示のみ

**推奨**:
- Plotly line chart（Weights & Biases風）
- 6カテゴリの時系列推移
- ズーム/パン機能

**実装コード**:
```python
def create_score_trend_chart(chunk_results: list) -> go.Figure:
    """チャンク別スコア推移"""
    # 実装詳細はフェーズ3で追加
    pass
```

**実装優先度**: 中

---

### フェーズ4: 仕上げ・最適化（4時間）

#### 4.1 レスポンシブ対応
**推奨ブレークポイント**:
```css
/* タブレット */
@media (max-width: 768px) {
    .metric-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* モバイル */
@media (max-width: 480px) {
    .metric-grid {
        grid-template-columns: 1fr;
    }
}
```

**実装優先度**: 中

---

#### 4.2 パフォーマンス最適化
**推奨施策**:
1. Plotlyチャートに `@st.cache_data` 適用
2. `use_container_width=True` 設定
3. 大量データ（100件以上）のページネーション

**実装例**:
```python
@st.cache_data
def create_radar_chart(evaluation: dict) -> go.Figure:
    # チャート生成ロジック
    pass

st.plotly_chart(fig, use_container_width=True)
```

**実装優先度**: 中

---

## 実装優先順位マトリクス

| 推奨事項 | 優先度 | 工数 | インパクト | フェーズ |
|----------|--------|------|-----------|---------|
| カラーパレット刷新 | 高 | 4h | 高 | 2 |
| メトリクスカード（Stripe風） | 高 | 3h | 高 | 2 |
| レーダーチャート | 高 | 2h | 高 | 2 |
| ヒートマップ | 高 | 3h | 高 | 3 |
| バーチャート | 高 | 2h | 中 | 3 |
| 時系列グラフ | 中 | 4h | 中 | 3 |
| タイポグラフィ | 高 | 2h | 中 | 2 |
| レスポンシブ対応 | 中 | 2h | 低 | 4 |
| パフォーマンス最適化 | 中 | 1h | 中 | 4 |

---

## 依存関係とリスク

### 依存ライブラリ
```
plotly>=5.18.0
kaleido>=0.2.1
streamlit-plotly-events>=0.0.6
```

### 技術リスク
1. **Plotlyとの互換性**: Streamlit 1.30以上推奨
2. **大量データ処理**: 100件以上の候補者でパフォーマンス低下の可能性
3. **レスポンシブ**: Streamlitの制約により完全対応は困難

### 軽減策
1. バージョン固定（requirements.txt）
2. ページネーション実装
3. 主要ブレークポイントのみ対応

---

## 検証方法

### フェーズ2検証
- [ ] `streamlit run src/app.py` でエラーなく起動
- [ ] メトリクスカードが新デザインで表示
- [ ] レーダーチャートが動作
- [ ] カラーパレットが統一

### フェーズ3検証
- [ ] ヒートマップが表示される
- [ ] バーチャートが動作する
- [ ] インタラクティブ操作（ズーム、ホバー）が機能

### フェーズ4検証
- [ ] タブレット/モバイルで表示が崩れない
- [ ] チャート生成が高速（キャッシュ確認）

---

## 参考資料

### ベンチマークサイト
- **AI/ML**: Hugging Face, Weights & Biases, Comet ML, Neptune.ai, Datadog
- **Data Viz**: Tableau, Looker, Metabase, Amplitude, Mixpanel
- **HR Tech**: Lever, Greenhouse, HireVue, Pymetrics, Workable
- **Modern SaaS**: Linear, Notion, Airtable
- **Enterprise**: Stripe, MongoDB Atlas

### スクリーンショット
- 格納場所: `ui_research/screenshots/`
- 詳細分析: `design_patterns.md`

---

## 次のステップ

### 即座に実行可能
1. [ ] 依存ライブラリインストール
   ```bash
   pip install plotly kaleido streamlit-plotly-events
   ```

2. [ ] `src/components/styles.py` 改修開始
   - CSS変数追加

3. [ ] `src/components/charts.py` 作成
   - レーダーチャート実装

### スクリーンショット分析後
1. [ ] `design_patterns.md` 完成
2. [ ] `color_schemes.json` 完成
3. [ ] 本ドキュメントの詳細化（具体的なカラー値、実装例）
