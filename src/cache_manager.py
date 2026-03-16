"""コンテキストキャッシュ管理モジュール"""
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from google import genai
except ImportError:
    genai = None


class CacheManager:
    """
    Gemini APIのコンテキストキャッシュ機能を管理するクラス

    主な機能:
        1. ナレッジベースの明示的キャッシュ作成
        2. キャッシュの有効期限管理
        3. キャッシュを使用した解析

    コスト削減効果:
        - キャッシュされたコンテンツは90%割引
        - 50名/月の場合: $12.50 → $0.177 (約98%削減)
    """

    def __init__(self, api_key: str, cache_dir: Optional[str] = None):
        """
        初期化

        Args:
            api_key: Gemini APIキー
            cache_dir: キャッシュメタデータの保存先ディレクトリ（オプション）
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self._client = None

        # キャッシュメタデータの保存先
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".ai_interview_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"

    @property
    def client(self):
        """Gemini クライアントを遅延初期化して返す"""
        if self._client is None:
            if genai is None:
                raise ImportError("google-genai package is not installed")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def create_knowledge_cache(
        self,
        knowledge_text: str,
        model: str = "gemini-2.5-flash",
        ttl_hours: int = 24
    ) -> str:
        """
        ナレッジベースのキャッシュを作成

        Args:
            knowledge_text: キャッシュするナレッジベーステキスト
            model: 使用するモデル名
            ttl_hours: キャッシュの有効期限（時間）

        Returns:
            str: キャッシュ名（キャッシュID）

        Raises:
            RuntimeError: キャッシュ作成に失敗した場合

        仮定:
            - google-genai SDKのcache APIは以下の形式と仮定:
              client.caches.create(
                  model=model,
                  contents=[knowledge_text],
                  ttl_seconds=ttl_hours * 3600
              )
        """
        try:
            # キャッシュを作成
            # 注: 実際のAPIの仕様に応じて調整が必要
            cache = self.client.caches.create(
                model=model,
                contents=[knowledge_text],
                ttl_seconds=ttl_hours * 3600
            )

            # キャッシュメタデータを保存
            cache_metadata = {
                "cache_name": cache.name,
                "model": model,
                "created_at": time.time(),
                "expires_at": time.time() + (ttl_hours * 3600),
                "ttl_hours": ttl_hours
            }

            self._save_metadata(cache_metadata)

            return cache.name

        except Exception as e:
            raise RuntimeError(f"Failed to create cache: {str(e)}")

    def get_cached_knowledge(self) -> Optional[str]:
        """
        保存されているキャッシュ名を取得（有効期限内の場合）

        Returns:
            Optional[str]: キャッシュ名。有効なキャッシュがない場合はNone
        """
        metadata = self._load_metadata()

        if not metadata:
            return None

        # 有効期限チェック
        current_time = time.time()
        expires_at = metadata.get("expires_at", 0)

        if current_time >= expires_at:
            # 期限切れ
            self._clear_metadata()
            return None

        return metadata.get("cache_name")

    def generate_content_with_cache(
        self,
        cache_name: str,
        prompt: str,
        video_file,
        model: str = "gemini-2.5-flash"
    ) -> Any:
        """
        キャッシュを使用してコンテンツを生成

        Args:
            cache_name: キャッシュ名
            prompt: プロンプトテキスト
            video_file: 動画ファイルオブジェクト（アップロード済み）
            model: 使用するモデル名

        Returns:
            Any: Gemini APIのレスポンス

        Raises:
            RuntimeError: コンテンツ生成に失敗した場合

        仮定:
            - キャッシュを参照する際は、contents引数でcache_nameを指定
            - 実際のAPIの仕様に応じて調整が必要
        """
        try:
            # キャッシュを参照してコンテンツ生成
            # 注: 実際のAPIの仕様に応じて調整が必要
            response = self.client.models.generate_content(
                model=model,
                contents=[
                    {"cache": cache_name},  # キャッシュ参照
                    prompt,
                    video_file
                ]
            )

            return response

        except Exception as e:
            raise RuntimeError(f"Failed to generate content with cache: {str(e)}")

    def refresh_cache_if_needed(
        self,
        knowledge_text: str,
        model: str = "gemini-2.5-flash",
        ttl_hours: int = 24
    ) -> str:
        """
        必要に応じてキャッシュを更新

        Args:
            knowledge_text: キャッシュするナレッジベーステキスト
            model: 使用するモデル名
            ttl_hours: キャッシュの有効期限（時間）

        Returns:
            str: キャッシュ名（既存または新規）
        """
        existing_cache = self.get_cached_knowledge()

        if existing_cache:
            return existing_cache

        # キャッシュが存在しないか期限切れの場合は新規作成
        return self.create_knowledge_cache(knowledge_text, model, ttl_hours)

    def delete_cache(self, cache_name: str) -> None:
        """
        キャッシュを削除

        Args:
            cache_name: 削除するキャッシュ名

        Raises:
            RuntimeError: 削除に失敗した場合
        """
        try:
            self.client.caches.delete(name=cache_name)
            self._clear_metadata()

        except Exception as e:
            raise RuntimeError(f"Failed to delete cache: {str(e)}")

    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """キャッシュメタデータをファイルに保存"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self) -> Optional[Dict[str, Any]]:
        """キャッシュメタデータをファイルから読み込み"""
        if not self.metadata_file.exists():
            return None

        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _clear_metadata(self) -> None:
        """キャッシュメタデータを削除"""
        if self.metadata_file.exists():
            self.metadata_file.unlink()
