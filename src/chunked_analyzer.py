"""チャンク単位での動画解析モジュール"""
import json
import sys
import time
import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 内部モジュール
from .video_chunker import ChunkInfo
from .knowledge_loader import load_knowledge_base
from .prompt_builder import build_prompt
from .response_parser import parse_response

# Gemini SDK
try:
    from google import genai
except ImportError:
    genai = None


# Streamlit環境でのprint安全化
def safe_print(msg, log_callback=None):
    """Streamlit環境でもエラーにならないprint関数"""
    try:
        print(msg)
    except (ValueError, OSError):
        # stdout/stderrがクローズされている場合は無視
        pass

    # ログコールバックがあれば呼び出し
    if log_callback:
        try:
            log_callback(msg)
        except:
            pass


# エラーコード定義
class AnalysisError:
    """解析エラーコード"""
    SUCCESS = "SUCCESS"
    ERR_API_KEY_INVALID = "ERR_001_API_KEY_INVALID"
    ERR_FILE_NOT_FOUND = "ERR_002_FILE_NOT_FOUND"
    ERR_FILE_TOO_LARGE = "ERR_003_FILE_TOO_LARGE"
    ERR_FILE_UPLOAD_FAILED = "ERR_004_FILE_UPLOAD_FAILED"
    ERR_FILE_PROCESSING_FAILED = "ERR_005_FILE_PROCESSING_FAILED"
    ERR_API_QUOTA_EXCEEDED = "ERR_006_API_QUOTA_EXCEEDED"
    ERR_API_RATE_LIMIT = "ERR_007_API_RATE_LIMIT"
    ERR_UNSUPPORTED_FORMAT = "ERR_008_UNSUPPORTED_FORMAT"
    ERR_GENERATE_CONTENT_FAILED = "ERR_009_GENERATE_CONTENT_FAILED"
    ERR_RESPONSE_PARSE_FAILED = "ERR_010_RESPONSE_PARSE_FAILED"
    ERR_UNKNOWN = "ERR_999_UNKNOWN"

    # エラーメッセージマッピング
    MESSAGES = {
        SUCCESS: "解析成功",
        ERR_API_KEY_INVALID: "APIキーが無効です。Google AI Studioで正しいキーを取得してください。",
        ERR_FILE_NOT_FOUND: "動画ファイルが見つかりません。",
        ERR_FILE_TOO_LARGE: "動画ファイルが大きすぎます（推奨: 500MB以下）。",
        ERR_FILE_UPLOAD_FAILED: "ファイルのアップロードに失敗しました。",
        ERR_FILE_PROCESSING_FAILED: "Gemini APIでのファイル処理に失敗しました。",
        ERR_API_QUOTA_EXCEEDED: "API利用制限を超えました。有料プランへのアップグレードをご検討ください。",
        ERR_API_RATE_LIMIT: "APIリクエスト数の制限を超えました。時間をおいて再試行してください。",
        ERR_UNSUPPORTED_FORMAT: "サポートされていない動画フォーマットです（対応: mp4, mov, avi, webm）。",
        ERR_GENERATE_CONTENT_FAILED: "コンテンツ生成に失敗しました。",
        ERR_RESPONSE_PARSE_FAILED: "APIレスポンスの解析に失敗しました。",
        ERR_UNKNOWN: "不明なエラーが発生しました。"
    }


