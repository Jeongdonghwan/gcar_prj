"""Kakao OAuth (Kakao Sync) helpers. Used by Sprint 3.

Never persist access tokens. Only `kakao_id` is stored against the User row.
"""
import secrets
from urllib.parse import urlencode

import requests
from flask import current_app


AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"
PROFILE_URL = "https://kapi.kakao.com/v2/user/me"


def new_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(state: str) -> str:
    params = {
        "client_id": current_app.config["KAKAO_REST_API_KEY"],
        "redirect_uri": current_app.config["KAKAO_REDIRECT_URI"],
        "response_type": "code",
        "state": state,
        "scope": "account_email profile_nickname",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    payload = {
        "grant_type": "authorization_code",
        "client_id": current_app.config["KAKAO_REST_API_KEY"],
        "redirect_uri": current_app.config["KAKAO_REDIRECT_URI"],
        "code": code,
    }
    resp = requests.post(TOKEN_URL, data=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_profile(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(PROFILE_URL, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()
