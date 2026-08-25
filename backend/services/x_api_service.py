from __future__ import annotations

import base64
import os
from typing import Any

import httpx


class XAPIService:
    TOKEN_URL = "https://api.x.com/2/oauth2/token"
    API_BASE_URL = "https://api.x.com/2"

    def __init__(self) -> None:
        self.client_id = self._require_env("X_CLIENT_ID")
        self.client_secret = self._require_env("X_CLIENT_SECRET")
        self.redirect_uri = self._require_env("X_REDIRECT_URI")

    def exchange_code_for_token(self, code: str, code_verifier: str) -> dict[str, Any]:
        headers = {
            "Authorization": self._build_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": code_verifier,
        }
        response = self._post_or_raise(self.TOKEN_URL, headers=headers, data=data)
        return response.json() if response.content else {}

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        headers = {
            "Authorization": self._build_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
        }
        response = self._post_or_raise(self.TOKEN_URL, headers=headers, data=data)
        return response.json() if response.content else {}

    def get_authenticated_user(self, access_token: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = httpx.get(f"{self.API_BASE_URL}/users/me", headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def create_post(self, access_token: str, text: str) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = self._post_or_raise(
            f"{self.API_BASE_URL}/tweets",
            headers=headers,
            json={"text": text},
        )
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.content else {},
        }

    def _build_basic_auth_header(self) -> str:
        auth_value = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        encoded = base64.b64encode(auth_value).decode("ascii")
        return f"Basic {encoded}"

    def _require_env(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} is not set")
        return value

    def _post_or_raise(
        self,
        url: str,
        *,
        headers: dict[str, str],
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        response = httpx.post(url, headers=headers, data=data, json=json, timeout=30.0)
        if response.is_error:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise ValueError(f"X API error ({response.status_code}) at {url}: {detail}")
        return response
