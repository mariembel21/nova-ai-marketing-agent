from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from cryptography.fernet import Fernet, InvalidToken

from backend.schemas.social_schema import SocialAccountType, SocialPlatform


class SocialOAuthService:
    AUTH_BASE_URL = "https://www.linkedin.com/oauth/v2/authorization"

    def __init__(self) -> None:
        self.client_id = self._require_env("LINKEDIN_CLIENT_ID")
        self.client_secret = self._require_env("LINKEDIN_CLIENT_SECRET")
        self.default_redirect_uri = self._require_env("LINKEDIN_REDIRECT_URI")
        self.scopes = self._get_scopes()
        self.fernet = Fernet(self._require_env("SOCIAL_TOKEN_ENCRYPTION_KEY").encode("utf-8"))

    def build_authorization_url(
        self,
        *,
        platform: SocialPlatform,
        account_type: SocialAccountType,
        redirect_uri: str | None = None,
    ) -> tuple[str, str]:
        if platform != SocialPlatform.LINKEDIN:
            raise ValueError("Only LinkedIn is supported for this flow")

        resolved_redirect_uri = redirect_uri or self.default_redirect_uri
        state = self.generate_state(platform=platform, account_type=account_type, redirect_uri=resolved_redirect_uri)
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": resolved_redirect_uri,
                "scope": " ".join(self.scopes),
                "state": state,
            }
        )
        return f"{self.AUTH_BASE_URL}?{query}", state

    def generate_state(self, *, platform: SocialPlatform, account_type: SocialAccountType, redirect_uri: str) -> str:
        payload = {
            "platform": platform.value,
            "account_type": account_type.value,
            "redirect_uri": redirect_uri,
            "iat": datetime.now(timezone.utc).isoformat(),
            "nonce": base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8").rstrip("="),
        }
        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(
            self.fernet._signing_key,  # type: ignore[attr-defined]
            payload_bytes,
            hashlib.sha256,
        ).digest()
        token = base64.urlsafe_b64encode(payload_bytes + b"." + signature).decode("utf-8")
        return token

    def verify_state(self, state: str) -> dict:
        try:
            decoded = base64.urlsafe_b64decode(state.encode("utf-8"))
            payload_bytes, signature = decoded.rsplit(b".", 1)
        except ValueError as exc:
            raise ValueError("Invalid OAuth state format") from exc

        expected_signature = hmac.new(
            self.fernet._signing_key,  # type: ignore[attr-defined]
            payload_bytes,
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid OAuth state signature")

        payload = json.loads(payload_bytes.decode("utf-8"))
        issued_at = datetime.fromisoformat(payload["iat"])
        if datetime.now(timezone.utc) - issued_at > timedelta(minutes=10):
            raise ValueError("OAuth state has expired")

        return payload

    def encrypt_secret(self, value: str) -> str:
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt_secret(self, value: str) -> str:
        try:
            return self.fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Unable to decrypt stored token") from exc

    def _require_env(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} is not set")
        return value

    def _get_scopes(self) -> list[str]:
        scopes = os.getenv("LINKEDIN_SCOPES", "openid profile email w_member_social")
        return [scope for scope in scopes.split() if scope]
