"""
AI面談動画解析システム - Streamlit Web UI

使い方:
    streamlit run src/streamlit_app.py
"""

# Windows環境でUTF-8出力を有効化（エンコーディングエラー対策）
import sys
import io

if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except (AttributeError, ValueError):
        # Streamlit環境などで既にstdoutが管理されている場合はスキップ
        pass

# プロジェクトルートをPythonパスに追加（srcモジュールのインポート用）
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import os
import json
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="AI面談動画解析システム",
    page_icon="🎥",
    layout="wide"
)

# タイトル
st.title("🎥 AI面談動画解析システム")
st.markdown("動画をアップロードして、AIによる行動心理学的評価を取得します")

# サイドバー: 設定
with st.sidebar:
    st.header("⚙️ 設定")

    api_key = st.text_input(
        "Gemini APIキー",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Google AI StudioでAPIキーを取得してください"
    )

    model = st.selectbox(
        "使用モデル",
        ["gemini-2.5-flash", "gemini-1.5-pro"],
        help="gemini-2.5-flashが推奨（低コスト・高速）"
    )

    # チャンク解析オプション
    use_chunking = st.checkbox(
        "長時間動画のチャンク解析を使用",
        value=True,
        help="30分以上の動画を5分単位に分割して解析します。並列処理で高速化されます。"
    )

    if use_chunking:
        chunk_duration = st.slider(
            "チャンク長（分）",
            min_value=3,
            max_value=10,
            value=5,
            help="動画を何分単位で分割するか"
        )

        use_parallel = st.checkbox(
            "並列処理を使用",
            value=False,
            help="複数チャンクを同時に解析して処理時間を短縮します（ファイルアクセスエラーが発生する場合はOFFにしてください）"
        )

    st.divider()

    st.info("""
    **使い方:**
    1. APIキーを入力
    2. 面談動画をアップロード
    3. 解析開始ボタンをクリック
    4. 結果を確認
    """)

# メインエリア
uploaded_file = st.file_uploader(
    "面談動画をアップロード",
    type=["mp4", "mov", "avi", "webm"],
    help="対応形式: MP4, MOV, AVI, WebM（推奨: 30分以内）"
)

