# 解析設計：精度を重視したアプローチ

## 設計における重要な課題

### 1. 精度の担保
**課題**: AIに動画を丸投げしても、重要な非言語シグナルを見落とす可能性が高い

### 2. 何をドキュメント化するか
- **オプションA**: 動画の不自然な点をドキュメント化
- **オプションB**: 非言語データ（視線、姿勢、声）をドキュメント化
- **オプションC**: その他のアプローチ

### 3. 長い動画（30分以上）の処理
- チャンク化の必要性
- 重要シーンの抽出方法
- 処理コストとのバランス

---

## 提案：段階的解析アプローチ（Multi-Stage Analysis）

精度を最大化するために、**動画を構造化データに変換してから解析**する方式を提案します。

---

## 設計パターンの比較

### パターンA: 動画直接投入（シンプル・低精度）

```
[動画] → [AI（Gemini/GPT-4o）] → [評価レポート]
```

#### メリット
- 実装が簡単
- 開発コストが低い

#### デメリット
- **精度が低い**: AIが重要なシグナルを見落とす
- **再現性がない**: 同じ動画でも結果がブレる
- **根拠が不明確**: なぜそう判断したのか分からない
- **長い動画に対応できない**: 30分以上は処理が不安定

#### 精度スコア: ⭐⭐☆☆☆（2/5）

---

### パターンB: 構造化データ変換方式（精度重視・推奨）

```
[動画]
  ↓
[前処理レイヤー]
  ├─ 音声抽出 → 文字起こし（Whisper API等）
  ├─ フレーム抽出 → 表情・姿勢解析（Computer Vision）
  └─ メタデータ抽出（話速、間、声のトーン）
  ↓
[構造化データ（JSON）]
  {
    "transcript": [...],      # 文字起こし
    "non_verbal": [...],      # 非言語データ
    "timeline_events": [...]  # タイムスタンプ付きイベント
  }
  ↓
[AI解析レイヤー]
  ├─ 言語分析（矛盾、曖昧さ、回避パターン）
  ├─ 非言語分析（視線、姿勢、表情の変化）
  └─ クロスリファレンス（言語 vs 非言語の一致度）
  ↓
[ナレッジベースとの突合]
  ↓
[総合評価レポート]
```

#### メリット
- **精度が高い**: 多角的な分析が可能
- **再現性がある**: 同じデータなら同じ結果
- **根拠が明確**: どのデータから判断したか追跡可能
- **長い動画に対応**: チャンク化して並列処理
- **改善が容易**: 各レイヤーを独立して改善できる

#### デメリット
- 実装が複雑
- 開発コストが高い
- 処理時間が長い

#### 精度スコア: ⭐⭐⭐⭐⭐（5/5）

---

### パターンC: ハイブリッド方式（バランス型・現実的）

```
[動画]
  ↓
[チャンク化] (5分単位で分割)
  ↓
[並列処理]
  ├─ チャンク1 → [AI解析] → 部分レポート1
  ├─ チャンク2 → [AI解析] → 部分レポート2
  └─ チャンクN → [AI解析] → 部分レポートN
  ↓
[統合レイヤー]
  - 部分レポートを統合
  - 矛盾点の検出
  - 時系列での変化パターン抽出
  ↓
[最終AI評価]
  - ナレッジベースと突合
  - 総合スコアリング
  ↓
[総合評価レポート]
```

#### メリット
- **精度が比較的高い**: 細かく見るので見落としが少ない
- **長い動画に対応**: チャンク化で無制限に対応可能
- **実装が現実的**: パターンBより簡単
- **並列処理可能**: 処理時間を短縮できる

#### デメリット
- パターンBより精度は劣る
- 統合ロジックの設計が必要

#### 精度スコア: ⭐⭐⭐⭐☆（4/5）

---

## 推奨設計：パターンC（ハイブリッド方式）

### 理由
1. **精度と実装コストのバランスが良い**
2. **段階的に改善可能**（PoC → 本格版へ）
3. **長い動画にも対応**

---

## 詳細設計：ハイブリッド方式

### Phase 1: 動画の前処理

#### 1.1 チャンク化
```python
# 5分（300秒）単位で分割
chunks = split_video(video_path, chunk_duration=300)
# 例: 30分動画 → 6チャンク
```

