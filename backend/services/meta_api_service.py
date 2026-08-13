from __future__ import annotations

import os
import time
from typing import Any

import httpx


class MetaAPIService:
    GRAPH_BASE_URL = "https://graph.facebook.com/v21.0"
    CONTAINER_POLL_INTERVAL_SECONDS = 5
    CONTAINER_POLL_MAX_ATTEMPTS = 12

    def __init__(self) -> None:
        self.client_id = self._require_env("META_CLIENT_ID")
        self.client_secret = self._require_env("META_CLIENT_SECRET")
        self.redirect_uri = self._require_env("META_REDIRECT_URI")

    def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        response = httpx.get(f"{self.GRAPH_BASE_URL}/oauth/access_token", params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def get_managed_pages(self, access_token: str) -> list[dict[str, Any]]:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "fields": "id,name,access_token,instagram_business_account{id,username}",
            "limit": 100,
        }

        pages: list[dict[str, Any]] = []
        next_url: str | None = f"{self.GRAPH_BASE_URL}/me/accounts"
        next_params: dict[str, Any] | None = params

        while next_url:
            response = httpx.get(next_url, headers=headers, params=next_params, timeout=30.0)
            response.raise_for_status()
            payload = response.json()
            pages.extend(payload.get("data", []))

            paging = payload.get("paging") or {}
            next_url = paging.get("next")
            next_params = None

        return pages

    def create_facebook_post(self, access_token: str, page_id: str, text: str, media_url: str | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}

        if media_url:
            payload: dict[str, Any] = {"caption": text, "url": media_url}
            endpoint = f"{self.GRAPH_BASE_URL}/{page_id}/photos"
        else:
            payload = {"message": text}
            endpoint = f"{self.GRAPH_BASE_URL}/{page_id}/feed"

        response = httpx.post(endpoint, headers=headers, data=payload, timeout=30.0)
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.content else {},
        }
    def create_instagram_post(
        self,
        access_token: str,
        ig_business_id: str,
        text: str,
        media_url: str,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}

        container_payload: dict[str, Any] = {"caption": text}

        if self._looks_like_video(media_url):
            container_payload["video_url"] = media_url
            container_payload["media_type"] = "VIDEO"
        else:
            container_payload["image_url"] = media_url

        container_response = self._post_or_raise(
            f"{self.GRAPH_BASE_URL}/{ig_business_id}/media",
            headers=headers,
            data=container_payload,
        )

        container_body = (
            container_response.json()
            if container_response.content
            else {}
        )

        container_id = container_body.get("id")

        if not container_id:
            raise ValueError("Instagram media container id was not returned")

        self._wait_for_container_ready(headers, container_id)

        publish_response = self._post_or_raise(
            f"{self.GRAPH_BASE_URL}/{ig_business_id}/media_publish",
            headers=headers,
            data={"creation_id": container_id},
        )

        return {
            "container": {
                "status_code": container_response.status_code,
                "headers": dict(container_response.headers),
                "body": container_body,
            },
            "publish": {
                "status_code": publish_response.status_code,
                "headers": dict(publish_response.headers),
                "body": (
                    publish_response.json()
                    if publish_response.content
                    else {}
                ),
            },
        }

    def _wait_for_container_ready(self, headers: dict[str, str], container_id: str) -> None:
        for _ in range(self.CONTAINER_POLL_MAX_ATTEMPTS):
            status_response = httpx.get(
                f"{self.GRAPH_BASE_URL}/{container_id}",
                headers=headers,
                params={"fields": "status_code"},
                timeout=30.0,
            )
            status_response.raise_for_status()
            status_code = (status_response.json() or {}).get("status_code")

            if status_code == "FINISHED":
                return
            if status_code in ("ERROR", "EXPIRED"):
                raise ValueError(f"Instagram media container failed with status: {status_code}")

            time.sleep(self.CONTAINER_POLL_INTERVAL_SECONDS)

        raise TimeoutError("Instagram media container did not finish processing in time")

    def _looks_like_video(self, media_url: str) -> bool:
        lower_url = media_url.lower()
        return lower_url.endswith((".mp4", ".mov", ".m4v", ".webm", ".avi"))

    def _require_env(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} is not set")
        return value

    def _post_or_raise(self, url: str, headers: dict[str, str], data: dict[str, Any]) -> httpx.Response:
        response = httpx.post(url, headers=headers, data=data, timeout=30.0)
        if response.is_error:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise ValueError(f"Meta API error ({response.status_code}) at {url}: {detail}")
        return response