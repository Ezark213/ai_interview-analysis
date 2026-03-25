"""アプリケーション設定モジュール

APIキーの読み込みなど、環境に依存する設定を管理する。
ローカル環境（.env）とStreamlit Cloud（Secrets）の両方に対応。
"""
import os

import streamlit as st
from dotenv import load_dotenv


def load_api_keys() -> tuple[str, str, str]:
    """
    APIキーを読み込む（session_state優先 → .env → Streamlit Secrets）

    優先順位:
        1. session_state（UI入力、ブラウザリロードで消去）
        2. 環境変数（.envファイルから読み込み）
        3. Streamlit Secrets（クラウド環境）

    Returns:
        tuple: (gemini_key_1, gemini_key_2, openai_key)
    """
    # 1. session_state（UI入力値）を最優先で参照
    key1 = st.session_state.get("gemini_api_key_1", "")
    key2 = st.session_state.get("gemini_api_key_2", "")
    openai_key = st.session_state.get("openai_api_key", "")

    # 2. session_stateにない場合、.envから読み込み
    if not key1:
        load_dotenv()
        key1 = os.getenv("GEMINI_API_KEY_1", "")
        key2 = os.getenv("GEMINI_API_KEY_2", "") if not key2 else key2
        openai_key = os.getenv("OPENAI_API_KEY", "") if not openai_key else openai_key

    # 3. .envにもない場合、Streamlit Secretsから読み込み
    if not key1:
        try:
            key1 = st.secrets.get("GEMINI_API_KEY_1", "")
            key2 = st.secrets.get("GEMINI_API_KEY_2", "") if not key2 else key2
        except Exception:
            pass

    if not openai_key:
        try:
            openai_key = st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            pass

    return key1, key2, openai_key


def get_key_source(key_name: str) -> str:
    """APIキーの読み込み元を判定する。

    Returns:
        "ui": session_stateから, "env": .env/環境変数から,
        "secrets": Streamlit Secretsから, "": 未設定
    """
    if st.session_state.get(key_name, ""):
        return "ui"

    load_dotenv()
    env_map = {
        "gemini_api_key_1": "GEMINI_API_KEY_1",
        "gemini_api_key_2": "GEMINI_API_KEY_2",
        "openai_api_key": "OPENAI_API_KEY",
    }
    env_var = env_map.get(key_name, "")
    if env_var and os.getenv(env_var, ""):
        return "env"

    secret_key = env_var
    if secret_key:
        try:
            if st.secrets.get(secret_key, ""):
                return "secrets"
        except Exception:
            pass

    return ""
