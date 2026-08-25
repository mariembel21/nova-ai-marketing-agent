from __future__ import annotations

import base64
import os
import unittest
from unittest.mock import MagicMock, patch

from backend.services.x_api_service import XAPIService


class XAPIServiceTests(unittest.TestCase):
    @staticmethod
    def _env() -> dict[str, str]:
        return {
            "X_CLIENT_ID": "x-client-id",
            "X_CLIENT_SECRET": "x-client-secret",
            "X_REDIRECT_URI": "http://localhost:8000/social/x/auth/callback",
        }

    def test_exchange_code_for_token_uses_basic_auth_and_expected_form_body(self) -> None:
        with patch.dict(os.environ, self._env(), clear=False):
            service = XAPIService()

            response = MagicMock()
            response.is_error = False
            response.content = b'{"access_token":"token"}'
            response.json.return_value = {"access_token": "token"}

            with patch("backend.services.x_api_service.httpx.post", return_value=response) as mock_post:
                result = service.exchange_code_for_token("auth-code", "pkce-verifier")

        self.assertEqual(result, {"access_token": "token"})
        mock_post.assert_called_once()

        called_url = mock_post.call_args.args[0]
        called_kwargs = mock_post.call_args.kwargs
        expected_auth = "Basic " + base64.b64encode(b"x-client-id:x-client-secret").decode("ascii")

        self.assertEqual(called_url, XAPIService.TOKEN_URL)
        self.assertEqual(called_kwargs["headers"]["Authorization"], expected_auth)
        self.assertEqual(called_kwargs["headers"]["Content-Type"], "application/x-www-form-urlencoded")
        self.assertEqual(
            called_kwargs["data"],
            {
                "grant_type": "authorization_code",
                "code": "auth-code",
                "redirect_uri": "http://localhost:8000/social/x/auth/callback",
                "client_id": "x-client-id",
                "code_verifier": "pkce-verifier",
            },
        )


if __name__ == "__main__":
    unittest.main()
