from __future__ import annotations
import os

from typing import Any
from urllib.parse import urlencode

import httpx


class LinkedInAPIService:
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    OPENID_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"

    def __init__(self) -> None:
        self.client_id = self._require_env("LINKEDIN_CLIENT_ID")
        self.client_secret = self._require_env("LINKEDIN_CLIENT_SECRET")
        self.redirect_uri = self._require_env("LINKEDIN_REDIRECT_URI")

    def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }
        response = httpx.post(self.TOKEN_URL, data=data, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = httpx.post(self.TOKEN_URL, data=data, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def get_user_info(self, access_token: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = httpx.get(self.OPENID_USERINFO_URL, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def create_post(self, access_token: str, *, author_urn: str, text: str, media_url: str | None = None) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE" if not media_url else "ARTICLE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
            },
        }
        if media_url:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "originalUrl": media_url,
                }
            ]

        response = httpx.post(self.POSTS_URL, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.content else {},
        }

    def _require_env(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} is not set")
        return value
