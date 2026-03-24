"""動画解析アナライザーモジュール"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# 環境変数読み込み
from dotenv import load_dotenv

# Gemini SDK
# 仮定: google-genai SDKのインポートパスは `from google import genai`
try:
    from google import genai
except ImportError:
    genai = None
    try:
        print("Warning: google-genai not installed. Install with: pip install google-genai")
    except:
        pass

# 内部モジュール
from .knowledge_loader import load_knowledge_base
from .prompt_builder import build_prompt
from .response_parser import parse_response


# Streamlit環境でのprint安全化
def safe_print(msg, log_callback=None):
    """Streamlit環境でもエラーにならないprint関数"""
    try:
        print(msg)
    except (ValueError, OSError):
        pass
    if log_callback:
        try:
            log_callback(msg)
        except:
            pass


class VideoAnalyzer:
    """
    Gemini 2.5 Flash APIを使用した動画解析クラス

    仮定:
        - google-genai SDKのAPI: `client = genai.Client(api_key=...)`
        - ファイルアップロード: `client.files.upload(file=...)`
        - コンテンツ生成: `client.models.generate_content(model=..., contents=[...])`
        - レスポンス取得: `response.text`
    """

    SUPPORTED_FORMATS = [".mp4", ".mov", ".avi", ".webm"]

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", log_callback=None):
        """
        初期化

        Args:
            api_key: Gemini APIキー
            model: 使用するモデル名（デフォルト: gemini-2.5-flash）
            log_callback: ログメッセージを受け取るコールバック関数（オプション）
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.model = model
        self._client = None  # 遅延初期化
        self.log_callback = log_callback

    @property
    def client(self):
        """Gemini クライアントを遅延初期化して返す"""
        if self._client is None:
            if genai is None:
                raise ImportError("google-genai package is not installed")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def analyze(self, video_path: str, transcript: str = None, knowledge_text: str = None) -> Dict[str, Any]:
        """
        動画を解析し、評価結果を返す

        Args:
            video_path: 動画ファイルのパス
            transcript: 文字起こしテキスト（オプション。Whisper使用時に渡す）
            knowledge_text: カスタムナレッジベーステキスト（オプション。Noneの場合はデフォルトを使用）

        Returns:
            Dict[str, Any]: 評価結果（JSON形式）

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: サポート外の拡張子の場合
        """
        # ログ出力用ヘルパー関数
        def log(msg):
            safe_print(msg, self.log_callback)

        # 1. ファイル存在チェック
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 2. 拡張子チェック
        file_ext = Path(video_path).suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported video format: {file_ext}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # 3. ナレッジベース読み込み
        if knowledge_text is None:
            knowledge_text = load_knowledge_base()

        # 4. プロンプト構築
        prompt_text = build_prompt(knowledge_text, transcript=transcript)

        # 5. Gemini API呼び出し
        try:
            # ファイルアップロード
            log(f"Uploading video file...")
            log(f"File path: {video_path}")
            log(f"File exists: {os.path.exists(video_path)}")
            log(f"File size: {os.path.getsize(video_path) / 1024 / 1024:.1f}MB")

            log("Initializing Gemini client...")
            try:
                client = self.client  # クライアント初期化を明示的に実行
                log("Gemini client initialized")
            except Exception as e:
                log(f"Client initialization failed: {e}")
                raise

            # ファイルを開いて確認
            log("Opening file for verification...")
            try:
                with open(video_path, 'rb') as f:
                    first_bytes = f.read(100)
                    log(f"File readable, first 10 bytes: {first_bytes[:10]}")
            except Exception as file_error:
                raise FileNotFoundError(f"Cannot read file: {str(file_error)}")

            # 直接アップロード（詳細ログ付き）
            log("Calling client.files.upload()...")
            log("This may take several minutes for large files...")

            video_file = client.files.upload(file=video_path)
            log(f"files.upload() returned successfully, state: {video_file.state if video_file else 'None'}")

            # ファイルがACTIVE状態になるまで待機
            import time
            log(f"Waiting for file to be processed (state: {video_file.state})...")
            while video_file.state != "ACTIVE":
                time.sleep(2)
                video_file = self.client.files.get(name=video_file.name)
                log(f"File state: {video_file.state}")
                if video_file.state == "FAILED":
                    raise Exception(f"File processing failed: {video_file.name}")

            log(f"File is active. Generating content...")

            # コンテンツ生成
            # 仮定: contents引数にプロンプトとファイルを渡す
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt_text, video_file]
            )

            # レスポンステキスト取得
            # 仮定: response.textで文字列を取得
            response_text = response.text

        except Exception as e:
            # APIエラーをそのまま再送出
            raise e

        # 6. レスポンスパース
        result = parse_response(response_text)

        return result


def main():
    """CLIエントリーポイント"""
    # 引数パーサー
    parser = argparse.ArgumentParser(
        description="AI面談動画解析ツール - Gemini 2.5 Flash使用"
    )
    parser.add_argument(
        "video_path",
        help="解析する動画ファイルのパス"
    )
    parser.add_argument(
        "--api-key",
        help="Gemini APIキー（省略時は環境変数GEMINI_API_KEYを使用）"
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="使用するモデル名（デフォルト: gemini-2.5-flash）"
    )

    args = parser.parse_args()

    # 環境変数読み込み
    load_dotenv()

    # APIキー取得
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set. Use --api-key or set GEMINI_API_KEY in .env")
        sys.exit(1)

    # アナライザー初期化
    try:
        analyzer = VideoAnalyzer(api_key=api_key, model=args.model)
    except ImportError as e:
        print(f"Error: {e}")
        print("Install dependencies: pip install -r requirements.txt")
        sys.exit(1)

    # 解析実行
    try:
        log(f"Analyzing video: {args.video_path}")
        result = analyzer.analyze(args.video_path)

        # 結果をJSON形式で出力
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
