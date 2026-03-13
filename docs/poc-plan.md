# プロトタイプ実装計画（PoC）

## 目標

**インターネット上の知識を活用し、動画解析が動作する最小限のプロトタイプを作成する**

---

## Phase 1: ナレッジベースの構築（1〜2日）

### 収集する情報源

#### 1. 行動心理学の基礎知識
- **ソース**: Wikipedia、オープンな学術サイト
- **内容**:
  - 非言語コミュニケーション（視線、姿勢、ジェスチャー）
  - ストレス反応の兆候
  - 嘘の検知に関する研究
  - 信頼性・誠実性の評価指標

#### 2. 面接評価のベストプラクティス
- **ソース**: HR関連のブログ、公開されている評価シート
- **内容**:
  - 構造化面接の評価項目
  - コンピテンシー評価の観点
  - レッドフラグ（警告サイン）のリスト

#### 3. SES/IT業界特有のリスク要因
- **ソース**: 業界フォーラム、QiitaなどのTech記事
- **内容**:
  - よくあるトラブル事例
  - 問題のある要員の特徴
  - 成功する要員の特徴

### ドキュメント構造

```
knowledge-base/
├── behavioral-psychology.md      # 行動心理学の基礎
├── interview-evaluation.md       # 面接評価の観点
├── red-flags.md                  # 警告サイン（リスク要因）
├── success-patterns.md           # 成功パターン
└── scoring-criteria.md           # スコアリング基準
```

### サンプル: red-flags.md

```markdown
# 警告サイン（リスク要因）

## コミュニケーション面
- 質問に対して曖昧な回答が多い
- 視線が定まらない、頻繁に目を逸らす
- 過度に早口、または極端にゆっくり話す
- 話の内容に矛盾が見られる

## 態度・姿勢
- 防衛的な態度（腕を組む、後ろに傾く）
- 過度に緊張（手の震え、声の震え）
- 逆に過度にリラックスしすぎ（無関心に見える）

## 回答内容
- 前職の退職理由が曖昧
- 他者への批判が多い
- 具体的なエピソードが出てこない
- 責任転嫁の傾向

## 技術面
- 経歴に対して技術知識が浅い
- 実務経験の説明が抽象的
- 最近の技術動向に無関心
```

---

## Phase 2: プロトタイプの実装（2〜3日）

### 技術スタック

- **言語**: Python 3.10+
- **AI API**: Gemini 1.5 Flash（まずはこれで開始）
- **UI**: Streamlit（簡易Webインターフェース）
- **依存ライブラリ**:
  - `google-generativeai`: Gemini API
  - `streamlit`: WebUI
  - `python-dotenv`: 環境変数管理

### ディレクトリ構造

```
ai_interview-analysis/
├── src/
│   ├── main.py                   # Streamlitアプリのエントリーポイント
│   ├── ai_analyzer.py            # AI解析ロジック
│   ├── knowledge_loader.py       # ナレッジベース読み込み
│   └── report_generator.py       # レポート生成
├── knowledge-base/               # ナレッジベース
│   ├── behavioral-psychology.md
│   ├── red-flags.md
│   └── scoring-criteria.md
├── data/                         # テストデータ
│   └── sample-videos/           # サンプル動画（.gitignore対象）
├── outputs/                      # 出力レポート
│   └── reports/
├── .env.example                  # 環境変数のサンプル
├── requirements.txt              # Pythonパッケージ
└── README.md
```

### コア機能

#### 1. knowledge_loader.py
```python
"""ナレッジベースの読み込み"""
import os
from pathlib import Path

def load_knowledge_base():
    """全ナレッジをテキストとして結合"""
    knowledge_dir = Path("knowledge-base")
    knowledge_text = ""

    for md_file in knowledge_dir.glob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            knowledge_text += f"\n\n## {md_file.stem}\n\n"
            knowledge_text += f.read()

    return knowledge_text
```

