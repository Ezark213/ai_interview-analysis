"""チャンク単位での動画解析モジュール"""
import json
import sys
import time
import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 内部モジュール
from video_chunker import ChunkInfo
from knowledge_loader import load_knowledge_base
from prompt_builder import build_prompt
from response_parser import parse_response

# Gemini SDK
try:
    from google import genai
except ImportError:
    genai = None


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

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """
        初期化

        Args:
            api_key: Gemini APIキー
            model: 使用するモデル名
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.model = model
        self._client = None  # 遅延初期化

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
        単一チャンクを解析

        Args:
            chunk: チャンク情報

        Returns:
            Dict[str, Any]: 評価結果（chunk_id, chunk_time_range付き）

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            Exception: APIエラー

        仮定:
            - 現時点では、動画全体をアップロードして解析
            - チャンク単位の時間範囲指定は将来的に実装
            - chunk.start_time, chunk.end_timeはメタデータとして付加のみ
        """
        # ナレッジベース読み込み
        knowledge_text = load_knowledge_base()

        # プロンプト構築
        prompt_text = build_prompt(knowledge_text)

        # Gemini API呼び出し
        try:
            # ファイルアップロード
            video_file = self.client.files.upload(file=chunk.video_path)

            # ファイルがACTIVE状態になるまで待機
            print(f"[Chunk {chunk.chunk_id}] Waiting for file to be processed (state: {video_file.state})...", file=sys.stderr)
            while video_file.state != "ACTIVE":
                time.sleep(2)
                video_file = self.client.files.get(name=video_file.name)
                print(f"[Chunk {chunk.chunk_id}] File state: {video_file.state}", file=sys.stderr)
                if video_file.state == "FAILED":
                    raise Exception(f"File processing failed for chunk {chunk.chunk_id}: {video_file.name}")

            print(f"[Chunk {chunk.chunk_id}] File is active. Generating content...", file=sys.stderr)

            # コンテンツ生成
            # TODO: 将来的には時間範囲パラメータを追加
            # 仮定: 現時点では動画全体を解析（チャンク範囲は考慮しない）
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt_text, video_file]
            )

            response_text = response.text

        except Exception as e:
            # APIエラーをそのまま再送出
            raise e

        # レスポンスパース
        result = parse_response(response_text)

        # チャンク情報を付加
        result["chunk_id"] = chunk.chunk_id
        result["chunk_time_range"] = {
            "start": chunk.start_time,
            "end": chunk.end_time
        }

        return result

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
