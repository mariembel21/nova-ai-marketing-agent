from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.models.social_account import SocialAccount
from backend.models.social_publish_record import SocialPublishRecord
from backend.schemas.social_schema import ConnectionStatusResponse, PublishPostRequest, PublishPostResponse, SocialConnectionStatus, SocialPlatform
from backend.services.linkedin_api_service import LinkedInAPIService
from backend.services.social_oauth_service import SocialOAuthService


class SocialPublishService:
    def __init__(
        self,
        db: Session,
        *,
        oauth_service: SocialOAuthService | None = None,
        linkedin_api_service: LinkedInAPIService | None = None,
    ) -> None:
        self.db = db
        self.oauth_service = oauth_service or SocialOAuthService()
        self.linkedin_api_service = linkedin_api_service or LinkedInAPIService()

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

    def publish_post(self, request: PublishPostRequest) -> PublishPostResponse:
        if request.platform != SocialPlatform.LINKEDIN:
            raise ValueError("Only LinkedIn publishing is supported")

        account = self.db.query(SocialAccount).filter(SocialAccount.account_uuid == request.social_account_id).first()
        if not account:
            raise ValueError("Social account not found")

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

            if account.expires_at and account.expires_at <= datetime.now(timezone.utc):
                if not refresh_token:
                    raise ValueError("Access token expired and refresh token is unavailable")
                refreshed = self.linkedin_api_service.refresh_access_token(refresh_token)
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

            post_response = self.linkedin_api_service.create_post(
                access_token,
                author_urn=f"urn:li:person:{account.external_id}",
                text=request.text,
                media_url=request.media_url,
            )
            linkedin_post_urn = post_response.get("body", {}).get("id") or post_response.get("headers", {}).get("x-restli-id")
            record.status = "published"
            record.linkedin_post_urn = linkedin_post_urn
            record.error_details = None
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return PublishPostResponse(
                publish_record_id=str(record.record_uuid),
                platform=request.platform,
                status=record.status,
                linkedin_post_urn=linkedin_post_urn,
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
                linkedin_post_urn=record.linkedin_post_urn,
                error_details=record.error_details,
            )
