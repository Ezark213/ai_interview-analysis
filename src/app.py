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
    page_icon="AI",
    layout="wide"
)

# カスタムCSS注入
st.markdown("""
<style>
    /* メインコンテンツの余白調整 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* ヘッダーのフォント調整 */
    h1 {
        color: #1B3A5C;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    h2 {
        color: #1E293B;
        font-weight: 600;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
    }

    /* サイドバーのスタイル */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2 {
        border-bottom: none;
    }

    /* メトリクスカードのスタイル */
    [data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
    }

    /* ボタンのスタイル */
    .stButton > button[kind="primary"] {
        background-color: #1B3A5C;
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #264D73;
    }

    /* タブのスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
    }

    /* テーブルのスタイル */
    .stDataFrame {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
    }

    /* フッターのスタイル */
    .footer-text {
        color: #94A3B8;
        font-size: 0.85rem;
        text-align: center;
        padding: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# タイトル
st.title("AI面談動画解析システム")
st.markdown("面談動画の行動心理学的リスク評価を実施します")

# === APIキー読み込み ===
from src.config import load_api_keys, get_key_source
api_key_1, api_key_2, openai_key = load_api_keys()

# === サイドバー（スリム化: 実行時設定 + コンパクトステータス） ===
with st.sidebar:
    st.header("解析設定")

    model = st.selectbox(
        "使用モデル",
        ["gemini-2.5-flash", "gemini-1.5-pro"],
        help="gemini-2.5-flashが推奨（低コスト・高速）"
    )

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

    # コンパクトステータス表示
    st.subheader("ステータス")
    gemini_status = "設定済み" if api_key_1 else "未設定"
    openai_status = "設定済み" if openai_key else "未設定"
    whisper_status = "ON" if st.session_state.get("use_whisper", False) else "OFF"

    from src.knowledge_loader import list_presets, load_combined_knowledge
    preset_id = st.session_state.get("selected_preset")
    if preset_id:
        presets = list_presets()
        preset_name = next((p["name"] for p in presets if p["id"] == preset_id), "デフォルト")
    else:
        preset_name = "デフォルト"

    st.markdown(f"""
| 項目 | 状態 |
|------|------|
| Gemini API | {'✅ ' + gemini_status if api_key_1 else '❌ ' + gemini_status} |
| OpenAI API | {'✅ ' + openai_status if openai_key else '➖ ' + openai_status} |
| Whisper | {whisper_status} |
| 評価基準 | {preset_name} |
""")


# ===== メインエリア: 3タブ構造 =====
tab_single, tab_batch, tab_settings = st.tabs(["単一動画解析", "バッチ処理", "設定"])


# ==========================================
# タブ3: 設定
# ==========================================
with tab_settings:
    st.header("設定")

    # --- API設定 ---
    st.subheader("API設定")

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
        st.success("APIキーを保存しました（このセッション中のみ有効）")
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

    st.divider()

    # --- 評価基準 ---
    st.subheader("評価基準")

    presets = list_presets()
    preset_options = {"デフォルト": None}
    for p in presets:
        preset_options[p["name"]] = p["id"]

    # 現在選択中のプリセットのインデックスを取得
    current_preset = st.session_state.get("selected_preset")
    preset_keys = list(preset_options.keys())
    current_idx = 0
    for i, k in enumerate(preset_keys):
        if preset_options[k] == current_preset:
            current_idx = i
            break

    selected_preset_name = st.selectbox(
        "評価基準プリセット",
        preset_keys,
        index=current_idx,
        help="面接の種類に合った評価基準を選択",
        key="settings_preset_select",
    )
    st.session_state["selected_preset"] = preset_options[selected_preset_name]

    # カスタムナレッジベースのアップロード
    uploaded_kb = st.file_uploader(
        "カスタム評価基準（.md）をアップロード（オプション）",
        type=["md"],
        help="独自の評価基準をMarkdown形式でアップロードできます",
        key="settings_kb_uploader",
    )
    # アップロード即時にsession_stateに保存（タブ切り替え対策）
    if uploaded_kb is not None:
        content = uploaded_kb.read().decode("utf-8")
        st.session_state["custom_knowledge"] = content
        st.success(f"カスタム評価基準を読み込みました: {uploaded_kb.name}")
    if st.session_state.get("custom_knowledge"):
        st.caption("カスタム評価基準が設定されています")
        if st.button("カスタム評価基準をクリア", key="clear_custom_kb"):
            st.session_state["custom_knowledge"] = None
            st.rerun()

    st.divider()

    # --- 使用ガイド ---
    with st.expander("使用ガイド"):
        st.markdown("""
        ### 推奨される動画
        - **時間**: 10-30分程度
        - **形式**: MP4（H.264エンコード）
        - **解像度**: 720p以上
        - **音質**: クリアな音声

        ### 評価のポイント（6カテゴリ）
        1. **コミュニケーション**: 言語的明瞭さ、傾聴力
        2. **ストレス耐性**: 困難な質問への対応
        3. **信頼性**: エピソードの具体性・一貫性
        4. **チームワーク**: 協働経験・対人関係
        5. **信頼度**: 発言内容の信頼性（CBCA/RM/VA）
        6. **職業的態度**: 敬語・マナー・貢献志向

        ### 注意事項
        - 候補者の同意を必ず取得してください
        - AIの評価は参考情報として扱ってください
        - 最終判断は人間が行ってください
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
    selected_preset = st.session_state.get("selected_preset")
    custom_content = st.session_state.get("custom_knowledge")

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
                # ナレッジベースの読み込み
                try:
                    knowledge_text = load_combined_knowledge(
                        preset_id=selected_preset,
                        custom_content=custom_content
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
                use_chunk_analysis = use_chunking and chunk_strategy["should_chunk"]

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
                                    chunks, parallel=use_parallel,
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

                        # JSON出力
                        with st.expander("JSON出力"):
                            st.json(result)

                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            json_str = json.dumps(result, ensure_ascii=False, indent=2)
                            st.download_button(
                                label="JSONをダウンロード",
                                data=json_str,
                                file_name=f"analysis_result_{timestamp}.json",
                                mime="application/json"
                            )

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

    # 設定タブから値を読み取る
    selected_preset = st.session_state.get("selected_preset")
    custom_content = st.session_state.get("custom_knowledge")

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
                    # ナレッジベース読み込み
                    try:
                        knowledge_text = load_combined_knowledge(
                            preset_id=selected_preset,
                            custom_content=custom_content
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

                    def make_analyzer():
                        return VideoAnalyzer(api_key=api_key_1, model=model, log_callback=batch_log_callback)

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

        col1, col2 = st.columns(2)
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


# フッター
st.divider()
st.markdown("""
<div class="footer-text">
    AI面談動画解析システム v1.0<br>
    本システムの評価結果は参考情報です。最終的な判断は必ず人間が行ってください。<br>
    Powered by Google Gemini API
</div>
""", unsafe_allow_html=True)