class ChunkedVideoAnalyzer:
    """
    チャンク単位での動画解析クラス

    既存のVideoAnalyzerのロジックを再利用し、チャンク情報を付加する

    仮定:
        - google-genai SDKのFile APIは動画全体をアップロードする
        - 現時点では、チャンク単位の時間範囲指定は未対応
        - 将来的には、File API + 時間範囲パラメータでの解析をサポート予定
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", log_callback=None):
        """
        初期化

        Args:
            api_key: Gemini APIキー
            model: 使用するモデル名
            log_callback: ログメッセージを受け取るコールバック関数（オプション）
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.model = model
        self._client = None  # 遅延初期化
        self.log_callback = log_callback  # UIへのログ出力用

    @property
    def client(self):
        """Gemini クライアントを遅延初期化して返す"""
        if self._client is None:
            if genai is None:
                raise ImportError("google-genai package is not installed")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def analyze_chunk(self, chunk: ChunkInfo) -> Dict[str, Any]:
        """
        単一チャンクを解析（エラーハンドリング強化版）

        Args:
            chunk: チャンク情報

        Returns:
            Dict[str, Any]: 処理結果（status, error_code, 評価結果など）
            {
                "status": "success" or "error",
                "error_code": "SUCCESS" or "ERR_XXX",
                "error_message": "メッセージ",
                "chunk_id": 0,
                "chunk_time_range": {...},
                "processing_info": {
                    "file_uploaded": bool,
                    "file_state": str,
                    "content_generated": bool,
                    "response_parsed": bool
                },
                "evaluation": {...}  # 成功時のみ
            }
        """
        # 処理状態を追跡
        processing_info = {
            "file_uploaded": False,
            "file_state": "PENDING",
            "content_generated": False,
            "response_parsed": False
        }

        # ログ出力用ヘルパー関数
        def log(msg):
            safe_print(msg, self.log_callback)

        # 基本情報
        result = {
            "chunk_id": chunk.chunk_id,
            "chunk_time_range": {
                "start": chunk.start_time,
                "end": chunk.end_time
            },
            "processing_info": processing_info
        }

        try:
            # ステップ1: ファイル存在チェック
            if not os.path.exists(chunk.video_path):
                return self._create_error_result(
                    result,
                    AnalysisError.ERR_FILE_NOT_FOUND,
                    f"Video file not found: {chunk.video_path}"
                )

            # ステップ2: ファイルサイズチェック（500MB制限）
            file_size = os.path.getsize(chunk.video_path)
            max_size = 500 * 1024 * 1024  # 500MB
            if file_size > max_size:
                return self._create_error_result(
                    result,
                    AnalysisError.ERR_FILE_TOO_LARGE,
                    f"File size {file_size / 1024 / 1024:.1f}MB exceeds limit (500MB)"
                )

            log(f"[Chunk {chunk.chunk_id}] File OK: {file_size / 1024 / 1024:.1f}MB")

            # ステップ3: ナレッジベース読み込み
            knowledge_text = load_knowledge_base()

            # ステップ4: プロンプト構築
            prompt_text = build_prompt(knowledge_text)

            # ステップ5: ファイルアップロード
            log(f"[Chunk {chunk.chunk_id}] Uploading file...")
            log(f"[Chunk {chunk.chunk_id}] File path: {chunk.video_path}")
            log(f"[Chunk {chunk.chunk_id}] File exists: {os.path.exists(chunk.video_path)}")

            try:
                log(f"[Chunk {chunk.chunk_id}] Initializing Gemini client...")
                try:
                    client = self.client  # クライアント初期化を明示的に実行
                    log(f"[Chunk {chunk.chunk_id}] Gemini client initialized")

                    # APIが応答するかテスト
                    log(f"[Chunk {chunk.chunk_id}] Testing API connection by listing models...")
                    try:
                        models = client.models.list()
                        log(f"[Chunk {chunk.chunk_id}] API connection OK, found {len(list(models))} models")
                    except Exception as api_test_error:
                        log(f"[Chunk {chunk.chunk_id}] API test failed: {api_test_error}")
                        return self._create_error_result(
                            result,
                            AnalysisError.ERR_API_KEY_INVALID,
                            f"API connection failed: {str(api_test_error)}"
                        )
                except Exception as e:
                    log(f"[Chunk {chunk.chunk_id}] Client initialization failed: {e}")
                    raise

                # ファイルを開いて確認
                log(f"[Chunk {chunk.chunk_id}] Opening file for verification...")
                try:
                    with open(chunk.video_path, 'rb') as f:
                        first_bytes = f.read(100)
                        log(f"[Chunk {chunk.chunk_id}] File readable, first 10 bytes: {first_bytes[:10]}")
                except Exception as file_error:
                    return self._create_error_result(
                        result,
                        AnalysisError.ERR_FILE_NOT_FOUND,
                        f"Cannot read file: {str(file_error)}"
                    )

                # 直接アップロード（タイムアウトなし、詳細ログ付き）
                log(f"[Chunk {chunk.chunk_id}] Calling client.files.upload()...")
                log(f"[Chunk {chunk.chunk_id}] This may take several minutes for 118MB file...")

                try:
                    video_file = client.files.upload(file=chunk.video_path)
                    log(f"[Chunk {chunk.chunk_id}] files.upload() returned successfully")

                    if not video_file:
                        return self._create_error_result(
                            result,
                            AnalysisError.ERR_FILE_UPLOAD_FAILED,
                            "files.upload() returned None"
                        )

                    log(f"[Chunk {chunk.chunk_id}] File name: {video_file.name}, State: {video_file.state}")
                except Exception as upload_error:
                    log(f"[Chunk {chunk.chunk_id}] files.upload() raised exception: {upload_error}")
                    error_msg = str(upload_error).lower()
                    if "api key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
                        return self._create_error_result(
                            result,
                            AnalysisError.ERR_API_KEY_INVALID,
                            f"API authentication failed: {str(upload_error)}"
                        )
                    return self._create_error_result(
                        result,
                        AnalysisError.ERR_FILE_UPLOAD_FAILED,
                        f"File upload failed: {str(upload_error)}"
                    )

                # アップロード成功後の処理
                processing_info["file_uploaded"] = True
                processing_info["file_state"] = video_file.state
                log(f"[Chunk {chunk.chunk_id}] Upload successful (state: {video_file.state})")
            except Exception as e:
                error_msg = str(e).lower()
                # APIキー関連エラー
                if "api key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
                    return self._create_error_result(
                        result,
                        AnalysisError.ERR_API_KEY_INVALID,
                        f"API authentication failed: {str(e)}"
                    )
                # 一般的なアップロードエラー
                return self._create_error_result(
                    result,
                    AnalysisError.ERR_FILE_UPLOAD_FAILED,
                    f"File upload failed: {str(e)}"
                )

            # ステップ6: ファイルがACTIVE状態になるまで待機
            log(f"[Chunk {chunk.chunk_id}] Waiting for file processing...")
            timeout_count = 0
            max_timeout = 60  # 最大2分（2秒 × 60回）

            while video_file.state != "ACTIVE":
                if timeout_count >= max_timeout:
                    return self._create_error_result(
                        result,
                        AnalysisError.ERR_FILE_PROCESSING_FAILED,
                        f"File processing timeout (state: {video_file.state})"
                    )

                time.sleep(2)
                timeout_count += 1
                video_file = self.client.files.get(name=video_file.name)
                processing_info["file_state"] = video_file.state

                if video_file.state == "FAILED":
                    return self._create_error_result(
                        result,
                        AnalysisError.ERR_FILE_PROCESSING_FAILED,
                        f"Gemini API file processing failed: {video_file.name}"
                    )

                if timeout_count % 5 == 0:  # 10秒ごとにログ出力
                    log(f"[Chunk {chunk.chunk_id}] File state: {video_file.state} (waiting {timeout_count * 2}s)")

            log(f"[Chunk {chunk.chunk_id}] File is ACTIVE. Generating content...")

            # ステップ7: コンテンツ生成
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[prompt_text, video_file]
                )
                processing_info["content_generated"] = True
                response_text = response.text
                log(f"[Chunk {chunk.chunk_id}] Content generated: {len(response_text)} chars")

                # デバッグ: レスポンステキストの先頭500文字を出力
                log(f"[Chunk {chunk.chunk_id}] Response preview: {response_text[:500]}")
            except Exception as e:
                error_msg = str(e).lower()
                # API制限エラー
                if "quota" in error_msg or "limit exceeded" in error_msg:
                    return self._create_error_result(
                        result,
                        AnalysisError.ERR_API_QUOTA_EXCEEDED,
                        f"API quota exceeded: {str(e)}"
                    )
                if "rate limit" in error_msg:
                    return self._create_error_result(
                        result,
                        AnalysisError.ERR_API_RATE_LIMIT,
                        f"API rate limit exceeded: {str(e)}"
                    )
                # 一般的なコンテンツ生成エラー
                return self._create_error_result(
                    result,
                    AnalysisError.ERR_GENERATE_CONTENT_FAILED,
                    f"Content generation failed: {str(e)}"
                )

            # ステップ8: レスポンスパース
            try:
                evaluation = parse_response(response_text)
                processing_info["response_parsed"] = True
                log(f"[Chunk {chunk.chunk_id}] Response parsed successfully")

                # デバッグ: パース結果のスコアを出力
                overall_score = evaluation.get("overall_risk_score", "N/A")
                log(f"[Chunk {chunk.chunk_id}] Parsed overall_risk_score: {overall_score}")
            except Exception as e:
                return self._create_error_result(
                    result,
                    AnalysisError.ERR_RESPONSE_PARSE_FAILED,
                    f"Response parsing failed: {str(e)}"
                )

            # 成功結果を返す
            result["status"] = "success"
            result["error_code"] = AnalysisError.SUCCESS
            result["error_message"] = AnalysisError.MESSAGES[AnalysisError.SUCCESS]

            # parse_responseの結果を展開してresultにマージ
            result["overall_risk_score"] = evaluation.get("overall_risk_score", 0)
            result["risk_level"] = evaluation.get("risk_level", "不明")
            result["evaluation"] = evaluation.get("evaluation", {})
            result["red_flags"] = evaluation.get("red_flags", [])
            result["positive_signals"] = evaluation.get("positive_signals", [])
            result["recommendation"] = evaluation.get("recommendation", "")
            result["disclaimer"] = evaluation.get("disclaimer", "")

            log(f"[Chunk {chunk.chunk_id}] ✓ Analysis completed successfully")
            return result

        except Exception as e:
            # 予期しないエラー
            return self._create_error_result(
                result,
                AnalysisError.ERR_UNKNOWN,
                f"Unexpected error: {str(e)}"
            )

    def _create_error_result(
        self,
        base_result: Dict[str, Any],
        error_code: str,
        detail_message: str
    ) -> Dict[str, Any]:
        """
        エラー結果を作成するヘルパーメソッド

        Args:
            base_result: ベース結果（chunk_id等を含む）
            error_code: エラーコード
            detail_message: 詳細メッセージ

        Returns:
            エラー結果辞書
        """
        base_result["status"] = "error"
        base_result["error_code"] = error_code
        base_result["error_message"] = AnalysisError.MESSAGES.get(error_code, "Unknown error")
        base_result["error_detail"] = detail_message

        chunk_id = base_result.get("chunk_id", "?")
        safe_print(f"[Chunk {chunk_id}] ✗ ERROR: {error_code} - {detail_message}")

        return base_result

    def analyze_chunks(
        self,
        chunks: List[ChunkInfo],
        parallel: bool = True,
        max_workers: int = 3
    ) -> List[Dict[str, Any]]:
        """
        複数チャンクを解析（並列または順次）

        Args:
            chunks: チャンク情報のリスト
            parallel: 並列処理を使用するか（デフォルト: True）
            max_workers: 並列処理の最大ワーカー数（デフォルト: 3）

        Returns:
            List[Dict[str, Any]]: 各チャンクの評価結果のリスト（元の順序を維持）

        注意:
            - 並列処理を使用すると処理時間が大幅に短縮されます
            - max_workersはAPI制限に応じて調整してください
        """
        if not parallel:
            # 順次処理
            return self._analyze_chunks_sequential(chunks)

        # 並列処理
        return self._analyze_chunks_parallel(chunks, max_workers)

    def _analyze_chunks_sequential(self, chunks: List[ChunkInfo]) -> List[Dict[str, Any]]:
        """
        複数チャンクを順次解析

        Args:
            chunks: チャンク情報のリスト

        Returns:
            List[Dict[str, Any]]: 各チャンクの評価結果のリスト
        """
        results = []
        for chunk in chunks:
            result = self.analyze_chunk(chunk)
            results.append(result)

        return results

    def _analyze_chunks_parallel(
        self,
        chunks: List[ChunkInfo],
        max_workers: int
    ) -> List[Dict[str, Any]]:
        """
        複数チャンクを並列解析

        Args:
            chunks: チャンク情報のリスト
            max_workers: 並列処理の最大ワーカー数

        Returns:
            List[Dict[str, Any]]: 各チャンクの評価結果のリスト（元の順序を維持）
        """
        # チャンクIDと結果を紐づけるための辞書
        results_dict = {}

        # ThreadPoolExecutorで並列処理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 各チャンクの解析タスクを投入
            future_to_chunk = {
                executor.submit(self.analyze_chunk, chunk): chunk
                for chunk in chunks
            }

            # 完了したタスクから結果を取得
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    result = future.result()
                    results_dict[chunk.chunk_id] = result
                except Exception as e:
                    # エラーが発生した場合はエラー情報を記録
                    results_dict[chunk.chunk_id] = {
                        "chunk_id": chunk.chunk_id,
                        "error": str(e),
                        "chunk_time_range": {
                            "start": chunk.start_time,
                            "end": chunk.end_time
                        }
                    }

        # 元の順序（chunk_id順）で結果を返す
        results = [results_dict[chunk.chunk_id] for chunk in chunks]

        return results
