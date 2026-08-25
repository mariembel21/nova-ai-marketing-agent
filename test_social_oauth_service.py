from __future__ import annotations

import base64
import hashlib
import os
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend.schemas.social_schema import SocialAccountType, SocialPlatform
from backend.services.social_oauth_service import SocialOAuthService


class SocialOAuthServiceTests(unittest.TestCase):
    @staticmethod
    def _env() -> dict[str, str]:
        return {
            "SOCIAL_TOKEN_ENCRYPTION_KEY": Fernet.generate_key().decode("utf-8"),
            "LINKEDIN_CLIENT_ID": "linkedin-client",
            "LINKEDIN_CLIENT_SECRET": "linkedin-secret",
            "LINKEDIN_REDIRECT_URI": "http://localhost:8000/social/linkedin/auth/callback",
            "META_CLIENT_ID": "meta-client",
            "META_CLIENT_SECRET": "meta-secret",
            "META_REDIRECT_URI": "http://localhost:8000/social/facebook/auth/callback",
            "META_CONFIG_ID": "meta-config",
            "X_CLIENT_ID": "x-client",
            "X_CLIENT_SECRET": "x-secret",
            "X_REDIRECT_URI": "http://localhost:8000/social/x/auth/callback",
        }

    def test_generate_and_verify_state_round_trips_code_verifier(self) -> None:
        with patch.dict(os.environ, self._env(), clear=False):
            service = SocialOAuthService()
            state = service.generate_state(
                platform=SocialPlatform.X,
                account_type=SocialAccountType.PERSONAL,
                redirect_uri="http://localhost:8000/social/x/auth/callback",
                code_verifier="pkce-verifier-value",
            )

            payload = service.verify_state(state)

        self.assertEqual(payload["platform"], SocialPlatform.X.value)
        self.assertEqual(payload["account_type"], SocialAccountType.PERSONAL.value)
        self.assertEqual(payload["code_verifier"], "pkce-verifier-value")

    def test_generate_pkce_pair_matches_s256_transformation(self) -> None:
        with patch.dict(os.environ, self._env(), clear=False):
            service = SocialOAuthService()
            code_verifier, code_challenge = service._generate_pkce_pair()

        expected_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest()).decode("ascii").rstrip("=")

        self.assertGreaterEqual(len(code_verifier), 43)
        self.assertLessEqual(len(code_verifier), 128)
        self.assertEqual(code_challenge, expected_challenge)
        self.assertNotIn("=", code_challenge)


if __name__ == "__main__":
    unittest.main()