#### 1.2 音声文字起こし（オプション：精度向上のため）
```python
# Whisper APIで文字起こし
transcript = transcribe_audio(video_path)
# 結果: タイムスタンプ付きテキスト
[
  {"start": 0.0, "end": 3.5, "text": "はい、よろしくお願いします。"},
  {"start": 3.5, "end": 8.2, "text": "前職では、えーと、Webアプリの開発を..."},
  ...
]
```

---

### Phase 2: チャンクごとの解析

各チャンクに対して、以下を解析:

#### 2.1 AIプロンプト設計（重要）

```python
prompt = f"""
あなたは行動心理学の専門家です。
以下の面談動画の一部（5分間）を解析してください。

【解析対象】
- 時間: {chunk_start}〜{chunk_end}
- 文字起こし: {transcript_chunk}

【ナレッジベース】
{knowledge_base}

【解析項目】
1. **非言語シグナル**
   - 視線の動き（逸らす、泳ぐ、固定等）
   - 表情の変化（緊張、不安、リラックス等）
   - 姿勢・ジェスチャー（腕を組む、前傾、後傾等）
   - 声のトーン・速度の変化

2. **言語分析**
   - 回答の明瞭さ（具体的 vs 曖昧）
   - 矛盾や回避パターン
   - 言葉に詰まる頻度
   - 「えーと」「まあ」などのフィラーの頻度

3. **リスクシグナルの検出**
   以下のナレッジベースに記載された「警告サイン」が
   このチャンクで検出されたかを評価してください。

【出力形式】
JSON形式で以下を出力:
{{
  "chunk_id": {chunk_id},
  "time_range": "{chunk_start} - {chunk_end}",
  "non_verbal_signals": [
    {{"timestamp": "00:03:25", "signal": "視線が左上に逸れる", "duration": "3秒", "risk_level": "中"}},
    ...
  ],
  "verbal_patterns": [
    {{"timestamp": "00:05:12", "pattern": "前職の退職理由が曖昧", "risk_level": "高"}},
    ...
  ],
  "detected_red_flags": [
    "質問に対して曖昧な回答",
    "視線が定まらない"
  ],
  "positive_signals": [
    "技術的な質問に具体的に回答",
    "適切なアイコンタクト"
  ],
  "chunk_risk_score": 35
}}
"""
```

#### 2.2 並列処理
```python
import asyncio

async def analyze_chunk(chunk, knowledge_base):
    # Gemini APIで解析
    result = await gemini_api.analyze(chunk, knowledge_base)
    return result

# 全チャンクを並列処理
results = await asyncio.gather(*[
    analyze_chunk(chunk, knowledge_base)
    for chunk in chunks
])
```

---

### Phase 3: 統合レイヤー

#### 3.1 部分レポートの統合
```python
def integrate_chunk_results(chunk_results):
    """各チャンクの結果を統合"""

    all_red_flags = []
    all_positive_signals = []
    timeline_events = []

    for result in chunk_results:
        all_red_flags.extend(result['detected_red_flags'])
        all_positive_signals.extend(result['positive_signals'])

        # タイムライン統合
        timeline_events.extend(result['non_verbal_signals'])
        timeline_events.extend(result['verbal_patterns'])

    # 時系列ソート
    timeline_events.sort(key=lambda x: x['timestamp'])

    return {
        'red_flags': list(set(all_red_flags)),  # 重複除去
        'positive_signals': list(set(all_positive_signals)),
        'timeline': timeline_events
    }
```

#### 3.2 時系列パターン分析
```python
def analyze_temporal_patterns(timeline_events):
    """時系列での変化パターンを分析"""

    # 例: 特定の質問トピックで一貫してリスクシグナルが出ているか
    patterns = []

    # 前職の話題で複数の警告サイン
    career_related = [e for e in timeline_events if '前職' in e.get('context', '')]
    if len(career_related) >= 3:
        patterns.append({
            'pattern': '前職に関する質問で複数の警告サイン',
            'risk_level': '高'
        })

    return patterns
```

---

### Phase 4: 最終評価