if uploaded_file is not None:
    # 動画情報表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ファイル名", uploaded_file.name)
    with col2:
        st.metric("サイズ", f"{uploaded_file.size / 1024 / 1024:.1f} MB")
    with col3:
        st.metric("形式", uploaded_file.type)

    # 一時保存ディレクトリ（絶対パスを使用）
    temp_dir = Path(__file__).parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)

    # ファイル名を英数字のみに変更（Gemini API用）
    # 元の拡張子を保持し、タイムスタンプで一意性を確保
    from datetime import datetime
    import os as os_module
    file_ext = os_module.path.splitext(uploaded_file.name)[1]  # 例: .mp4
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"uploaded_video_{timestamp}{file_ext}"
    temp_path = temp_dir / safe_filename

    # ファイル保存
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success(f"✅ ファイルをアップロードしました: {uploaded_file.name}")

    # 解析ボタン
    if st.button("🚀 解析開始", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ APIキーを入力してください")
        else:
            # チャンク解析を使用するかどうかを判定
            use_chunk_analysis = use_chunking and uploaded_file.size > 50 * 1024 * 1024  # 50MB以上

            with st.spinner("動画を解析中... これには数分かかることがあります"):
                # リアルタイムログ表示エリア
                log_container = st.expander("📝 処理ログ（リアルタイム）", expanded=True)
                log_text = log_container.empty()
                log_messages = []

                def log_callback(msg):
                    """ログメッセージをUIに表示"""
                    log_messages.append(msg)
                    # 最新50行のみ表示
                    display_logs = log_messages[-50:]
                    log_text.text("\n".join(display_logs))

                try:
                    if use_chunk_analysis:
                        # チャンク解析を使用
                        from src.video_chunker import VideoChunker, get_video_duration
                        from src.chunked_analyzer import ChunkedVideoAnalyzer
                        from src.chunk_integrator import ChunkIntegrator

                        # 進捗表示
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        status_text.text("動画の長さを取得中...")

                        # 動画の長さを取得
                        try:
                            duration_seconds = get_video_duration(str(temp_path))
                        except Exception as e:
                            # ffmpegが利用できない場合は推定値を使用
                            st.warning(f"動画の長さを自動取得できませんでした。推定値を使用します。({str(e)})")
                            duration_seconds = 1800  # 30分と仮定

                        progress_bar.progress(10)

                        # チャンク化
                        status_text.text(f"動画を{chunk_duration}分単位に分割中...")
                        chunker = VideoChunker(chunk_duration_seconds=chunk_duration * 60)
                        chunks = chunker.create_chunks(str(temp_path), duration_seconds)

                        progress_bar.progress(20)

                        # チャンク解析
                        status_text.text(f"{len(chunks)}個のチャンクを解析中...")
                        analyzer = ChunkedVideoAnalyzer(api_key=api_key, model=model, log_callback=log_callback)
                        chunk_results = analyzer.analyze_chunks(chunks, parallel=use_parallel)

                        progress_bar.progress(80)

                        # 統合
                        status_text.text("結果を統合中...")
                        integrator = ChunkIntegrator()
                        result = integrator.integrate_chunks(chunk_results)

                        progress_bar.progress(100)
                        status_text.text("✅ 解析完了!")

                        # チャンク解析結果を保存（詳細表示用）
                        st.session_state['chunk_results'] = chunk_results

                        # デバッグ: チャンク結果の詳細を表示
                        with st.expander("🔍 デバッグ: チャンク処理結果の詳細"):
                            for idx, chunk_res in enumerate(chunk_results):
                                st.subheader(f"Chunk {idx} 処理結果")
                                st.json(chunk_res)

                    else:
                        # 通常の解析を使用
                        from src.analyzer import VideoAnalyzer

                        # 解析実行
                        analyzer = VideoAnalyzer(api_key=api_key, model=model, log_callback=log_callback)
                        result = analyzer.analyze(str(temp_path))

                    # 成功メッセージ
                    st.success("✅ 解析完了!")

                    # デバッグ：結果の内容を確認
                    if result.get("overall_risk_score", 0) == 0:
                        st.warning("⚠️ デバッグ情報：スコアが0です。結果の内容を確認してください。")
                        with st.expander("🔍 デバッグ：解析結果の生データ"):
                            st.json(result)

                    # 総合評価
                    st.header("📊 総合評価")
                    score = result.get("overall_risk_score", 0)
                    risk_level = result.get("risk_level", "不明")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("総合スコア", f"{score}/100", help="高いほど良い評価")
                    with col2:
                        # リスクレベルに応じて色を変更
                        if risk_level == "低":
                            st.success(f"リスクレベル: {risk_level}")
                        elif risk_level == "中":
                            st.warning(f"リスクレベル: {risk_level}")
                        else:
                            st.error(f"リスクレベル: {risk_level}")

                    # 詳細評価
                    st.header("📋 詳細評価")

                    evaluation = result.get("evaluation", {})

                    # 各カテゴリーをタブで表示
                    if evaluation:
                        tabs = st.tabs(list(evaluation.keys()))

                        for tab, (category, data) in zip(tabs, evaluation.items()):
                            with tab:
                                st.subheader(f"{category}")

                                # スコア表示
                                score_val = data.get("score", 0)
                                st.progress(score_val / 100)
                                st.metric("スコア", f"{score_val}/100")

                                # 観察事項
                                st.write("**観察事項:**")
                                observations = data.get("observations", [])
                                for obs in observations:
                                    st.write(f"- {obs}")

                                # 確信度
                                confidence = data.get("confidence", "不明")
                                st.write(f"**確信度:** {confidence}")

                    # リスクシグナル
                    st.header("⚠️ リスクシグナル")
                    red_flags = result.get("red_flags", [])
                    if red_flags:
                        for flag in red_flags:
                            st.warning(f"- {flag}")
                    else:
                        st.success("重大なリスクシグナルは検出されませんでした")

                    # ポジティブシグナル
                    st.header("✅ ポジティブシグナル")
                    positive_signals = result.get("positive_signals", [])
                    if positive_signals:
                        for signal in positive_signals:
                            st.success(f"- {signal}")
                    else:
                        st.info("特筆すべきポジティブシグナルはありませんでした")

                    # 推奨事項
                    st.header("💡 推奨事項")
                    recommendation = result.get("recommendation", "推奨事項なし")
                    st.info(recommendation)

                    # 免責事項
                    disclaimer = result.get("disclaimer", "")
                    if disclaimer:
                        st.warning(disclaimer)

                    # チャンク別詳細（チャンク解析を使用した場合のみ）
                    if 'chunk_results' in st.session_state and st.session_state['chunk_results']:
                        st.header("⏱️ 時系列分析")

                        chunk_results = st.session_state['chunk_results']

                        # 一貫性の問題があれば表示
                        if "chunk_analysis" in result:
                            consistency_issues = result["chunk_analysis"].get("consistency_issues", [])
                            if consistency_issues:
                                st.warning("⚠️ チャンク間の一貫性に関する注意点:")
                                for issue in consistency_issues:
                                    st.write(f"- {issue}")

                            # 時系列パターンを表示
                            patterns = result["chunk_analysis"].get("temporal_patterns", {})
                            if patterns.get("score_trend"):
                                trend = patterns["score_trend"]
                                if trend == "improving":
                                    st.success("📈 スコアが面談の進行とともに向上しています")
                                elif trend == "declining":
                                    st.warning("📉 スコアが面談の進行とともに低下しています")
                                else:
                                    st.info("📊 スコアは安定しています")

                        # チャンク別の詳細を折りたたみで表示
                        with st.expander("📋 チャンク別の詳細評価"):
                            for chunk_result in chunk_results:
                                chunk_id = chunk_result.get("chunk_id", 0)
                                time_range = chunk_result.get("chunk_time_range", {})
                                start_min = time_range.get("start", 0) // 60
                                end_min = time_range.get("end", 0) // 60

                                st.subheader(f"チャンク #{chunk_id + 1} ({start_min}-{end_min}分)")

                                # エラーがあれば表示
                                if "error" in chunk_result:
                                    st.error(f"❌ エラー: {chunk_result['error']}")
                                    continue

                                # スコアを表示
                                score = chunk_result.get("overall_risk_score", 0)
                                st.metric("スコア", f"{score}/100")

                                # 評価項目を簡潔に表示
                                eval_data = chunk_result.get("evaluation", {})
                                if eval_data:
                                    cols = st.columns(4)
                                    for idx, (cat_key, cat_data) in enumerate(eval_data.items()):
                                        cat_score = cat_data.get("score", 0)
                                        with cols[idx % 4]:
                                            st.metric(cat_key, f"{cat_score}")

                                st.divider()

                    # JSON出力（折りたたみ）
                    with st.expander("📄 詳細なJSON出力を表示"):
                        st.json(result)

                        # ダウンロードボタン
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        json_str = json.dumps(result, ensure_ascii=False, indent=2)
                        st.download_button(
                            label="📥 JSONをダウンロード",
                            data=json_str,
                            file_name=f"analysis_result_{timestamp}.json",
                            mime="application/json"
                        )

                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {str(e)}")
                    st.exception(e)

                finally:
                    # 一時ファイル削除
                    if temp_path.exists():
                        temp_path.unlink()
                        st.info("一時ファイルを削除しました")

else:
    # ファイルがアップロードされていない場合
    st.info("👆 動画ファイルをアップロードしてください")

    # 使用例を表示
    with st.expander("📘 使用例とベストプラクティス"):
        st.markdown("""
        ### 推奨される動画
        - **時間**: 10-30分程度
        - **形式**: MP4（H.264エンコード）
        - **解像度**: 720p以上
        - **音質**: クリアな音声

        ### 評価のポイント
        1. **非言語コミュニケーション**: 表情、視線、姿勢
        2. **言語パターン**: 回答の明瞭さ、一貫性
        3. **ストレス耐性**: 難しい質問への対応
        4. **信頼性**: 具体的なエピソード、正直さ

        ### 注意事項
        - 候補者の同意を必ず取得してください
        - AIの評価は参考情報として扱ってください
        - 最終判断は人間が行ってください
        """)

# フッター
st.divider()
st.caption("AI面談動画解析システム v1.0 | Powered by Gemini 2.5 Flash")
