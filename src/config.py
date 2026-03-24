"""アプリケーション設定モジュール

APIキーの読み込みなど、環境に依存する設定を管理する。
ローカル環境（.env）とStreamlit Cloud（Secrets）の両方に対応。
"""
import os

import streamlit as st
from dotenv import load_dotenv


def load_api_keys() -> tuple[str, str, str]:
    """
    APIキーを読み込む（ローカル.env優先、なければStreamlit Secrets）

    優先順位:
        1. 環境変数（.envファイルから読み込み）
        2. Streamlit Secrets（クラウド環境）

    Returns:
        tuple: (gemini_key_1, gemini_key_2, openai_key)
    """
    # 1. まず.envから読み込み
    load_dotenv()
    key1 = os.getenv("GEMINI_API_KEY_1", "")
    key2 = os.getenv("GEMINI_API_KEY_2", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    # 2. .envにない場合、Streamlit Secretsから読み込み
    if not key1:
        try:
            key1 = st.secrets.get("GEMINI_API_KEY_1", "")
            key2 = st.secrets.get("GEMINI_API_KEY_2", "")
        except Exception:
            pass

    if not openai_key:
        try:
            openai_key = st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            pass

    return key1, key2, openai_key
