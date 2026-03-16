"""動画チャンク化モジュール"""
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


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

    def __init__(self, chunk_duration_seconds: int = 300, output_dir: Optional[str] = None):
        """
        初期化

        Args:
            chunk_duration_seconds: チャンクの長さ（秒）。デフォルト: 300秒（5分）
            output_dir: 分割ファイルの出力ディレクトリ。Noneの場合は temp/chunks/ を使用
        """
        self.chunk_duration = chunk_duration_seconds
        self.output_dir = output_dir
        self._created_files = []  # クリーンアップ用に作成したファイルを追跡

    def create_chunks(self, video_path: str, video_duration_seconds: int, split_physically: bool = True) -> List[ChunkInfo]:
        """
        動画を時間軸で分割し、チャンク情報のリストを生成
        split_physically=Trueの場合、ffmpegで動画を物理的に分割

        Args:
            video_path: 動画ファイルのパス
            video_duration_seconds: 動画の長さ（秒）
            split_physically: 物理的に動画を分割するか（デフォルト: True）

        Returns:
            List[ChunkInfo]: チャンク情報のリスト

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: サポート外の拡張子の場合
            RuntimeError: ffmpegによる分割に失敗した場合
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

        # 出力ディレクトリの決定
        if self.output_dir is None:
            # プロジェクトルート/temp/chunks/を使用
            project_root = Path(__file__).parent.parent
            output_dir = project_root / "temp" / "chunks"
        else:
            output_dir = Path(self.output_dir)

        # 出力ディレクトリを作成
        output_dir.mkdir(parents=True, exist_ok=True)

        # チャンク情報の生成
        chunks = []
        current_time = 0
        chunk_id = 0

        while current_time < video_duration_seconds:
            # 次のチャンクの終了時刻を計算
            end_time = min(current_time + self.chunk_duration, video_duration_seconds)
            duration = end_time - current_time

            # チャンクのファイルパスを決定
            if split_physically:
                # 物理的に分割する場合、分割後のファイルパスを指定
                chunk_filename = f"chunk_{chunk_id:03d}{file_ext}"
                chunk_path = str(output_dir / chunk_filename)
            else:
                # 分割しない場合は元のファイルパスを使用（旧方式）
                chunk_path = video_path

            # ChunkInfoを作成
            chunk = ChunkInfo(
                chunk_id=chunk_id,
                start_time=current_time,
                end_time=end_time,
                duration=duration,
                video_path=chunk_path
            )
            chunks.append(chunk)

            # 次のチャンクへ
            current_time = end_time
            chunk_id += 1

        # 物理的に分割を実行
        if split_physically:
            self._split_video_with_ffmpeg(video_path, chunks, file_ext)

        return chunks

    def _split_video_with_ffmpeg(self, video_path: str, chunks: List[ChunkInfo], file_ext: str):
        """
        ffmpegを使って動画を物理的に分割

        Args:
            video_path: 元の動画ファイルのパス
            chunks: チャンク情報のリスト
            file_ext: ファイル拡張子

        Raises:
            RuntimeError: ffmpegの実行に失敗した場合
        """
        print(f"Splitting video into {len(chunks)} chunks using ffmpeg...")

        for chunk in chunks:
            # ffmpegコマンドを構築
            # -ss: 開始時刻、-t: 長さ、-c copy: 再エンコードなし（高速）
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-ss", str(chunk.start_time),
                "-t", str(chunk.duration),
                "-c", "copy",  # 再エンコードなし
                "-y",  # 上書き確認なし
                chunk.video_path
            ]

            try:
                # ffmpegを実行
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"Created chunk {chunk.chunk_id}: {chunk.video_path}")
                self._created_files.append(chunk.video_path)

            except subprocess.CalledProcessError as e:
                # ffmpegのエラー
                error_msg = e.stderr if e.stderr else str(e)
                raise RuntimeError(f"ffmpeg failed to split video (chunk {chunk.chunk_id}): {error_msg}")
            except FileNotFoundError:
                raise RuntimeError(
                    "ffmpeg not found. Please install ffmpeg:\n"
                    "  Windows: choco install ffmpeg or download from https://ffmpeg.org/\n"
                    "  Mac: brew install ffmpeg\n"
                    "  Linux: sudo apt-get install ffmpeg"
                )

    def cleanup(self):
        """
        作成した分割ファイルを削除
        """
        for file_path in self._created_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted chunk file: {file_path}")
            except Exception as e:
                print(f"Warning: Failed to delete {file_path}: {e}")

        self._created_files.clear()


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
