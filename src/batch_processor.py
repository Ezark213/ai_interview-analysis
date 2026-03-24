"""バッチ処理モジュール

複数の面談動画を一括で順次解析し、結果をCSV/JSONでエクスポートする。
Iteration-11: バッチ処理機能（MS5最終成果物）
"""
import json
import csv
import io
import time
from typing import List, Dict, Any, Optional, Callable


class BatchProcessor:
    """複数動画の一括解析を管理するクラス"""

    MAX_BATCH_SIZE = 10  # バッチ上限

    def __init__(self, analyzer_factory: Callable, log_callback: Optional[Callable] = None):
        """
        Args:
            analyzer_factory: 解析器を生成するファクトリ関数
                → lambda: VideoAnalyzer(api_keys=keys, model=model) のような形
            log_callback: ログコールバック（進捗通知用）
        """
        self.analyzer_factory = analyzer_factory
        self.log_callback = log_callback
        self.results: List[Dict[str, Any]] = []

    def process_batch(
        self,
        video_paths: List[str],
        video_names: List[str],
        wait_seconds: int = 30,
        **analyze_kwargs
    ) -> List[Dict[str, Any]]:
        """
        複数動画を順次処理

        Args:
            video_paths: 動画ファイルパスのリスト
            video_names: 表示用ファイル名のリスト
            wait_seconds: 動画間の待機秒数（API制限対策）
            **analyze_kwargs: analyze()に渡す追加引数（knowledge_text等）

        Returns:
            List[Dict]: 各動画の結果。失敗時はerrorフィールド付き

        Raises:
            ValueError: video_pathsが空の場合
        """
        if not video_paths:
            raise ValueError("video_paths cannot be empty")

        if len(video_paths) > self.MAX_BATCH_SIZE:
            raise ValueError(
                f"Batch size {len(video_paths)} exceeds maximum {self.MAX_BATCH_SIZE}"
            )

        results = []
        analyzer = self.analyzer_factory()

        for i, (path, name) in enumerate(zip(video_paths, video_names)):
            if self.log_callback:
                self.log_callback(f"Processing {i+1}/{len(video_paths)}: {name}")

            try:
                raw_result = analyzer.analyze(path, **analyze_kwargs)
                result = dict(raw_result)  # 元の辞書を変更しないようコピー
                result["filename"] = name
                result["status"] = "success"
                results.append(result)
            except Exception as e:
                results.append({
                    "filename": name,
                    "status": "error",
                    "error": str(e),
                    "overall_risk_score": None,
                    "risk_level": None,
                    "evaluation": None,
                    "behavioral_metrics": None,
                    "red_flags": [],
                    "positive_signals": [],
                    "recommendation": None,
                    "disclaimer": None,
                })

            # 最後の動画以外は待機（API制限対策）
            if i < len(video_paths) - 1 and wait_seconds > 0:
                if self.log_callback:
                    self.log_callback(f"Waiting {wait_seconds}s before next video...")
                time.sleep(wait_seconds)

        self.results = results
        return results

    def export_to_csv(self, results: List[Dict] = None) -> str:
        """
        結果をCSV文字列としてエクスポート

        Args:
            results: エクスポート対象の結果リスト。Noneの場合は最後のバッチ結果を使用

        Returns:
            str: CSV形式の文字列
        """
        if results is None:
            results = self.results

        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー
        writer.writerow([
            "ファイル名",
            "ステータス",
            "総合スコア",
            "リスクレベル",
            "コミュニケーション",
            "ストレス耐性",
            "信頼性",
            "チームワーク",
            "推奨事項",
        ])

        for r in results:
            evaluation = r.get("evaluation") or {}
            writer.writerow([
                r.get("filename", ""),
                r.get("status", ""),
                r.get("overall_risk_score", ""),
                r.get("risk_level", ""),
                evaluation.get("communication", {}).get("score", "") if isinstance(evaluation, dict) else "",
                evaluation.get("stress_tolerance", {}).get("score", "") if isinstance(evaluation, dict) else "",
                evaluation.get("reliability", {}).get("score", "") if isinstance(evaluation, dict) else "",
                evaluation.get("teamwork", {}).get("score", "") if isinstance(evaluation, dict) else "",
                r.get("recommendation", ""),
            ])

        return output.getvalue()

    def export_to_json(self, results: List[Dict] = None) -> str:
        """
        結果をJSON文字列としてエクスポート

        Args:
            results: エクスポート対象の結果リスト。Noneの場合は最後のバッチ結果を使用

        Returns:
            str: JSON形式の文字列
        """
        if results is None:
            results = self.results

        return json.dumps(results, ensure_ascii=False, indent=2)

    @staticmethod
    def summarize_results(results: List[Dict]) -> Dict:
        """
        バッチ全体のサマリーを生成

        Args:
            results: 解析結果のリスト

        Returns:
            Dict: サマリー情報（成功/失敗数、平均スコア等）
        """
        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") == "error"]

        scores = [
            r["overall_risk_score"]
            for r in successful
            if r.get("overall_risk_score") is not None
        ]

        return {
            "total": len(results),
            "success_count": len(successful),
            "error_count": len(failed),
            "average_score": round(sum(scores) / len(scores), 1) if scores else None,
            "min_score": min(scores) if scores else None,
            "max_score": max(scores) if scores else None,
        }
