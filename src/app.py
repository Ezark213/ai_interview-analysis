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
import pandas as pd
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

    # APIキー読み込み（.env / Streamlit Secrets 両対応）
    from src.config import load_api_keys
    api_key_1, api_key_2, openai_key = load_api_keys()

    if api_key_1 and api_key_2:
        st.success("✅ APIキー1, 2が設定されています（自動切り替え有効）")
    elif api_key_1:
        st.info("ℹ️ APIキー1のみ設定されています")
    else:
        st.error("❌ APIキーが設定されていません")

    model = st.selectbox(
        "使用モデル",
        ["gemini-2.5-flash", "gemini-1.5-pro"],
        help="gemini-2.5-flashが推奨（低コスト・高速）"
    )

    # チャンク解析オプション
    use_chunking = st.checkbox(
        "長時間動画のチャンク解析を使用",
        value=True,
        help="動画の長さに応じて自動的に分割数を決定します（15分以下: 分割なし、15-30分: 2分割、30-60分: 3分割、60-90分: 4分割、90分超: 5分割）"
    )

    if use_chunking:
        use_parallel = st.checkbox(
            "並列処理を使用",
            value=False,
            help="複数チャンクを同時に解析して処理時間を短縮します（ファイルアクセスエラーが発生する場合はOFFにしてください）"
        )

    st.divider()

    # Whisper文字起こしオプション
    st.subheader("Whisper文字起こし")
    if openai_key:
        use_whisper = st.checkbox(
            "Whisper文字起こしを使用",
            value=False,
            help="OpenAI Whisper APIで音声を文字起こしし、発言内容と非言語行動を照合します（有料: $0.006/分）"
        )
        if use_whisper:
            st.caption("Whisper APIの利用には費用が発生します（約$0.006/分）")
    else:
        use_whisper = False
        st.info("OpenAI APIキーを設定するとWhisper文字起こし機能が使えます")

    st.divider()

    # 評価基準プリセット選択
    st.subheader("評価基準")
    from src.knowledge_loader import list_presets, load_combined_knowledge

    presets = list_presets()
    preset_options = {"デフォルト（SES面談）": None}
    for p in presets:
        preset_options[p["name"]] = p["id"]

    selected_preset_name = st.selectbox(
        "評価基準プリセット",
        list(preset_options.keys()),
        help="面接の種類に合った評価基準を選択"
    )
    selected_preset = preset_options[selected_preset_name]

    # カスタムナレッジベースのアップロード
    uploaded_kb = st.file_uploader(
        "カスタム評価基準（.md）をアップロード（オプション）",
        type=["md"],
        help="独自の評価基準をMarkdown形式でアップロードできます"
    )
    custom_content = uploaded_kb.read().decode("utf-8") if uploaded_kb else None

    st.divider()

    st.info("""
    **使い方:**
    1. 面談動画をアップロード
    2. 解析開始ボタンをクリック
    3. 結果を確認
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

    # ファイルが正しく保存されたか確認
    import time
    time.sleep(0.5)  # ファイルシステムの同期を待つ
    if not temp_path.exists():
        st.error(f"❌ ファイル保存に失敗しました: {temp_path}")
    else:
        file_size_mb = temp_path.stat().st_size / 1024 / 1024
        st.success(f"✅ ファイルをアップロードしました: {uploaded_file.name} ({file_size_mb:.1f}MB)")

        # Streamlit Cloud上限（200MB）に近い場合の警告
        if file_size_mb > 180:
            st.warning("⚠️ ファイルサイズが大きいです（200MB上限に近い）。クラウド環境では処理に失敗する場合があります。")

    # 解析ボタン
    if st.button("🚀 解析開始", type="primary", use_container_width=True):
        if not api_key_1:
            st.error("❌ APIキーが設定されていません。.envファイルまたはStreamlit Secretsを確認してください。")
        else:
            # ナレッジベースの読み込み
            try:
                knowledge_text = load_combined_knowledge(
                    preset_id=selected_preset,
                    custom_content=custom_content
                )
            except (ValueError, FileNotFoundError) as e:
                st.error(f"❌ ナレッジベースの読み込みに失敗: {e}")
                knowledge_text = None

            # 動画の長さを取得してスマートチャンク分割戦略を決定
            from src.video_chunker import VideoChunker, get_video_duration, calculate_chunk_strategy

            try:
                duration_seconds = get_video_duration(str(temp_path))
            except Exception as e:
                st.warning(f"動画の長さを自動取得できませんでした。推定値を使用します。({str(e)})")
                duration_seconds = 1800  # 30分と仮定

            chunk_strategy = calculate_chunk_strategy(duration_seconds)

            # チャンク解析を使用するかどうかを判定（スマート判定）
            use_chunk_analysis = use_chunking and chunk_strategy["should_chunk"]

            # 分割戦略を表示
            duration_min = duration_seconds // 60
            if not chunk_strategy["should_chunk"]:
                st.info(f"📹 {duration_min}分の動画: 分割なしで解析します")
            else:
                chunk_min = chunk_strategy["chunk_duration_seconds"] // 60
                st.info(f"📹 {duration_min}分の動画: {chunk_strategy['num_chunks']}分割（各約{chunk_min}分）で解析します")

            # 長時間動画の注意表示
            if duration_seconds > 5400:
                st.warning("⚠️ 90分超の長時間動画です。解析に時間がかかる場合があります。API制限エラーが発生した場合は時間をおいて再試行してください。")

            # Whisper文字起こし実行（解析前）
            transcript = None
            transcript_result = None
            if use_whisper:
                with st.spinner("音声を文字起こし中..."):
                    try:
                        from src.whisper_transcriber import WhisperTranscriber
                        transcriber = WhisperTranscriber(api_key=openai_key)
                        transcript_result = transcriber.transcribe_video(str(temp_path))
                        transcript = transcript_result.get("text", "")

                        # 文字起こし結果を表示
                        with st.expander("文字起こし結果", expanded=False):
                            st.text(transcript)
                            if transcript_result.get("segments"):
                                st.caption(f"{len(transcript_result['segments'])}個のセグメントを検出")
                    except Exception as e:
                        st.warning(f"文字起こしに失敗しました（動画解析は続行します）: {str(e)}")
                        transcript = None
                        transcript_result = None

            with st.spinner("動画を解析中... これには数分かかることがあります"):
                # リアルタイムログ表示エリア
                log_container = st.expander("処理ログ（リアルタイム）", expanded=True)
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
                        from src.chunked_analyzer import ChunkedVideoAnalyzer
                        from src.chunk_integrator import ChunkIntegrator

                        # 進捗表示
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        progress_bar.progress(10)

                        # スマートチャンク分割
                        num_chunks = chunk_strategy["num_chunks"]
                        chunk_dur = chunk_strategy["chunk_duration_seconds"]
                        status_text.text(f"動画を{num_chunks}分割（各約{chunk_dur // 60}分）に分割中...")
                        chunker = VideoChunker(chunk_duration_seconds=chunk_dur)
                        chunks = chunker.create_chunks(str(temp_path), duration_seconds, split_physically=True)

                        progress_bar.progress(20)

                        # チャンク解析（APIキーは.envから自動読み込み）
                        status_text.text(f"{len(chunks)}個のチャンクを解析中...")
                        analyzer = ChunkedVideoAnalyzer(model=model, log_callback=log_callback)

                        try:
                            chunk_results = analyzer.analyze_chunks(
                                chunks, parallel=use_parallel,
                                full_transcript=transcript_result,
                                knowledge_text=knowledge_text
                            )

                            progress_bar.progress(80)

                            # デバッグ: チャンク結果のステータスを確認
                            log_callback("=== Chunk Results Summary ===")
                            for i, cr in enumerate(chunk_results):
                                status = cr.get("status", "unknown")
                                error_code = cr.get("error_code", "N/A")
                                has_eval = "evaluation" in cr
                                log_callback(f"Chunk {i}: status={status}, error_code={error_code}, has_evaluation={has_eval}")
                                if status == "error":
                                    log_callback(f"  Error: {cr.get('error_message', 'No error message')}")

                            # 統合
                            status_text.text("結果を統合中...")
                            integrator = ChunkIntegrator()
                            result = integrator.integrate_chunks(chunk_results)

                            progress_bar.progress(100)
                            status_text.text("✅ 解析完了!")

                            # チャンク解析結果を保存（詳細表示用）
                            st.session_state['chunk_results'] = chunk_results

                        finally:
                            # チャンク分割ファイルをクリーンアップ
                            status_text.text("分割ファイルを削除中...")
                            chunker.cleanup()
                            st.info("分割された動画ファイルを削除しました")

                        # デバッグ: チャンク結果の詳細を表示
                        with st.expander("🔍 デバッグ: チャンク処理結果の詳細"):
                            for idx, chunk_res in enumerate(chunk_results):
                                st.subheader(f"Chunk {idx} 処理結果")
                                st.json(chunk_res)

                    else:
                        # 通常の解析を使用
                        from src.analyzer import VideoAnalyzer

                        # 解析実行
                        analyzer = VideoAnalyzer(api_key=api_key_1, model=model, log_callback=log_callback)
                        result = analyzer.analyze(str(temp_path), transcript=transcript, knowledge_text=knowledge_text)

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

                    # 行動メトリクス
                    metrics = result.get("behavioral_metrics")
                    if metrics:
                        st.header("行動メトリクス")
                        metrics_df = pd.DataFrame([
                            {"指標": "アイコンタクトの質", "評価": metrics.get("eye_contact_quality", "-")},
                            {"指標": "ジェスチャーの自然さ", "評価": metrics.get("gesture_naturalness", "-")},
                            {"指標": "姿勢の安定性", "評価": metrics.get("posture_stability", "-")},
                            {"指標": "発話の流暢さ", "評価": metrics.get("speech_fluency", "-")},
                            {"指標": "フィラーの頻度", "評価": metrics.get("filler_frequency", "-")},
                            {"指標": "応答速度", "評価": metrics.get("response_speed", "-")},
                            {"指標": "言語-非言語の一致度", "評価": metrics.get("verbal_nonverbal_consistency", "-")},
                        ])
                        st.table(metrics_df)

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
