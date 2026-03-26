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

# UIコンポーネントのインポート
from src.components.styles import inject_custom_css

# ページ設定
st.set_page_config(
    page_title="AI面談動画解析システム",
    page_icon="AI",
    layout="wide"
)

# カスタムCSS注入（企業向けSaaS風デザイン）
custom_css = inject_custom_css()

# Try both methods for maximum compatibility
st.markdown(custom_css, unsafe_allow_html=True)

# Also try using components.html if available
try:
    import streamlit.components.v1 as components
    components.html(custom_css, height=0)
except:
    pass

# タイトル
st.title("AI面談動画解析システム")
st.markdown("面談動画の行動心理学的リスク評価を実施します")

# === APIキー読み込み ===
from src.config import load_api_keys, get_key_source
api_key_1, api_key_2, openai_key = load_api_keys()

from src.knowledge_loader import load_combined_knowledge, load_reference_docs, save_reference_doc, load_preset

# モデル選択（session_stateで管理、設定タブで変更可能）
if "model" not in st.session_state:
    st.session_state["model"] = "gemini-2.5-flash"
model = st.session_state["model"]


# ===== メインエリア: 4タブ構造 =====
tab_single, tab_batch, tab_knowledge, tab_guide, tab_settings, tab_feedback = st.tabs(["単一動画解析", "バッチ処理", "ナレッジベース", "使い方", "設定", "フィードバック"])