#### 2. ai_analyzer.py
```python
"""AI解析のコアロジック"""
import google.generativeai as genai
from pathlib import Path

class VideoAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_video(self, video_path: str, knowledge_base: str):
        """動画を解析してリスク評価を返す"""

        # 動画ファイルをアップロード
        video_file = genai.upload_file(path=video_path)

        # プロンプト構築
        prompt = f"""
あなたは採用面接の専門家です。
以下のナレッジベースを参考に、面談動画を解析し、候補者のリスクを評価してください。

【ナレッジベース】
{knowledge_base}

【評価項目】
1. コミュニケーション能力（0-100）
2. ストレス耐性（0-100）
3. 信頼性・誠実性（0-100）
4. 技術的な適性（0-100）

【出力形式】
JSON形式で以下を出力してください:
{{
  "overall_risk_score": <0-100の数値。低いほどリスクが高い>,
  "communication_score": <0-100>,
  "stress_tolerance_score": <0-100>,
  "reliability_score": <0-100>,
  "technical_score": <0-100>,
  "red_flags": [<検出された警告サインのリスト>],
  "positive_points": [<良い点のリスト>],
  "recommendation": "<総合的な推奨事項>"
}}
"""

        # API呼び出し
        response = self.model.generate_content([prompt, video_file])

        return response.text
```

#### 3. main.py（Streamlit UI）
```python
"""Streamlit WebUIのメインアプリ"""
import streamlit as st
from ai_analyzer import VideoAnalyzer
from knowledge_loader import load_knowledge_base
import json
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

st.title("🎥 AI面談動画解析システム（PoC）")

# サイドバー: API設定
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input(
        "Gemini APIキー",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password"
    )

# メイン画面
st.header("動画アップロード")
uploaded_file = st.file_uploader("面談動画をアップロード", type=["mp4", "mov", "avi"])

if uploaded_file and api_key:
    # 一時ファイルとして保存
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # 解析開始
    if st.button("🚀 解析開始"):
        with st.spinner("動画を解析中..."):
            # ナレッジベース読み込み
            knowledge = load_knowledge_base()

            # AI解析
            analyzer = VideoAnalyzer(api_key)
            result_json = analyzer.analyze_video(temp_path, knowledge)

            # 結果をパース
            try:
                result = json.loads(result_json)

                # 結果表示
                st.success("解析完了！")

                # スコア表示
                st.header("📊 総合評価")
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("総合スコア", f"{result['overall_risk_score']}/100")

                with col2:
                    risk_level = "低" if result['overall_risk_score'] >= 70 else "中" if result['overall_risk_score'] >= 40 else "高"
                    st.metric("リスクレベル", risk_level)

                # 詳細スコア
                st.header("📈 詳細スコア")
                st.write(f"**コミュニケーション**: {result['communication_score']}/100")
                st.write(f"**ストレス耐性**: {result['stress_tolerance_score']}/100")
                st.write(f"**信頼性**: {result['reliability_score']}/100")
                st.write(f"**技術適性**: {result['technical_score']}/100")

                # 警告サイン
                if result['red_flags']:
                    st.header("⚠️ 警告サイン")
                    for flag in result['red_flags']:
                        st.warning(flag)

                # 良い点
                if result['positive_points']:
                    st.header("✅ 良い点")
                    for point in result['positive_points']:
                        st.success(point)

                # 推奨事項
                st.header("💡 推奨事項")
                st.info(result['recommendation'])

            except json.JSONDecodeError:
                st.error("結果のパースに失敗しました")
                st.text(result_json)

        # 一時ファイル削除
        os.remove(temp_path)

else:
    st.info("動画をアップロードし、APIキーを設定してください")
```

---

## Phase 3: 初期ナレッジの収集（即座に開始可能）

### 今すぐできること

1. **Webから情報収集**
   - 行動心理学の基礎（Wikipedia等）
   - 面接評価の観点（HR系ブログ）
   - IT業界のトラブル事例（Qiita、Note等）

2. **ナレッジのMarkdown化**
   - 収集した情報を構造化
   - Gitで管理

---

## 見積もり

### 開発時間
- **ナレッジベース構築**: 1〜2日
- **プロトタイプ実装**: 2〜3日
- **動作検証**: 1日
- **合計**: 4〜6日

### コスト
- **開発コスト**: 0円（自社開発）
- **API利用料（検証フェーズ）**: 約1,000円/月
- **インフラ**: 0円（ローカル実行）

---

## 次のアクション

どこから始めますか？

### オプション1: ナレッジベースの構築から
- インターネットから情報収集
- Markdown形式でドキュメント化
- リポジトリにコミット

### オプション2: 実装から（ダミーナレッジで開始）
- Pythonコードの実装
- 簡易的なナレッジで動作確認
- 後からナレッジを充実化

### オプション3: 両方を並行
- ナレッジ収集 + 実装を同時進行
- 最短で動くものを完成

どの方法で進めますか？または、まずは私が簡単なナレッジサンプルを作成して、実装のベースコードを書いてみましょうか？
