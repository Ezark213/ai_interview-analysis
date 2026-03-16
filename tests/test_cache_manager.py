"""コンテキストキャッシュ管理のテスト"""
import pytest
import time
import json
from pathlib import Path
from src.cache_manager import CacheManager


class TestCacheManager:
    """コンテキストキャッシュ管理機能のテスト"""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """一時キャッシュディレクトリ"""
        return tmp_path / "test_cache"

    @pytest.fixture
    def cache_manager(self, cache_dir):
        """CacheManagerインスタンス（テスト用API key）"""
        return CacheManager(api_key="test_api_key", cache_dir=str(cache_dir))

    @pytest.fixture
    def sample_knowledge(self):
        """サンプルナレッジベース"""
        return """
        # 行動心理学の評価基準

        ## 1. コミュニケーション能力
        - 明瞭な発話
        - 適切なアイコンタクト
        """

    def test_init_creates_cache_dir(self, cache_dir):
        """初期化時にキャッシュディレクトリを作成"""
        manager = CacheManager(api_key="test_key", cache_dir=str(cache_dir))

        assert cache_dir.exists()
        assert (cache_dir / "cache_metadata.json").parent.exists()

    def test_create_knowledge_cache_mock(self, cache_manager, sample_knowledge, mocker):
        """ナレッジベースのキャッシュ作成（モック）"""
        # Gemini APIをモック化
        mock_cache = mocker.MagicMock()
        mock_cache.name = "test_cache_12345"

        mock_client = mocker.MagicMock()
        mock_client.caches.create.return_value = mock_cache
        cache_manager._client = mock_client

        # 実行
        cache_name = cache_manager.create_knowledge_cache(
            knowledge_text=sample_knowledge,
            model="gemini-2.5-flash",
            ttl_hours=24
        )

        # 検証
        assert cache_name == "test_cache_12345"
        mock_client.caches.create.assert_called_once()

        # メタデータが保存されているか確認
        metadata_file = cache_manager.metadata_file
        assert metadata_file.exists()

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            assert metadata["cache_name"] == "test_cache_12345"
            assert metadata["model"] == "gemini-2.5-flash"
            assert metadata["ttl_hours"] == 24

    def test_get_cached_knowledge_valid(self, cache_manager):
        """有効なキャッシュが存在する場合"""
        # メタデータを手動で作成（有効期限内）
        metadata = {
            "cache_name": "test_cache_12345",
            "model": "gemini-2.5-flash",
            "created_at": time.time(),
            "expires_at": time.time() + 3600,  # 1時間後
            "ttl_hours": 1
        }
        cache_manager._save_metadata(metadata)

        # 実行
        cache_name = cache_manager.get_cached_knowledge()

        # 検証
        assert cache_name == "test_cache_12345"

    def test_get_cached_knowledge_expired(self, cache_manager):
        """期限切れのキャッシュの場合"""
        # メタデータを手動で作成（期限切れ）
        metadata = {
            "cache_name": "test_cache_12345",
            "model": "gemini-2.5-flash",
            "created_at": time.time() - 7200,  # 2時間前
            "expires_at": time.time() - 3600,  # 1時間前（期限切れ）
            "ttl_hours": 1
        }
        cache_manager._save_metadata(metadata)

        # 実行
        cache_name = cache_manager.get_cached_knowledge()

        # 検証
        assert cache_name is None

        # メタデータが削除されているか確認
        assert not cache_manager.metadata_file.exists()

    def test_get_cached_knowledge_no_metadata(self, cache_manager):
        """メタデータが存在しない場合"""
        cache_name = cache_manager.get_cached_knowledge()

        assert cache_name is None

    def test_refresh_cache_if_needed_existing(self, cache_manager, sample_knowledge):
        """既存のキャッシュがある場合（更新不要）"""
        # 有効なメタデータを作成
        metadata = {
            "cache_name": "existing_cache_12345",
            "model": "gemini-2.5-flash",
            "created_at": time.time(),
            "expires_at": time.time() + 3600,
            "ttl_hours": 1
        }
        cache_manager._save_metadata(metadata)

        # 実行
        cache_name = cache_manager.refresh_cache_if_needed(sample_knowledge)

        # 検証: 既存のキャッシュ名が返される
        assert cache_name == "existing_cache_12345"

    def test_refresh_cache_if_needed_create_new(self, cache_manager, sample_knowledge, mocker):
        """キャッシュが存在しない場合（新規作成）"""
        # Gemini APIをモック化
        mock_cache = mocker.MagicMock()
        mock_cache.name = "new_cache_67890"

        mock_client = mocker.MagicMock()
        mock_client.caches.create.return_value = mock_cache
        cache_manager._client = mock_client

        # 実行
        cache_name = cache_manager.refresh_cache_if_needed(sample_knowledge)

        # 検証: 新しいキャッシュが作成される
        assert cache_name == "new_cache_67890"
        mock_client.caches.create.assert_called_once()

    def test_generate_content_with_cache_mock(self, cache_manager, mocker):
        """キャッシュを使用したコンテンツ生成（モック）"""
        # Gemini APIをモック化
        mock_response = mocker.MagicMock()
        mock_response.text = '{"overall_risk_score": 85}'

        mock_client = mocker.MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        cache_manager._client = mock_client

        # 動画ファイルをモック
        mock_video = mocker.MagicMock()

        # 実行
        response = cache_manager.generate_content_with_cache(
            cache_name="test_cache_12345",
            prompt="評価してください",
            video_file=mock_video
        )

        # 検証
        assert response.text == '{"overall_risk_score": 85}'
        mock_client.models.generate_content.assert_called_once()

    def test_delete_cache_mock(self, cache_manager, mocker):
        """キャッシュの削除（モック）"""
        # メタデータを作成
        metadata = {
            "cache_name": "test_cache_12345",
            "model": "gemini-2.5-flash",
            "created_at": time.time(),
            "expires_at": time.time() + 3600,
            "ttl_hours": 1
        }
        cache_manager._save_metadata(metadata)

        # Gemini APIをモック化
        mock_client = mocker.MagicMock()
        cache_manager._client = mock_client

        # 実行
        cache_manager.delete_cache("test_cache_12345")

        # 検証
        mock_client.caches.delete.assert_called_once_with(name="test_cache_12345")

        # メタデータが削除されているか確認
        assert not cache_manager.metadata_file.exists()

    def test_save_and_load_metadata(self, cache_manager):
        """メタデータの保存と読み込み"""
        metadata = {
            "cache_name": "test_cache_12345",
            "model": "gemini-2.5-flash",
            "created_at": time.time(),
            "expires_at": time.time() + 3600,
            "ttl_hours": 1
        }

        # 保存
        cache_manager._save_metadata(metadata)

        # 読み込み
        loaded_metadata = cache_manager._load_metadata()

        # 検証
        assert loaded_metadata["cache_name"] == metadata["cache_name"]
        assert loaded_metadata["model"] == metadata["model"]

    def test_clear_metadata(self, cache_manager):
        """メタデータの削除"""
        metadata = {
            "cache_name": "test_cache_12345",
            "model": "gemini-2.5-flash"
        }

        # 保存
        cache_manager._save_metadata(metadata)
        assert cache_manager.metadata_file.exists()

        # 削除
        cache_manager._clear_metadata()

        # 検証
        assert not cache_manager.metadata_file.exists()