# ==========================================
# タブ3: ナレッジベース
# ==========================================
with tab_knowledge:
    st.header("ナレッジベース")
    st.markdown("AIの評価基準と参考資料を管理します。")

    # --- 評価基準 ---
    st.subheader("評価基準（AIプロンプトに投入）")
    st.info("SES面談向け評価基準が自動的に適用されます（客先常駐適応力・早期離職リスク等を重視）")

    with st.expander("評価基準の内容を確認"):
        try:
            criteria_text = load_preset("ses_interview")
            st.markdown(criteria_text)
        except Exception as e:
            st.error(f"評価基準の読み込みに失敗: {e}")

    st.divider()

    # --- 参考資料 ---
    st.subheader("参考資料（人間閲覧用）")
    st.caption("理論的背景や学術的根拠などの参考資料です。AIプロンプトには投入されません。")

    ref_docs = load_reference_docs()
    if ref_docs:
        for doc in ref_docs:
            with st.expander(f"{doc['filename']}"):
                st.markdown(doc["content"])
    else:
        st.info("参考資料はまだ登録されていません。")

    # 参考資料アップロード
    uploaded_ref = st.file_uploader(
        "参考資料をアップロード（Markdownファイル）",
        type=["md"],
        help="Markdown形式のファイルを参考資料として追加します",
        key="ref_upload",
    )
    if uploaded_ref is not None:
        ref_content = uploaded_ref.read().decode("utf-8")
        if st.button("参考資料を保存", key="save_ref"):
            try:
                saved_path = save_reference_doc(uploaded_ref.name, ref_content)
                st.success(f"参考資料を保存しました: {uploaded_ref.name}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    st.divider()

    # --- 評価のポイント ---
    st.subheader("評価のポイント（6カテゴリ）")
    st.markdown("""
| カテゴリ | 概要 |
|---------|------|
| コミュニケーション | 言語的明瞭さ、傾聴力、構造化された説明 |
| ストレス耐性 | 困難な質問への対応、感情制御、回復力 |
| 信頼性 | エピソードの具体性、一貫性、検証可能性 |
| チームワーク | 協働経験、対人関係、貢献姿勢 |
| 信頼度 | CBCA/RM/VAベースの発言内容信頼性 |
| 職業的態度 | 敬語、マナー、報連相、貢献志向 |
""")


# ==========================================
# タブ4: 設定
# ==========================================
with tab_settings:
    st.header("設定")

    # --- モデル選択 ---
    st.subheader("使用モデル")
    selected_model = st.selectbox(
        "解析に使用するモデル",
        ["gemini-2.5-flash", "gemini-1.5-pro"],
        index=0 if st.session_state.get("model") == "gemini-2.5-flash" else 1,
        help="gemini-2.5-flashが推奨（低コスト・高速）",
        key="settings_model",
    )
    if selected_model != st.session_state.get("model"):
        st.session_state["model"] = selected_model
        model = selected_model

    st.divider()

    # --- API設定 ---
    st.subheader("API設定")
    st.caption(".envファイルから自動読み込み済みです。手動入力で上書きできます。")

    # .env / Secrets からの読み込み状態を表示
    src_key1 = get_key_source("gemini_api_key_1")
    src_key2 = get_key_source("gemini_api_key_2")
    src_openai = get_key_source("openai_api_key")

    def _source_label(src: str) -> str:
        if src == "env":
            return "（.envから読み込み済み）"
        elif src == "secrets":
            return "（Streamlit Secretsから読み込み済み）"
        elif src == "ui":
            return "（UI入力済み）"
        return ""

    gemini_key1_input = st.text_input(
        f"Gemini APIキー 1（必須）{_source_label(src_key1)}",
        value=st.session_state.get("gemini_api_key_1", ""),
        type="password",
        placeholder=".envに設定済み" if src_key1 == "env" else "APIキーを入力",
        key="settings_gemini_key1",
    )

    gemini_key2_input = st.text_input(
        f"Gemini APIキー 2（オプション: 自動切り替え用）{_source_label(src_key2)}",
        value=st.session_state.get("gemini_api_key_2", ""),
        type="password",
        placeholder=".envに設定済み" if src_key2 == "env" else "APIキーを入力（省略可）",
        key="settings_gemini_key2",
    )

    openai_key_input = st.text_input(
        f"OpenAI APIキー（オプション: Whisper用）{_source_label(src_openai)}",
        value=st.session_state.get("openai_api_key", ""),
        type="password",
        placeholder=".envに設定済み" if src_openai == "env" else "APIキーを入力（省略可）",
        key="settings_openai_key",
    )

    if st.button("APIキーを保存", type="primary", key="save_api_keys"):
        st.session_state["gemini_api_key_1"] = gemini_key1_input
        st.session_state["gemini_api_key_2"] = gemini_key2_input
        st.session_state["openai_api_key"] = openai_key_input
        st.success("APIキーを保存しました（このセッション中のみ有効）。.envの値より優先されます。")
        st.rerun()

    # 接続状態表示
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        if api_key_1:
            st.success("Gemini API 1: 設定済み")
        else:
            st.error("Gemini API 1: 未設定")
    with col_s2:
        if api_key_2:
            st.success("Gemini API 2: 設定済み")
        else:
            st.info("Gemini API 2: 未設定（オプション）")
    with col_s3:
        if openai_key:
            st.success("OpenAI API: 設定済み")
        else:
            st.info("OpenAI API: 未設定（オプション）")

    st.divider()

    # --- Whisper文字起こし ---
    st.subheader("Whisper文字起こし")
    if openai_key:
        use_whisper = st.checkbox(
            "Whisper文字起こしを使用",
            value=st.session_state.get("use_whisper", False),
            help="OpenAI Whisper APIで音声を文字起こしし、発言内容と非言語行動を照合します（有料: $0.006/分）",
            key="settings_use_whisper",
        )
        st.session_state["use_whisper"] = use_whisper
        if use_whisper:
            st.caption("Whisper APIの利用には費用が発生します（約$0.006/分）")
    else:
        st.checkbox(
            "Whisper文字起こしを使用",
            value=False,
            disabled=True,
            help="OpenAI APIキーを設定するとWhisper文字起こし機能が使えます",
            key="settings_use_whisper_disabled",
        )
        st.session_state["use_whisper"] = False
        st.info("OpenAI APIキーを設定するとWhisper文字起こし機能が使えます")



# ==========================================
# タブ4: 使い方
# ==========================================
with tab_guide:
    st.header("使い方ガイド")

    st.subheader("推奨される動画")
    st.markdown("""
| 項目 | 推奨値 |
|------|--------|
| 時間 | 10〜30分程度 |
| 形式 | MP4（H.264エンコード） |
| 解像度 | 720p以上 |
| 音質 | クリアな音声 |
""")

    st.divider()

    st.subheader("基本的な使い方")
    st.markdown("""
1. **設定タブ** でAPIキーを入力（初回のみ）
2. **単一動画解析タブ** で動画をアップロード → 「解析開始」ボタン
3. 解析完了後、結果を画面で確認 or **HTMLレポートをダウンロード**
4. 複数動画をまとめて解析したい場合は **バッチ処理タブ** を使用
""")

    st.divider()

    st.subheader("解析結果の見方")
    st.markdown("""
- **総合スコア（0〜100）**: 高いほど良い評価。85+は非常に良好、55未満は要注意
- **リスクレベル**: 低・中・高の3段階
- **6カテゴリ評価**: 各カテゴリ0〜100点で個別評価
- **リスクシグナル**: 懸念事項がある場合に表示
- **ポジティブシグナル**: 好印象な点がある場合に表示
""")

    st.divider()

    st.subheader("注意事項")
    st.warning("""
- 候補者の同意を必ず取得してください
- AIの評価は **参考情報** として扱ってください
- 最終判断は必ず **人間** が行ってください
- 1つの動画の評価だけで採用判断をしないでください
""")


# ==========================================
# タブ1: 単一動画解析（既存機能）
# ==========================================
with tab_single:
    # APIキー未設定時のバナー
    if not api_key_1:
        st.warning("APIキーが設定されていません。「設定」タブからAPIキーを入力してください。")

    uploaded_file = st.file_uploader(
        "動画ファイルを選択",
        type=["mp4", "mov", "avi", "webm"],
        help="対応形式: MP4, MOV, AVI, WebM（推奨: 30分以内）",
        key="single_uploader"
    )

    # 設定タブから値を読み取る
    use_whisper = st.session_state.get("use_whisper", False)

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
        from datetime import datetime
        import os as os_module
        file_ext = os_module.path.splitext(uploaded_file.name)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"uploaded_video_{timestamp}{file_ext}"
        temp_path = temp_dir / safe_filename

        # ファイル保存
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())

        # ファイルが正しく保存されたか確認
        import time
        time.sleep(0.5)
        if not temp_path.exists():
            st.error(f"ファイル保存に失敗しました: {temp_path}")
        else:
            file_size_mb = temp_path.stat().st_size / 1024 / 1024
            st.success(f"ファイルをアップロードしました: {uploaded_file.name} ({file_size_mb:.1f}MB)")

            if file_size_mb > 180:
                st.warning("ファイルサイズが大きいです（200MB上限に近い）。クラウド環境では処理に失敗する場合があります。")

        # 解析ボタン
        if st.button("解析開始", type="primary", use_container_width=True, key="single_analyze"):
            if not api_key_1:
                st.error("APIキーが設定されていません。「設定」タブからAPIキーを入力してください。")
            else:
                # ナレッジベースの読み込み（SES面談固定）
                try:
                    knowledge_text = load_combined_knowledge(
                        preset_id="ses_interview"
                    )
                except (ValueError, FileNotFoundError) as e:
                    st.error(f"ナレッジベースの読み込みに失敗: {e}")
                    knowledge_text = None

                # 動画の長さを取得してスマートチャンク分割戦略を決定
                from src.video_chunker import VideoChunker, get_video_duration, calculate_chunk_strategy

                try:
                    duration_seconds = get_video_duration(str(temp_path))
                except Exception as e:
                    st.warning(f"動画の長さを自動取得できませんでした。推定値を使用します。({str(e)})")
                    duration_seconds = 1800

                chunk_strategy = calculate_chunk_strategy(duration_seconds)
                use_chunk_analysis = chunk_strategy["should_chunk"]

                duration_min = duration_seconds // 60
                if not chunk_strategy["should_chunk"]:
                    st.info(f"{duration_min}分の動画: 分割なしで解析します")
                else:
                    chunk_min = chunk_strategy["chunk_duration_seconds"] // 60
                    st.info(f"{duration_min}分の動画: {chunk_strategy['num_chunks']}分割（各約{chunk_min}分）で解析します")

                if duration_seconds > 5400:
                    st.warning("90分超の長時間動画です。解析に時間がかかる場合があります。API制限エラーが発生した場合は時間をおいて再試行してください。")

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

                            with st.expander("文字起こし結果", expanded=False):
                                st.text(transcript)
                                if transcript_result.get("segments"):
                                    st.caption(f"{len(transcript_result['segments'])}個のセグメントを検出")
                        except Exception as e:
                            st.warning(f"文字起こしに失敗しました（動画解析は続行します）: {str(e)}")
                            transcript = None
                            transcript_result = None

                with st.spinner("動画を解析中... これには数分かかることがあります"):
                    log_container = st.expander("処理ログ（リアルタイム）", expanded=True)
                    log_text = log_container.empty()
                    log_messages = []

                    def log_callback(msg):
                        log_messages.append(msg)
                        display_logs = log_messages[-50:]
                        log_text.text("\n".join(display_logs))

                    try:
                        if use_chunk_analysis:
                            from src.chunked_analyzer import ChunkedVideoAnalyzer
                            from src.chunk_integrator import ChunkIntegrator

                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            progress_bar.progress(10)

                            num_chunks = chunk_strategy["num_chunks"]
                            chunk_dur = chunk_strategy["chunk_duration_seconds"]
                            status_text.text(f"動画を{num_chunks}分割（各約{chunk_dur // 60}分）に分割中...")
                            chunker = VideoChunker(chunk_duration_seconds=chunk_dur)
                            chunks = chunker.create_chunks(str(temp_path), duration_seconds, split_physically=True)

                            progress_bar.progress(20)

                            status_text.text(f"{len(chunks)}個のチャンクを解析中...")
                            analyzer = ChunkedVideoAnalyzer(model=model, log_callback=log_callback)

                            try:
                                chunk_results = analyzer.analyze_chunks(
                                    chunks, parallel=False,
                                    full_transcript=transcript_result,
                                    knowledge_text=knowledge_text
                                )

                                progress_bar.progress(80)

                                log_callback("=== Chunk Results Summary ===")
                                for i, cr in enumerate(chunk_results):
                                    status = cr.get("status", "unknown")
                                    error_code = cr.get("error_code", "N/A")
                                    has_eval = "evaluation" in cr
                                    log_callback(f"Chunk {i}: status={status}, error_code={error_code}, has_evaluation={has_eval}")
                                    if status == "error":
                                        log_callback(f"  Error: {cr.get('error_message', 'No error message')}")

                                status_text.text("結果を統合中...")
                                integrator = ChunkIntegrator()
                                result = integrator.integrate_chunks(chunk_results)

                                progress_bar.progress(100)
                                status_text.text("解析が完了しました")

                                st.session_state['chunk_results'] = chunk_results

                            finally:
                                status_text.text("分割ファイルを削除中...")
                                chunker.cleanup()
                                st.info("分割された動画ファイルを削除しました")

                            with st.expander("デバッグ: チャンク処理結果"):
                                for idx, chunk_res in enumerate(chunk_results):
                                    st.subheader(f"Chunk {idx} 処理結果")
                                    st.json(chunk_res)

                        else:
                            from src.analyzer import VideoAnalyzer

                            analyzer = VideoAnalyzer(api_key=api_key_1, model=model, log_callback=log_callback)
                            result = analyzer.analyze(str(temp_path), transcript=transcript, knowledge_text=knowledge_text)

                        st.success("解析が完了しました")

                        if result.get("overall_risk_score", 0) == 0:
                            st.warning("デバッグ情報: スコアが0です。結果の内容を確認してください。")
                            with st.expander("デバッグ: 解析結果の生データ"):
                                st.json(result)

                        # 総合評価
                        st.header("総合評価")
                        score = result.get("overall_risk_score", 0)
                        risk_level = result.get("risk_level", "不明")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("総合スコア", f"{score}/100", help="高いほど良い評価")
                        with col2:
                            if risk_level == "低":
                                st.success(f"リスクレベル: {risk_level}")
                            elif risk_level == "中":
                                st.warning(f"リスクレベル: {risk_level}")
                            else:
                                st.error(f"リスクレベル: {risk_level}")

                        # 詳細評価
                        st.header("詳細評価")
                        evaluation = result.get("evaluation", {})

                        # カテゴリ名の日本語マッピング
                        category_labels = {
                            "communication": "コミュニケーション",
                            "stress_tolerance": "ストレス耐性",
                            "reliability": "信頼性",
                            "teamwork": "チームワーク",
                            "credibility": "信頼度",
                            "professional_demeanor": "職業的態度",
                        }

                        if evaluation:
                            tab_names = [category_labels.get(k, k) for k in evaluation.keys()]
                            eval_tabs = st.tabs(tab_names)
                            for eval_tab, (category, data) in zip(eval_tabs, evaluation.items()):
                                with eval_tab:
                                    label = category_labels.get(category, category)
                                    st.subheader(f"{label}")
                                    score_val = data.get("score", 0)
                                    st.progress(score_val / 100)
                                    st.metric("スコア", f"{score_val}/100")

                                    st.write("**観察事項:**")
                                    observations = data.get("observations", [])
                                    for obs in observations:
                                        st.write(f"- {obs}")

                                    confidence = data.get("confidence", "不明")
                                    st.write(f"**確信度:** {confidence}")

                        # リスクシグナル
                        st.header("リスクシグナル")
                        red_flags = result.get("red_flags", [])
                        if red_flags:
                            for flag in red_flags:
                                st.warning(f"- {flag}")
                        else:
                            st.success("重大なリスクシグナルは検出されませんでした")

                        # ポジティブシグナル
                        st.header("ポジティブシグナル")
                        positive_signals = result.get("positive_signals", [])
                        if positive_signals:
                            for signal in positive_signals:
                                st.success(f"- {signal}")
                        else:
                            st.info("特筆すべきポジティブシグナルはありませんでした")

                        # 推奨事項
                        st.header("推奨事項")
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

                        # チャンク別詳細
                        if 'chunk_results' in st.session_state and st.session_state['chunk_results']:
                            st.header("時系列分析")
                            chunk_results = st.session_state['chunk_results']

                            if "chunk_analysis" in result:
                                consistency_issues = result["chunk_analysis"].get("consistency_issues", [])
                                if consistency_issues:
                                    st.warning("チャンク間の一貫性に関する注意点:")
                                    for issue in consistency_issues:
                                        st.write(f"- {issue}")

                                patterns = result["chunk_analysis"].get("temporal_patterns", {})
                                if patterns.get("score_trend"):
                                    trend = patterns["score_trend"]
                                    if trend == "improving":
                                        st.success("スコアが面談の進行とともに向上しています")
                                    elif trend == "declining":
                                        st.warning("スコアが面談の進行とともに低下しています")
                                    else:
                                        st.info("スコアは安定しています")

                            with st.expander("チャンク別の詳細評価"):
                                for chunk_result in chunk_results:
                                    chunk_id = chunk_result.get("chunk_id", 0)
                                    time_range = chunk_result.get("chunk_time_range", {})
                                    start_min = time_range.get("start", 0) // 60
                                    end_min = time_range.get("end", 0) // 60

                                    st.subheader(f"チャンク #{chunk_id + 1} ({start_min}-{end_min}分)")

                                    if "error" in chunk_result:
                                        st.error(f"エラー: {chunk_result['error']}")
                                        continue

                                    score = chunk_result.get("overall_risk_score", 0)
                                    st.metric("スコア", f"{score}/100")

                                    eval_data = chunk_result.get("evaluation", {})
                                    if eval_data:
                                        num_cols = min(len(eval_data), 6)
                                        cols = st.columns(num_cols)
                                        for idx, (cat_key, cat_data) in enumerate(eval_data.items()):
                                            cat_score = cat_data.get("score", 0)
                                            cat_label = category_labels.get(cat_key, cat_key)
                                            with cols[idx % num_cols]:
                                                st.metric(cat_label, f"{cat_score}")

                                    st.divider()

                        # レポート出力
                        st.header("レポート出力")
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            from src.report_generator import generate_html_report
                            html_report = generate_html_report(
                                result,
                                filename=uploaded_file.name,
                                analysis_date=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
                            )
                            st.download_button(
                                label="HTMLレポートをダウンロード",
                                data=html_report.encode("utf-8"),
                                file_name=f"analysis_report_{timestamp}.html",
                                mime="text/html",
                                key="single_html_download",
                            )
                        with col_dl2:
                            json_str = json.dumps(result, ensure_ascii=False, indent=2)
                            st.download_button(
                                label="JSONをダウンロード",
                                data=json_str,
                                file_name=f"analysis_result_{timestamp}.json",
                                mime="application/json",
                                key="single_json_download",
                            )

                        with st.expander("JSON出力"):
                            st.json(result)

                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")
                        st.exception(e)

                    finally:
                        if temp_path.exists():
                            temp_path.unlink()
                            st.info("一時ファイルを削除しました")

    else:
        st.info("動画ファイルをアップロードして解析を開始してください")


