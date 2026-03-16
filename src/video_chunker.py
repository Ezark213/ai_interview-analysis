"""動画チャンク化モジュール"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ChunkInfo:
    """
    チャンク情報を保持するデータクラス

    Attributes:
        chunk_id: チャンクID（0から開始）
        start_time: 開始時刻（秒）
        end_time: 終了時刻（秒）
        duration: チャンク長（秒）
        video_path: 元動画のパス
    """
    chunk_id: int
    start_time: int
    end_time: int
    duration: int
    video_path: str


class VideoChunker:
    """
    動画を時間軸で分割するクラス

    仕様の仮定:
        - 動画の長さ（duration）は外部から渡される（moviepy, ffmpeg等で事前取得）
        - チャンクは時間情報のみ保持（物理的な分割は将来的に実装）
        - サポートする拡張子: .mp4, .mov, .avi, .webm
        - .wmvはサポート外
    """

    SUPPORTED_FORMATS = [".mp4", ".mov", ".avi", ".webm"]
    UNSUPPORTED_FORMATS = [".wmv"]  # 明示的にサポート外

    def __init__(self, chunk_duration_seconds: int = 300):
        """
        初期化

        Args:
            chunk_duration_seconds: チャンクの長さ（秒）。デフォルト: 300秒（5分）
        """
        self.chunk_duration = chunk_duration_seconds

    def create_chunks(self, video_path: str, video_duration_seconds: int) -> List[ChunkInfo]:
        """
        動画を時間軸で分割し、チャンク情報のリストを生成

        Args:
            video_path: 動画ファイルのパス
            video_duration_seconds: 動画の長さ（秒）

        Returns:
            List[ChunkInfo]: チャンク情報のリスト

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: サポート外の拡張子の場合

        仮定:
            - video_duration_secondsは正確な値が渡されることを前提
            - チャンクは時間軸のメタデータのみ（物理的分割は将来実装）
        """
        # ファイル存在チェック
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 拡張子チェック
        file_ext = Path(video_path).suffix.lower()
        if file_ext in self.UNSUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported video format: {file_ext}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # チャンク情報の生成
        chunks = []
        current_time = 0
        chunk_id = 0

        while current_time < video_duration_seconds:
            # 次のチャンクの終了時刻を計算
            end_time = min(current_time + self.chunk_duration, video_duration_seconds)
            duration = end_time - current_time

            # ChunkInfoを作成
            chunk = ChunkInfo(
                chunk_id=chunk_id,
                start_time=current_time,
                end_time=end_time,
                duration=duration,
                video_path=video_path
            )
            chunks.append(chunk)

            # 次のチャンクへ
            current_time = end_time
            chunk_id += 1

        return chunks


def get_video_duration(video_path: str) -> int:
    """
    動画の長さ（秒）を取得

    Args:
        video_path: 動画ファイルのパス

    Returns:
        int: 動画の長さ（秒）

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        RuntimeError: ffprobeの実行に失敗した場合
    """
    import ffmpeg

    # ファイル存在チェック
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    try:
        # ffprobeで動画情報を取得
        probe = ffmpeg.probe(video_path)

        # duration（秒）を取得
        video_info = next(
            stream for stream in probe['streams']
            if stream['codec_type'] == 'video'
        )

        # durationは文字列の場合があるのでfloatに変換して整数に丸める
        duration = float(probe['format']['duration'])
        return int(duration)

    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to get video duration: {e.stderr.decode() if e.stderr else str(e)}")
    except (KeyError, StopIteration) as e:
        raise RuntimeError(f"Failed to parse video metadata: {str(e)}")