#### 4.1 総合AIによる最終判定
```python
final_prompt = f"""
あなたは採用面接の最終評価者です。
以下の統合データを基に、候補者の総合評価を行ってください。

【統合データ】
- 検出された警告サイン: {integrated_data['red_flags']}
- ポジティブシグナル: {integrated_data['positive_signals']}
- タイムライン: {integrated_data['timeline']}
- 時系列パターン: {temporal_patterns}

【ナレッジベース】
{knowledge_base}

【評価基準】
警告サインの数と重要度を総合的に判断し、
0-100のスコアで評価してください（低いほどリスクが高い）。

【出力】
{{
  "overall_risk_score": <0-100>,
  "risk_level": "<低/中/高>",
  "critical_concerns": [<重大な懸念事項>],
  "recommendation": "<推奨事項>",
  "confidence": "<高/中/低>"  # AI自身の判定の確信度
}}
"""
```

---

## 長い動画（30分以上）の対応

### 戦略1: チャンク数の上限なし
- 5分単位で分割 → 60分動画なら12チャンク
- 並列処理で時間を短縮

### 戦略2: 重要シーンの自動検出（高度）
```python
# 音声のトーン変化、沈黙の長さ等から
# 「重要そうなシーン」を自動検出
important_scenes = detect_important_moments(video)

# 重要シーンのみ詳細解析
for scene in important_scenes:
    detailed_analysis = analyze_scene(scene)
```

### 戦略3: サマリー + 詳細のハイブリッド
```python
# Step 1: 全体をざっくりサマリー（低解像度）
summary = analyze_full_video_summary(video)

# Step 2: リスクが検出された箇所のみ詳細解析
if summary['potential_risk_areas']:
    for risk_area in summary['potential_risk_areas']:
        detailed = analyze_specific_segment(
            video,
            start=risk_area['start'],
            end=risk_area['end']
        )
```

---

## 精度向上のための追加施策

### 1. ナレッジベースの構造化
```markdown
# red-flags.md

## カテゴリ1: コミュニケーション

### リスクシグナル: 視線が定まらない
- **検出方法**: 視線が頻繁に左右・上下に動く
- **リスクレベル**: 中
- **背景**: 不誠実さや緊張の可能性
- **誤検知の可能性**: 単なる緊張の場合もある
- **他の情報との突合**: 発言内容が曖昧な場合、リスクレベルを「高」に引き上げ
```

### 2. 文字起こしの活用（オプション）
- Whisper API（OpenAI）で高精度な文字起こし
- 言語分析の精度が大幅向上
- コスト: $0.006 / 分 → 30分で$0.18（約27円）

### 3. マルチモーダル統合
```python
# 言語と非言語の一致度チェック
def check_consistency(verbal, non_verbal):
    """
    例: 「問題ありませんでした」と言いながら
        視線が泳いでいる → 不一致 → リスク
    """
    if verbal['sentiment'] == 'positive' and non_verbal['stress_level'] == 'high':
        return {'consistency': 'low', 'risk': 'high'}
```

---

## 開発の優先順位（段階的アプローチ）

### Phase 1: MVP（最小限の動作確認）
- **実装**: パターンA（動画直接投入）
- **目的**: 動作確認、API連携の確認
- **期間**: 1〜2日

### Phase 2: 精度改善版
- **実装**: パターンC（チャンク化 + 統合）
- **目的**: 実用的な精度の達成
- **期間**: 3〜5日

### Phase 3: 本格版
- **実装**: パターンB（構造化データ + マルチモーダル）
- **目的**: 最高精度、本番運用
- **期間**: 2〜3週間

---

## まとめ：推奨設計

```
【ハイブリッド方式（パターンC）を推奨】

1. 動画を5分単位でチャンク化
2. 各チャンクをGemini APIで並列解析
   - 非言語シグナル検出
   - 言語パターン分析
   - リスクシグナル検出
3. 結果を統合して時系列パターン分析
4. 最終AIで総合評価
5. ナレッジベースと突合してレポート生成

【精度を高めるポイント】
- 構造化されたプロンプト設計
- タイムスタンプ付きイベントログ化
- 言語 vs 非言語の一致度チェック
- オプション: Whisperで文字起こし
```

---

## 次のステップ

この設計で進めて良いか、ご意見をお聞かせください。

特に以下の点について:
1. **Phase 1（MVP）から始めるか、Phase 2から始めるか**
2. **文字起こし（Whisper）を使うか、使わないか**
3. **5分チャンクで良いか、別の時間が良いか**
4. **他に重視したい精度向上のポイント**