# ==========================================
# タブ2: バッチ処理（IT-11新規）
# ==========================================
with tab_batch:
    # APIキー未設定時のバナー
    if not api_key_1:
        st.warning("APIキーが設定されていません。「設定」タブからAPIキーを入力してください。")

    st.header("バッチ処理")
    st.info("最大10件の動画を一括で解析します。API制限への対応として、動画間に30秒の待機を設けています。")

    uploaded_files = st.file_uploader(
        "動画ファイルを選択（複数可）",
        type=["mp4", "mov", "avi", "webm"],
        accept_multiple_files=True,
        help="最大10ファイル。対応形式: MP4, MOV, AVI, WebM",
        key="batch_uploader"
    )

    if uploaded_files:
        if len(uploaded_files) > 10:
            st.error("一度に処理できるのは最大10ファイルです。10件以下に絞ってください。")
        else:
            st.write(f"**{len(uploaded_files)}件の動画が選択されています：**")
            for f in uploaded_files:
                st.write(f"  - {f.name} ({f.size / 1024 / 1024:.1f}MB)")

            if st.button("バッチ解析開始", type="primary", use_container_width=True, key="batch_analyze"):
                if not api_key_1:
                    st.error("APIキーが設定されていません。")
                else:
                    # ナレッジベース読み込み（SES面談固定）
                    try:
                        knowledge_text = load_combined_knowledge(
                            preset_id="ses_interview"
                        )
                    except (ValueError, FileNotFoundError) as e:
                        st.error(f"ナレッジベースの読み込みに失敗: {e}")
                        knowledge_text = None

                    # 一時保存
                    temp_dir = Path(__file__).parent.parent / "temp"
                    temp_dir.mkdir(exist_ok=True)

                    video_paths = []
                    video_names = []
                    import os as os_module

                    for uf in uploaded_files:
                        file_ext = os_module.path.splitext(uf.name)[1]
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        safe_name = f"batch_{ts}{file_ext}"
                        p = temp_dir / safe_name
                        with open(p, "wb") as fw:
                            fw.write(uf.read())
                        video_paths.append(str(p))
                        video_names.append(uf.name)

                    # バッチ処理実行
                    from src.batch_processor import BatchProcessor
                    from src.analyzer import VideoAnalyzer

                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    log_container = st.expander("処理ログ", expanded=True)
                    log_text = log_container.empty()
                    log_messages = []

                    def batch_log_callback(msg):
                        log_messages.append(msg)
                        log_text.text("\n".join(log_messages[-50:]))

                    # APIキーローテーション: 複数キーを交互に使用
                    api_keys = [k for k in [api_key_1, api_key_2] if k]
                    _key_counter = [0]  # mutableでクロージャ内からインクリメント可能に

                    def make_analyzer():
                        key = api_keys[_key_counter[0] % len(api_keys)]
                        _key_counter[0] += 1
                        batch_log_callback(f"[APIキー] キー{(_key_counter[0] - 1) % len(api_keys) + 1}/{len(api_keys)}を使用")
                        return VideoAnalyzer(api_key=key, model=model, log_callback=batch_log_callback)

                    processor = BatchProcessor(
                        analyzer_factory=make_analyzer,
                        log_callback=batch_log_callback
                    )

                    total = len(video_paths)
                    batch_log_callback(f"=== バッチ処理開始: {total}件 ===")

                    try:
                        results = processor.process_batch(
                            video_paths=video_paths,
                            video_names=video_names,
                            wait_seconds=30,
                            knowledge_text=knowledge_text
                        )

                        progress_bar.progress(100)
                        status_text.text("バッチ処理が完了しました")

                        st.session_state['batch_results'] = results

                    except Exception as e:
                        st.error(f"バッチ処理中にエラーが発生しました: {str(e)}")
                        st.exception(e)

                    finally:
                        # 一時ファイル削除
                        for vp in video_paths:
                            try:
                                Path(vp).unlink(missing_ok=True)
                            except Exception:
                                pass

    # 結果表示エリア
    if 'batch_results' in st.session_state and st.session_state['batch_results']:
        results = st.session_state['batch_results']

        # サマリー
        summary = BatchProcessor.summarize_results(results)
        st.header("結果サマリー")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("処理件数", f"{summary['total']}件")
        with col2:
            st.metric("成功", f"{summary['success_count']}件")
        with col3:
            st.metric("失敗", f"{summary['error_count']}件")
        with col4:
            avg = summary['average_score']
            st.metric("平均スコア", f"{avg}/100" if avg is not None else "-")

        # 比較テーブル
        st.header("候補者比較")
        comparison_rows = []
        for r in results:
            evaluation = r.get("evaluation") or {}
            row = {
                "ファイル名": r.get("filename", ""),
                "ステータス": r.get("status", ""),
                "総合スコア": r.get("overall_risk_score", "-"),
                "リスクレベル": r.get("risk_level", "-"),
                "コミュニケーション": evaluation.get("communication", {}).get("score", "-") if isinstance(evaluation, dict) else "-",
                "ストレス耐性": evaluation.get("stress_tolerance", {}).get("score", "-") if isinstance(evaluation, dict) else "-",
                "信頼性": evaluation.get("reliability", {}).get("score", "-") if isinstance(evaluation, dict) else "-",
                "チームワーク": evaluation.get("teamwork", {}).get("score", "-") if isinstance(evaluation, dict) else "-",
                "信頼度": evaluation.get("credibility", {}).get("score", "-") if isinstance(evaluation, dict) else "-",
                "職業的態度": evaluation.get("professional_demeanor", {}).get("score", "-") if isinstance(evaluation, dict) else "-",
            }
            comparison_rows.append(row)

        comparison_df = pd.DataFrame(comparison_rows)
        st.dataframe(comparison_df, use_container_width=True)

        # エクスポートボタン
        st.header("エクスポート")
        # BatchProcessorインスタンスが必要（エクスポート用）
        export_processor = BatchProcessor(analyzer_factory=lambda: None)

        col1, col2, col3 = st.columns(3)
        with col1:
            csv_data = export_processor.export_to_csv(results)
            st.download_button(
                "CSVダウンロード",
                csv_data,
                "batch_results.csv",
                "text/csv",
                key="batch_csv_download"
            )
        with col2:
            json_data = export_processor.export_to_json(results)
            st.download_button(
                "JSONダウンロード",
                json_data,
                "batch_results.json",
                "application/json",
                key="batch_json_download"
            )
        with col3:
            # HTML個別レポート（ZIP）
            import zipfile
            from src.report_generator import generate_html_report

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for r in results:
                    if r.get("status") != "success":
                        continue
                    fname = r.get("filename", "unknown")
                    safe_name = fname.rsplit(".", 1)[0] if "." in fname else fname
                    html_content = generate_html_report(
                        r,
                        filename=fname,
                        analysis_date=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
                    )
                    zf.writestr(f"{safe_name}_report.html", html_content.encode("utf-8"))
            zip_buffer.seek(0)
            st.download_button(
                "HTMLレポート（ZIP）",
                zip_buffer.getvalue(),
                "batch_html_reports.zip",
                "application/zip",
                key="batch_html_download"
            )

        # 各動画の詳細（折りたたみ）
        st.header("個別結果")
        for r in results:
            with st.expander(f"{r.get('filename', '不明')} - {r.get('status', '')}"):
                if r.get("status") == "error":
                    st.error(f"エラー: {r.get('error', '不明')}")
                else:
                    st.json(r)

        # バッチ結果クリアボタン
        if st.button("結果をクリア", key="clear_batch"):
            del st.session_state['batch_results']
            st.rerun()

    elif not uploaded_files:
        st.info("複数の動画ファイルをアップロードしてバッチ解析を開始してください")


