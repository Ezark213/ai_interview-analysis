"""APIキー読み込みのテスト

.env（ローカル）とStreamlit Secrets（クラウド）の両対応テスト。
優先順位: .env > Streamlit Secrets
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from src.config import load_api_keys


class TestLoadApiKeys:
    """load_api_keys() のテスト"""

    def test_load_api_key_from_env(self, monkeypatch):
        """環境変数からAPIキーを読み込める"""
        monkeypatch.setenv("GEMINI_API_KEY_1", "env-key-1")
        monkeypatch.setenv("GEMINI_API_KEY_2", "env-key-2")

        key1, key2 = load_api_keys()
        assert key1 == "env-key-1"
        assert key2 == "env-key-2"

    def test_load_api_key_from_streamlit_secrets(self, monkeypatch):
        """Streamlit secretsからAPIキーを読み込める（.envにキーがない場合）"""
        # 環境変数をクリア
        monkeypatch.delenv("GEMINI_API_KEY_1", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY_2", raising=False)

        # Streamlit secretsをモック
        mock_secrets = MagicMock()
        mock_secrets.get.side_effect = lambda key, default="": {
            "GEMINI_API_KEY_1": "secrets-key-1",
            "GEMINI_API_KEY_2": "secrets-key-2",
        }.get(key, default)

        with patch("src.config.st") as mock_st, \
             patch("src.config.load_dotenv"):  # .envからの再読み込みを防止
            mock_st.secrets = mock_secrets
            key1, key2 = load_api_keys()

        assert key1 == "secrets-key-1"
        assert key2 == "secrets-key-2"

    def test_env_takes_precedence_over_secrets(self, monkeypatch):
        """ローカル(.env)とクラウド(secrets)の両方がある場合、.envが優先"""
        monkeypatch.setenv("GEMINI_API_KEY_1", "env-key-1")
        monkeypatch.setenv("GEMINI_API_KEY_2", "env-key-2")

        # Streamlit secretsもモック
        mock_secrets = MagicMock()
        mock_secrets.get.side_effect = lambda key, default="": {
            "GEMINI_API_KEY_1": "secrets-key-1",
            "GEMINI_API_KEY_2": "secrets-key-2",
        }.get(key, default)

        with patch("src.config.st") as mock_st:
            mock_st.secrets = mock_secrets
            key1, key2 = load_api_keys()

        # .envの値が優先される
        assert key1 == "env-key-1"
        assert key2 == "env-key-2"
