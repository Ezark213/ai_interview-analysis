"""
Whisper APIを使った動画音声の文字起こしモジュール

OpenAI Whisper APIを使用して動画から音声を抽出し、
テキストに変換します。
"""
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict
import json


class WhisperTranscriber:
    """Whisper APIを使った音声文字起こしクラス"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初期化

        Args:
            api_key: OpenAI APIキー（Noneの場合は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. "
                "Please set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

    def extract_audio(self, video_path: str, output_audio_path: Optional[str] = None) -> str:
        """
        動画から音声を抽出

        Args:
            video_path: 動画ファイルのパス
            output_audio_path: 出力音声ファイルのパス（Noneの場合は自動生成）

        Returns:
            抽出された音声ファイルのパス

        Raises:
            FileNotFoundError: 動画ファイルが存在しない
            RuntimeError: ffmpegでの音声抽出に失敗
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 出力パスの生成
        if output_audio_path is None:
            video_stem = Path(video_path).stem
            output_audio_path = f"temp/{video_stem}_audio.mp3"

        # 出力ディレクトリの作成
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)

        # ffmpegで音声を抽出
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # 動画ストリームを無効化
            "-acodec", "libmp3lame",  # MP3エンコーダー
            "-q:a", "4",  # 音質（0-9、低いほど高品質）
            "-y",  # 上書き
            output_audio_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"Audio extracted: {output_audio_path}")
            return output_audio_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to extract audio from video: {e.stderr}"
            )

    def transcribe(self, audio_path: str, language: str = "ja") -> Dict:
        """
        音声ファイルを文字起こし

        Args:
            audio_path: 音声ファイルのパス
            language: 言語コード（デフォルト: ja（日本語））

        Returns:
            文字起こし結果（辞書形式）
            {
                "text": "文字起こしされたテキスト",
                "segments": [
                    {
                        "start": 0.0,
                        "end": 5.2,
                        "text": "セグメントのテキスト"
                    },
                    ...
                ]
            }

        Raises:
            FileNotFoundError: 音声ファイルが存在しない
            RuntimeError: Whisper APIでの文字起こしに失敗
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            # OpenAI SDKのインポート（遅延インポート）
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            # 音声ファイルを開いて文字起こし
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",  # タイムスタンプ付き
                    timestamp_granularities=["segment"]
                )

            # 結果を整形
            result = {
                "text": transcript.text,
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text
                    }
                    for seg in transcript.segments
                ] if hasattr(transcript, 'segments') else []
            }

            print(f"Transcription completed: {len(result['text'])} characters")
            return result

        except ImportError:
            raise RuntimeError(
                "OpenAI SDK not installed. "
                "Please run: pip install openai"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to transcribe audio: {str(e)}"
            )

    def transcribe_video(
        self,
        video_path: str,
        language: str = "ja",
        cleanup: bool = True
    ) -> Dict:
        """
        動画から音声を抽出して文字起こし

        Args:
            video_path: 動画ファイルのパス
            language: 言語コード（デフォルト: ja（日本語））
            cleanup: 音声ファイルを削除するか（デフォルト: True）

        Returns:
            文字起こし結果（辞書形式）

        Raises:
            FileNotFoundError: 動画ファイルが存在しない
            RuntimeError: 処理に失敗
        """
        audio_path = None
        try:
            # 音声を抽出
            audio_path = self.extract_audio(video_path)

            # 文字起こし
            result = self.transcribe(audio_path, language=language)

            return result

        finally:
            # クリーンアップ
            if cleanup and audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"Cleaned up: {audio_path}")

    def save_transcript(self, transcript: Dict, output_path: str):
        """
        文字起こし結果をファイルに保存

        Args:
            transcript: 文字起こし結果
            output_path: 出力ファイルのパス（.json または .txt）
        """
        output_path = Path(output_path)

        if output_path.suffix == ".json":
            # JSON形式で保存
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(transcript, f, ensure_ascii=False, indent=2)

        elif output_path.suffix == ".txt":
            # テキスト形式で保存
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(transcript["text"])

                # セグメント情報も追加
                if transcript.get("segments"):
                    f.write("\n\n--- セグメント情報 ---\n")
                    for seg in transcript["segments"]:
                        f.write(
                            f"[{seg['start']:.1f}s - {seg['end']:.1f}s] "
                            f"{seg['text']}\n"
                        )

        else:
            raise ValueError(
                f"Unsupported file format: {output_path.suffix}. "
                "Use .json or .txt"
            )

        print(f"Transcript saved: {output_path}")


def main():
    """
    CLIエントリーポイント

    使用例:
        python src/whisper_transcriber.py video.mp4
        python src/whisper_transcriber.py video.mp4 --output transcript.json
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="動画から音声を抽出して文字起こし"
    )
    parser.add_argument(
        "video_path",
        help="動画ファイルのパス"
    )
    parser.add_argument(
        "--output", "-o",
        help="出力ファイルのパス（.json または .txt）",
        default=None
    )
    parser.add_argument(
        "--language", "-l",
        help="言語コード（デフォルト: ja）",
        default="ja"
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI APIキー",
        default=None
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="音声ファイルを削除しない"
    )

    args = parser.parse_args()

    # 文字起こし実行
    transcriber = WhisperTranscriber(api_key=args.api_key)
    result = transcriber.transcribe_video(
        args.video_path,
        language=args.language,
        cleanup=not args.no_cleanup
    )

    # 結果を保存
    if args.output:
        transcriber.save_transcript(result, args.output)
    else:
        # 標準出力に表示
        print("\n--- 文字起こし結果 ---")
        print(result["text"])


if __name__ == "__main__":
    main()
