from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.models.social_account import SocialAccount
from backend.models.social_publish_record import SocialPublishRecord
from backend.schemas.social_schema import ConnectionStatusResponse, PublishPostRequest, PublishPostResponse, SocialConnectionStatus, SocialPlatform
from backend.services.meta_api_service import MetaAPIService
from backend.services.linkedin_api_service import LinkedInAPIService
from backend.services.social_oauth_service import SocialOAuthService
from backend.services.x_api_service import XAPIService


class SocialPublishService:
    def __init__(
        self,
        db: Session,
        *,
        oauth_service: SocialOAuthService | None = None,
        linkedin_api_service: LinkedInAPIService | None = None,
        meta_api_service: MetaAPIService | None = None,
        x_api_service: XAPIService | None = None,
    ) -> None:
        self.db = db
        self.oauth_service = oauth_service or SocialOAuthService()
        self.linkedin_api_service = linkedin_api_service
        self.meta_api_service = meta_api_service
        self.x_api_service = x_api_service

    def get_connection_status(self, platform: SocialPlatform, social_account_id: str | None = None) -> ConnectionStatusResponse:
        query = self.db.query(SocialAccount).filter(SocialAccount.platform == platform.value)
        if social_account_id:
            query = query.filter(SocialAccount.account_uuid == social_account_id)

        account = query.order_by(SocialAccount.updated_at.desc()).first()
        if not account:
            return ConnectionStatusResponse(
                platform=platform,
                status=SocialConnectionStatus.DISCONNECTED,
                account_id=None,
                account_name=None,
                external_id=None,
                expires_at=None,
                scopes=[],
            )

        expires_at = account.expires_at
        connection_status = SocialConnectionStatus.CONNECTED
        if expires_at and expires_at <= datetime.now(timezone.utc):
            connection_status = SocialConnectionStatus.EXPIRED

        return ConnectionStatusResponse(
            platform=platform,
            status=connection_status,
            account_id=str(account.account_uuid),
            account_name=account.account_name,
            external_id=account.external_id,
            expires_at=expires_at,
            scopes=[scope for scope in account.scopes.split() if scope],
        )

    def store_linkedin_account(
        self,
        *,
        platform: SocialPlatform,
        account_type: str,
        external_id: str,
        account_name: str,
        access_token: str,
        refresh_token: str | None,
        expires_in: int | None,
        scopes: list[str],
    ) -> SocialAccount:
        return self._store_account(
            platform=platform,
            account_type=account_type,
            external_id=external_id,
            account_name=account_name,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scopes=scopes,
        )

    def store_x_account(
        self,
        *,
        platform: SocialPlatform,
        account_type: str,
        external_id: str,
        account_name: str,
        access_token: str,
        refresh_token: str | None,
        expires_in: int | None,
        scopes: list[str],
    ) -> SocialAccount:
        return self._store_account(
            platform=platform,
            account_type=account_type,
            external_id=external_id,
            account_name=account_name,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scopes=scopes,
        )

    def store_meta_accounts(
        self,
        *,
        managed_pages: list[dict],
        account_type: str,
        access_token: str,
        expires_in: int | None,
        scopes: list[str],
    ) -> list[SocialAccount]:
        stored_accounts: list[SocialAccount] = []
        for page in managed_pages:
            page_access_token = page.get("access_token")
            if not page_access_token:
                continue

            stored_accounts.append(
                self._store_account(
                    platform=SocialPlatform.FACEBOOK,
                    account_type=account_type,
                    external_id=str(page["id"]),
                    account_name=page.get("name") or "Facebook Page",
                    access_token=page_access_token,
                    refresh_token=None,
                    expires_in=expires_in,
                    scopes=scopes,
                )
            )

            instagram_account = page.get("instagram_business_account") or {}
            instagram_external_id = instagram_account.get("id")
            if instagram_external_id:
                stored_accounts.append(
                    self._store_account(
                        platform=SocialPlatform.INSTAGRAM,
                        account_type=account_type,
                        external_id=str(instagram_external_id),
                        account_name=instagram_account.get("username") or page.get("name") or "Instagram Account",
                        access_token=page_access_token,
                        refresh_token=None,
                        expires_in=expires_in,
                        scopes=scopes,
                    )
                )

        return stored_accounts

    def publish_post(self, request: PublishPostRequest) -> PublishPostResponse:
        account = self.db.query(SocialAccount).filter(SocialAccount.account_uuid == request.social_account_id).first()
        if not account:
            raise ValueError("Social account not found")
        if account.platform != request.platform.value:
            raise ValueError("Social account platform does not match publish request platform")

        record = SocialPublishRecord(
            record_uuid=str(uuid.uuid4()),
            social_account_id=account.id,
            platform=request.platform.value,
            status="pending",
            text=request.text,
            hashtags=json.dumps(request.hashtags),
            media_url=request.media_url,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        try:
            access_token = self.oauth_service.decrypt_secret(account.encrypted_access_token)
            refresh_token = self.oauth_service.decrypt_secret(account.encrypted_refresh_token) if account.encrypted_refresh_token else None

            if request.platform in (SocialPlatform.LINKEDIN, SocialPlatform.X) and account.expires_at and account.expires_at <= datetime.now(timezone.utc):
                if not refresh_token:
                    raise ValueError("Access token expired and refresh token is unavailable")
                api_service = self._get_x_api_service() if request.platform == SocialPlatform.X else self._get_linkedin_api_service()
                refreshed = api_service.refresh_access_token(refresh_token)
                access_token = refreshed["access_token"]
                account.encrypted_access_token = self.oauth_service.encrypt_secret(access_token)
                if refreshed.get("refresh_token"):
                    account.encrypted_refresh_token = self.oauth_service.encrypt_secret(refreshed["refresh_token"])
                expires_in = refreshed.get("expires_in")
                if expires_in:
                    account.expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                self.db.add(account)
                self.db.commit()
                self.db.refresh(account)

            publication_id: str | None = None
            if request.platform == SocialPlatform.LINKEDIN:
                post_response = self._get_linkedin_api_service().create_post(
                    access_token,
                    author_urn=f"urn:li:person:{account.external_id}",
                    text=request.text,
                    media_url=request.media_url,
                )
                publication_id = post_response.get("body", {}).get("id") or post_response.get("headers", {}).get("x-restli-id")
            elif request.platform == SocialPlatform.FACEBOOK:
                post_response = self._get_meta_api_service().create_facebook_post(
                    access_token,
                    page_id=account.external_id,
                    text=request.text,
                    media_url=request.media_url,
                )
                publication_id = post_response.get("body", {}).get("id") or post_response.get("body", {}).get("post_id")
            elif request.platform == SocialPlatform.INSTAGRAM:
                if not request.media_url:
                    raise ValueError("Instagram publishing requires media_url")
                post_response = self._get_meta_api_service().create_instagram_post(
                    access_token,
                    ig_business_id=account.external_id,
                    text=request.text,
                    media_url=request.media_url,
                )
                publication_id = (
                    post_response.get("publish", {}).get("body", {}).get("id")
                    or post_response.get("publish", {}).get("body", {}).get("media_id")
                    or post_response.get("container", {}).get("body", {}).get("id")
                )
            elif request.platform == SocialPlatform.X:
                post_response = self._get_x_api_service().create_post(access_token, request.text)
                publication_id = post_response.get("body", {}).get("data", {}).get("id")
            else:
                raise ValueError(f"Unsupported social platform: {request.platform.value}")

            record.status = "published"
            record.platform_post_id = publication_id
            record.error_details = None
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return PublishPostResponse(
                publish_record_id=str(record.record_uuid),
                platform=request.platform,
                status=record.status,
                platform_post_id=publication_id,
                error_details=None,
            )
        except Exception as exc:
            record.status = "failed"
            record.error_details = str(exc)
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return PublishPostResponse(
                publish_record_id=str(record.record_uuid),
                platform=request.platform,
                status=record.status,
                platform_post_id=record.platform_post_id,
                error_details=record.error_details,
            )

    def _get_meta_api_service(self) -> MetaAPIService:
        if self.meta_api_service is None:
            self.meta_api_service = MetaAPIService()
        return self.meta_api_service

    def _get_linkedin_api_service(self) -> LinkedInAPIService:
        if self.linkedin_api_service is None:
            self.linkedin_api_service = LinkedInAPIService()
        return self.linkedin_api_service

    def _get_x_api_service(self) -> XAPIService:
        if self.x_api_service is None:
            self.x_api_service = XAPIService()
        return self.x_api_service

    def _store_account(
        self,
        *,
        platform: SocialPlatform,
        account_type: str,
        external_id: str,
        account_name: str,
        access_token: str,
        refresh_token: str | None,
        expires_in: int | None,
        scopes: list[str],
    ) -> SocialAccount:
        expires_at = None
        if expires_in is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        existing = (
            self.db.query(SocialAccount)
            .filter(SocialAccount.platform == platform.value, SocialAccount.external_id == external_id)
            .first()
        )
        if existing:
            existing.account_type = account_type
            existing.account_name = account_name
            existing.encrypted_access_token = self.oauth_service.encrypt_secret(access_token)
            existing.encrypted_refresh_token = self.oauth_service.encrypt_secret(refresh_token) if refresh_token else None
            existing.expires_at = expires_at
            existing.scopes = " ".join(scopes)
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        account = SocialAccount(
            account_uuid=str(uuid.uuid4()),
            platform=platform.value,
            account_type=account_type,
            external_id=external_id,
            account_name=account_name,
            encrypted_access_token=self.oauth_service.encrypt_secret(access_token),
            encrypted_refresh_token=self.oauth_service.encrypt_secret(refresh_token) if refresh_token else None,
            expires_at=expires_at,
            scopes=" ".join(scopes),
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account