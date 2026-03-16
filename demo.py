"""
AI面談動画解析システム - デモンストレーション用スクリプト

使い方:
    # デモモード（サンプル動画不要、即実行可能）
    python demo.py --demo

    # 実動画モード（動画ファイルを指定）
    python demo.py --video path/to/video.mp4

    # HTMLレポート生成（デフォルト: ダウンロードフォルダ）
    python demo.py --demo --html
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def print_banner():
    """バナー表示"""
    print("\n" + "="*70)
    print("  AI面談動画解析システム - デモンストレーション")
    print("="*70 + "\n")


def print_section(title):
    """セクションヘッダー表示"""
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}\n")


def get_demo_result():
    """デモ用のサンプル結果を返す"""
    return {
        "overall_risk_score": 95,
        "risk_level": "非常に低い",
        "evaluation": {
            "communication": {
                "score": 90,
                "observations": [
                    "適切なアイコンタクトを維持",
                    "明瞭な発話、聞き取りやすい声のトーン",
                    "質問に対して具体的な事例を交えて回答"
                ],
                "confidence": "高"
            },
            "stress_tolerance": {
                "score": 95,
                "observations": [
                    "難しい質問に対しても冷静に対応",
                    "予期しない質問でも動揺せず、思考を整理してから回答",
                    "プレッシャー下でも論理的な説明を維持"
                ],
                "confidence": "高"
            },
            "reliability": {
                "score": 98,
                "observations": [
                    "過去の実績について具体的な数値やエピソードを提示",
                    "質問に対して誠実に回答、誇張や曖昧な表現なし",
                    "自身の弱点についても率直に認め、改善策を説明"
                ],
                "confidence": "高"
            },
            "teamwork": {
                "score": 92,
                "observations": [
                    "チーム経験について前向きに語る",
                    "他者との協力関係を重視する姿勢が見られる",
                    "過去のチームでの役割を明確に説明"
                ],
                "confidence": "高"
            }
        },
        "red_flags": [],
        "positive_signals": [
            "技術的な質問に対して深い理解を示す具体的な回答",
            "自己学習の習慣があり、最新技術へのキャッチアップ姿勢",
            "過去のトラブル対応経験を冷静に振り返り、学びを説明",
            "長期的なキャリアビジョンが明確"
        ],
        "recommendation": "技術力・人間性ともに優秀な候補者。アサインを強く推奨。特にストレス耐性と信頼性の高さが際立っている。",
        "disclaimer": "本評価はAIによる参考情報です。最終的な採用判断は必ず人間が行ってください。",
        "analysis_metadata": {
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": "gemini-2.5-flash",
            "video_duration": "30分",
            "confidence_level": "高"
        }
    }


def print_result(result, colorful=True):
    """結果を見やすく表示"""

    # 総合スコア
    print_section("[総合評価]")
    score = result["overall_risk_score"]
    risk_level = result["risk_level"]

    # スコアバーを表示
    bar_length = 50
    filled_length = int(bar_length * score // 100)
    bar = '=' * filled_length + '-' * (bar_length - filled_length)

    print(f"  総合スコア: {score}点 / 100点")
    print(f"  [{bar}] {score}%")
    print(f"  リスクレベル: {risk_level}")

    # 各項目の評価
    print_section("[詳細評価]")

    eval_data = result["evaluation"]
    for category, data in eval_data.items():
        category_name = {
            "communication": "コミュニケーション能力",
            "stress_tolerance": "ストレス耐性",
            "reliability": "信頼性",
            "teamwork": "チームワーク"
        }.get(category, category)

        print(f"\n  【{category_name}】")
        print(f"    スコア: {data['score']}点")
        print(f"    確信度: {data['confidence']}")
        print(f"    観察事項:")
        for obs in data['observations']:
            print(f"      - {obs}")

    # ポジティブシグナル
    if result.get("positive_signals"):
        print_section("[ポジティブシグナル]")
        for signal in result["positive_signals"]:
            print(f"  + {signal}")

    # レッドフラグ
    if result.get("red_flags"):
        print_section("[レッドフラグ]")
        for flag in result["red_flags"]:
            print(f"  ! {flag}")
    else:
        print_section("[レッドフラグ]")
        print("  なし（リスク要因は検出されませんでした）")

    # 推奨事項
    print_section("[推奨事項]")
    print(f"  {result['recommendation']}")

    # 免責事項
    print(f"\n  [注] {result['disclaimer']}\n")


def generate_html_report(result, output_path):
    """HTMLレポートを生成"""

    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI面談動画解析レポート</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', 'Yu Gothic', 'Meiryo', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .score-section {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            margin-bottom: 30px;
        }}

        .score-circle {{
            width: 200px;
            height: 200px;
            margin: 0 auto 20px;
            border-radius: 50%;
            background: conic-gradient(
                #667eea 0deg {result['overall_risk_score'] * 3.6}deg,
                #e0e0e0 {result['overall_risk_score'] * 3.6}deg 360deg
            );
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }}

        .score-circle::before {{
            content: '';
            width: 160px;
            height: 160px;
            background: white;
            border-radius: 50%;
            position: absolute;
        }}

        .score-text {{
            position: relative;
            z-index: 1;
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
        }}

        .risk-level {{
            font-size: 1.5em;
            color: #28a745;
            font-weight: bold;
            margin-top: 10px;
        }}

        .section {{
            margin-bottom: 30px;
        }}

        .section-title {{
            font-size: 1.5em;
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}

        .category {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
        }}

        .category-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .category-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }}

        .category-score {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .progress-bar {{
            width: 100%;
            height: 10px;
            background: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 15px;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 1s ease;
        }}

        .observations {{
            list-style: none;
        }}

        .observations li {{
            padding: 8px 0 8px 25px;
            position: relative;
        }}

        .observations li::before {{
            content: '✓';
            position: absolute;
            left: 0;
            color: #28a745;
            font-weight: bold;
        }}

        .confidence {{
            display: inline-block;
            padding: 5px 15px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 0.9em;
        }}

        .positive-signals {{
            background: #d4edda;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #28a745;
        }}

        .positive-signals li {{
            padding: 8px 0 8px 25px;
            position: relative;
        }}

        .positive-signals li::before {{
            content: '✨';
            position: absolute;
            left: 0;
        }}

        .red-flags {{
            background: #f8d7da;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #dc3545;
        }}

        .no-red-flags {{
            background: #d4edda;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #28a745;
            text-align: center;
            font-weight: bold;
            color: #28a745;
        }}

        .recommendation {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #ffc107;
            font-size: 1.1em;
            line-height: 1.6;
        }}

        .disclaimer {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            color: #004085;
            margin-top: 30px;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 AI面談動画解析レポート</h1>
            <p>候補者の行動心理学的評価</p>
        </div>

        <div class="content">
            <!-- 総合スコア -->
            <div class="score-section">
                <div class="score-circle">
                    <div class="score-text">{result['overall_risk_score']}</div>
                </div>
                <div class="risk-level">リスクレベル: {result['risk_level']}</div>
            </div>

            <!-- 詳細評価 -->
            <div class="section">
                <h2 class="section-title">📋 詳細評価</h2>
"""

    # 各カテゴリーの評価
    category_names = {
        "communication": "コミュニケーション能力",
        "stress_tolerance": "ストレス耐性",
        "reliability": "信頼性",
        "teamwork": "チームワーク"
    }

    for category, data in result["evaluation"].items():
        category_name = category_names.get(category, category)
        score = data["score"]

        html_content += f"""
                <div class="category">
                    <div class="category-header">
                        <div class="category-name">{category_name}</div>
                        <div class="category-score">{score}点</div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {score}%"></div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <span class="confidence">確信度: {data['confidence']}</span>
                    </div>
                    <ul class="observations">
"""

        for obs in data["observations"]:
            html_content += f"                        <li>{obs}</li>\n"

        html_content += """
                    </ul>
                </div>
"""

    html_content += """
            </div>

            <!-- ポジティブシグナル -->
            <div class="section">
                <h2 class="section-title">✨ ポジティブシグナル</h2>
                <div class="positive-signals">
                    <ul>
"""

    for signal in result.get("positive_signals", []):
        html_content += f"                        <li>{signal}</li>\n"

    html_content += """
                    </ul>
                </div>
            </div>

            <!-- レッドフラグ -->
            <div class="section">
                <h2 class="section-title">⚠️ レッドフラグ</h2>
"""

    if result.get("red_flags"):
        html_content += """
                <div class="red-flags">
                    <ul>
"""
        for flag in result["red_flags"]:
            html_content += f"                        <li>{flag}</li>\n"
        html_content += """
                    </ul>
                </div>
"""
    else:
        html_content += """
                <div class="no-red-flags">
                    ✅ なし（リスク要因は検出されませんでした）
                </div>
"""

    html_content += f"""
            </div>

            <!-- 推奨事項 -->
            <div class="section">
                <h2 class="section-title">💡 推奨事項</h2>
                <div class="recommendation">
                    {result['recommendation']}
                </div>
            </div>

            <!-- 免責事項 -->
            <div class="disclaimer">
                ⓘ {result['disclaimer']}
            </div>
        </div>

        <div class="footer">
            生成日時: {result['analysis_metadata']['analyzed_at']}<br>
            使用モデル: {result['analysis_metadata']['model']}<br>
            動画時間: {result['analysis_metadata']['video_duration']}
        </div>
    </div>
</body>
</html>
"""

    # ファイルに保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='AI面談動画解析システム - デモンストレーション',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デモモード（サンプルデータで即実行）
  python demo.py --demo

  # HTMLレポート生成
  python demo.py --demo --html

  # 実動画モード（動画ファイルを指定）
  python demo.py --video path/to/video.mp4
        """
    )

    parser.add_argument('--demo', action='store_true',
                        help='デモモード（サンプルデータを使用）')
    parser.add_argument('--video', type=str,
                        help='解析する動画ファイルのパス')
    parser.add_argument('--html', action='store_true',
                        help='HTMLレポートを生成')
    parser.add_argument('--output', type=str,
                        help='HTMLレポートの出力先（デフォルト: ダウンロードフォルダ）')

    args = parser.parse_args()

    # どちらも指定されていない場合はヘルプを表示
    if not args.demo and not args.video:
        parser.print_help()
        return

    print_banner()

    # デモモード
    if args.demo:
        print("  [デモモード] 実行中...")
        print("  （サンプルデータを使用して結果を表示します）\n")

        result = get_demo_result()

        # 結果を表示
        print_result(result)

        # HTMLレポート生成
        if args.html or True:  # デフォルトでHTML生成
            # 出力先の決定
            if args.output:
                output_path = Path(args.output)
            else:
                # ダウンロードフォルダ
                downloads_folder = Path.home() / "Downloads"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = downloads_folder / f"AI面談解析レポート_{timestamp}.html"

            print_section("[HTMLレポート生成]")
            html_path = generate_html_report(result, output_path)
            print(f"  [完了] HTMLレポートを生成しました:")
            print(f"     {html_path}")
            print(f"\n  [ヒント] ブラウザで開くには:")
            print(f"     {html_path} をダブルクリック")
            print()

    # 実動画モード
    elif args.video:
        print(f"  [実動画モード] 実行中...")
        print(f"  動画: {args.video}\n")

        # 実際のanalyzer.pyを実行
        # （ここでは簡略化のため、実装は省略）
        print("  [警告] 実動画モードはまだ実装されていません。")
        print("  analyzer.pyを直接実行してください:")
        print(f"     python src/analyzer.py {args.video}")

    print("="*70)
    print("  [完了] デモ完了")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