# ==========================================
# タブ5: フィードバック
# ==========================================
with tab_feedback:
    st.header("フィードバック")
    st.markdown("ご意見・ご要望・バグ報告をお送りください。GitHub Issueとして管理され、メールでも通知されます。")

    with st.form("feedback_form", clear_on_submit=True):
        fb_name = st.text_input("お名前（任意）", placeholder="匿名でもOK")
        fb_category = st.selectbox(
            "カテゴリ",
            ["バグ報告", "機能リクエスト", "UI改善", "評価精度", "その他"],
        )
        fb_title = st.text_input("タイトル", placeholder="例: レーダーチャートが表示されない")
        fb_body = st.text_area(
            "詳細",
            height=150,
            placeholder="具体的な状況、再現手順、改善案などをお書きください",
        )
        fb_submitted = st.form_submit_button("送信", type="primary", use_container_width=True)

    if fb_submitted:
        if not fb_title.strip():
            st.error("タイトルを入力してください。")
        else:
            from src.feedback import submit_feedback

            # GitHub Token取得
            gh_token = os.getenv("GITHUB_TOKEN", "")
            if not gh_token:
                try:
                    gh_token = st.secrets.get("GITHUB_TOKEN", "")
                except Exception:
                    pass

            # SMTP設定取得
            smtp_config = {}
            smtp_host = os.getenv("SMTP_HOST", "")
            if not smtp_host:
                try:
                    smtp_host = st.secrets.get("SMTP_HOST", "")
                except Exception:
                    pass
            if smtp_host:
                smtp_config = {
                    "host": smtp_host,
                    "port": os.getenv("SMTP_PORT", "") or st.secrets.get("SMTP_PORT", "587"),
                    "user": os.getenv("SMTP_USER", "") or st.secrets.get("SMTP_USER", ""),
                    "password": os.getenv("SMTP_PASSWORD", "") or st.secrets.get("SMTP_PASSWORD", ""),
                    "to_email": os.getenv("FEEDBACK_EMAIL", "") or st.secrets.get("FEEDBACK_EMAIL", "yiwao@arma-as.co.jp"),
                }

            if not gh_token and not smtp_config:
                st.warning("フィードバック送信の設定がされていません（GITHUB_TOKEN または SMTP設定が必要です）。管理者に連絡してください。")
            else:
                with st.spinner("送信中..."):
                    result = submit_feedback(
                        title=fb_title.strip(),
                        body=fb_body.strip(),
                        category=fb_category,
                        sender_name=fb_name.strip() or "匿名",
                        github_token=gh_token,
                        smtp_config=smtp_config if smtp_config else None,
                    )

                # 結果表示
                gh = result.get("github")
                em = result.get("email")

                if gh and gh.get("success"):
                    st.success(f"GitHub Issueを作成しました: [#{gh['number']}]({gh['url']})")
                elif gh and not gh.get("success"):
                    st.warning(f"GitHub Issue作成に失敗: {gh.get('error', '不明')}")

                if em and em.get("success"):
                    st.success("メール通知を送信しました。")
                elif em and not em.get("success"):
                    st.warning(f"メール送信に失敗: {em.get('error', '不明')}")

                if (gh and gh.get("success")) or (em and em.get("success")):
                    st.balloons()
                    st.info("フィードバックありがとうございます！")


# フッター
st.divider()
st.markdown("""
<div class="footer-text">
    AI面談動画解析システム v1.1<br>
    本システムの評価結果は参考情報です。最終的な判断は必ず人間が行ってください。<br>
    Powered by Google Gemini API
</div>
""", unsafe_allow_html=True)
