from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.schemas.social_schema import (
    ConnectionStatusResponse,
    OAuthCallbackResponse,
    PublishPostRequest,
    PublishPostResponse,
    SocialAccountType,
    SocialPlatform,
    StartAuthRequest,
    StartAuthResponse,
)
from backend.services.meta_api_service import MetaAPIService
from backend.services.social_oauth_service import SocialOAuthService
from backend.services.social_publish_service import SocialPublishService


router = APIRouter(prefix="/social", tags=["social"])


@router.post("/facebook/auth/start", response_model=StartAuthResponse)
def start_facebook_auth(request: StartAuthRequest) -> StartAuthResponse:
    try:
        oauth_service = SocialOAuthService()
        authorization_url, state = oauth_service.build_authorization_url(
            platform=SocialPlatform.FACEBOOK,
            account_type=SocialAccountType.ORGANIZATION,
        )
        return StartAuthResponse(authorization_url=authorization_url, state=state)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/facebook/auth/callback", response_model=OAuthCallbackResponse)
def facebook_auth_callback(code: str, state: str, db: Session = Depends(get_db)) -> OAuthCallbackResponse:
    try:
        oauth_service = SocialOAuthService()
        meta_api_service = MetaAPIService()
        service = SocialPublishService(db, oauth_service=oauth_service, meta_api_service=meta_api_service)

        state_payload = oauth_service.verify_state(state)
        if state_payload.get("platform") != SocialPlatform.FACEBOOK.value:
            raise ValueError("OAuth state platform mismatch")

        token_payload = meta_api_service.exchange_code_for_token(code)
        access_token = token_payload["access_token"]
        managed_pages = meta_api_service.get_managed_pages(access_token)
        scopes = oauth_service.get_scopes(SocialPlatform.FACEBOOK)
        stored_accounts = service.store_meta_accounts(
            managed_pages=managed_pages,
            account_type=SocialAccountType.ORGANIZATION.value,
            access_token=access_token,
            expires_in=token_payload.get("expires_in"),
            scopes=scopes,
        )

        facebook_account = next((account for account in stored_accounts if account.platform == SocialPlatform.FACEBOOK.value), None)
        if not facebook_account:
            raise ValueError("No Facebook Pages were returned for the connected account")

        return OAuthCallbackResponse(
            account_id=str(facebook_account.account_uuid),
            platform=SocialPlatform.FACEBOOK,
            external_id=facebook_account.external_id,
            account_name=facebook_account.account_name,
            scopes=scopes,
            expires_at=facebook_account.expires_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/facebook/connection-status", response_model=ConnectionStatusResponse)
def facebook_connection_status(social_account_id: str | None = None, db: Session = Depends(get_db)) -> ConnectionStatusResponse:
    try:
        service = SocialPublishService(db)
        return service.get_connection_status(SocialPlatform.FACEBOOK, social_account_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/facebook/publish", response_model=PublishPostResponse)
def publish_facebook_post(request: PublishPostRequest, db: Session = Depends(get_db)) -> PublishPostResponse:
    try:
        if request.platform != SocialPlatform.FACEBOOK:
            raise ValueError("Publish request platform must be facebook")
        service = SocialPublishService(db)
        return service.publish_post(request)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/instagram/connection-status", response_model=ConnectionStatusResponse)
def instagram_connection_status(social_account_id: str | None = None, db: Session = Depends(get_db)) -> ConnectionStatusResponse:
    try:
        service = SocialPublishService(db)
        return service.get_connection_status(SocialPlatform.INSTAGRAM, social_account_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/instagram/publish", response_model=PublishPostResponse)
def publish_instagram_post(request: PublishPostRequest, db: Session = Depends(get_db)) -> PublishPostResponse:
    try:
        if request.platform != SocialPlatform.INSTAGRAM:
            raise ValueError("Publish request platform must be instagram")
        service = SocialPublishService(db)
        return service.publish_post(request)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
