from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from cryptography.fernet import Fernet, InvalidToken

from backend.schemas.social_schema import SocialAccountType, SocialPlatform


class SocialOAuthService:
    LINKEDIN_AUTH_BASE_URL = "https://www.linkedin.com/oauth/v2/authorization"
    META_AUTH_BASE_URL = "https://www.facebook.com/v21.0/dialog/oauth"
    X_AUTH_BASE_URL = "https://x.com/i/oauth2/authorize"

    META_SCOPES = [
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_posts",
        "instagram_basic",
        "instagram_content_publish",
    ]
    X_SCOPES = ["tweet.read", "tweet.write", "users.read", "offline.access"]

    def __init__(self) -> None:
        self.fernet = Fernet(self._require_env("SOCIAL_TOKEN_ENCRYPTION_KEY").encode("utf-8"))

    def build_authorization_url(
        self,
        *,
        platform: SocialPlatform,
        account_type: SocialAccountType,
    ) -> tuple[str, str]:
        provider_config = self._get_provider_config(platform)
        resolved_redirect_uri = provider_config["redirect_uri"]

        if platform == SocialPlatform.FACEBOOK:
            state = self.generate_state(platform=platform, account_type=account_type, redirect_uri=resolved_redirect_uri)
            query = urlencode(
                {
                    "client_id": provider_config["client_id"],
                    "redirect_uri": resolved_redirect_uri,
                    "config_id": provider_config["config_id"],
                    "response_type": "code",
                    "override_default_response_type": "true",
                    "state": state,
                }
            )
        elif platform == SocialPlatform.X:
            code_verifier, code_challenge = self._generate_pkce_pair()
            state = self.generate_state(
                platform=platform,
                account_type=account_type,
                redirect_uri=resolved_redirect_uri,
                code_verifier=code_verifier,
            )
            query = urlencode(
                {
                    "response_type": "code",
                    "client_id": provider_config["client_id"],
                    "redirect_uri": resolved_redirect_uri,
                    "scope": " ".join(provider_config["scopes"]),
                    "state": state,
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256",
                }
            )
        else:
            state = self.generate_state(platform=platform, account_type=account_type, redirect_uri=resolved_redirect_uri)
            query = urlencode(
                {
                    "response_type": "code",
                    "client_id": provider_config["client_id"],
                    "redirect_uri": resolved_redirect_uri,
                    "scope": " ".join(provider_config["scopes"]),
                    "state": state,
                }
            )
        return f"{provider_config['auth_base_url']}?{query}", state

    def generate_state(
        self,
        *,
        platform: SocialPlatform,
        account_type: SocialAccountType,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> str:
        payload = {
            "platform": platform.value,
            "account_type": account_type.value,
            "redirect_uri": redirect_uri,
            "iat": datetime.now(timezone.utc).isoformat(),
            "nonce": base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8").rstrip("="),
        }
        if code_verifier is not None:
            payload["code_verifier"] = self.encrypt_secret(code_verifier)
        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(
            self.fernet._signing_key,  # type: ignore[attr-defined]
            payload_bytes,
            hashlib.sha256,
        ).digest()

        payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode("ascii")
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
        return f"{payload_b64}.{signature_b64}"

    def verify_state(self, state: str) -> dict:
        try:
            payload_b64, signature_b64 = state.split(".", 1)
        except ValueError as exc:
            raise ValueError("Invalid OAuth state format") from exc

        try:
            payload_bytes = self._b64_decode(payload_b64)
            signature = self._b64_decode(signature_b64)
        except Exception as exc:
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

        encrypted_code_verifier = payload.get("code_verifier")
        if encrypted_code_verifier:
            payload["code_verifier"] = self.decrypt_secret(encrypted_code_verifier)

        return payload

    def _generate_pkce_pair(self) -> tuple[str, str]:
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest()).decode("ascii").rstrip("=")
        return code_verifier, code_challenge

    def _b64_decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)

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

    def get_scopes(self, platform: SocialPlatform) -> list[str]:
        return self._get_scopes(platform)

    def _get_scopes(self, platform: SocialPlatform) -> list[str]:
        if platform == SocialPlatform.FACEBOOK:
            scopes = os.getenv("META_SCOPES", " ".join(self.META_SCOPES))
        elif platform == SocialPlatform.X:
            scopes = os.getenv("X_SCOPES", " ".join(self.X_SCOPES))
        else:
            scopes = os.getenv("LINKEDIN_SCOPES", "openid profile email w_member_social")
        return [scope for scope in scopes.split() if scope]

    def _get_provider_config(self, platform: SocialPlatform) -> dict[str, str | list[str]]:
        if platform == SocialPlatform.FACEBOOK:
            return {
                "auth_base_url": self.META_AUTH_BASE_URL,
                "client_id": self._require_env("META_CLIENT_ID"),
                "client_secret": self._require_env("META_CLIENT_SECRET"),
                "redirect_uri": self._require_env("META_REDIRECT_URI"),
                "config_id": self._require_env("META_CONFIG_ID"),
                "scopes": self._get_scopes(platform),
            }

        if platform == SocialPlatform.LINKEDIN:
            return {
                "auth_base_url": self.LINKEDIN_AUTH_BASE_URL,
                "client_id": self._require_env("LINKEDIN_CLIENT_ID"),
                "client_secret": self._require_env("LINKEDIN_CLIENT_SECRET"),
                "redirect_uri": self._require_env("LINKEDIN_REDIRECT_URI"),
                "scopes": self._get_scopes(platform),
            }

        if platform == SocialPlatform.X:
            return {
                "auth_base_url": self.X_AUTH_BASE_URL,
                "client_id": self._require_env("X_CLIENT_ID"),
                "client_secret": self._require_env("X_CLIENT_SECRET"),
                "redirect_uri": self._require_env("X_REDIRECT_URI"),
                "scopes": self._get_scopes(platform),
            }

        raise ValueError(f"Unsupported social platform: {platform.value}")