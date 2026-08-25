from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.schemas.social_schema import (
    ConnectionStatusResponse,
    OAuthCallbackResponse,
    PublishPostRequest,
    PublishPostResponse,
    StartAuthRequest,
    StartAuthResponse,
    SocialPlatform,
)
from backend.services.linkedin_api_service import LinkedInAPIService
from backend.services.social_publish_service import SocialPublishService
from backend.services.social_oauth_service import SocialOAuthService
from backend.services.x_api_service import XAPIService


router = APIRouter(prefix="/social", tags=["social"])


@router.post("/linkedin/auth/start", response_model=StartAuthResponse)
def start_linkedin_auth(request: StartAuthRequest) -> StartAuthResponse:
    try:
        oauth_service = SocialOAuthService()
        authorization_url, state = oauth_service.build_authorization_url(
            platform=request.platform,
            account_type=request.account_type,
        )
        return StartAuthResponse(authorization_url=authorization_url, state=state)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/linkedin/auth/callback", response_model=OAuthCallbackResponse)
def linkedin_auth_callback(
    code: str,
    state: str,
    platform: SocialPlatform = SocialPlatform.LINKEDIN,
    db: Session = Depends(get_db),
) -> OAuthCallbackResponse:
    try:
        oauth_service = SocialOAuthService()
        linkedin_api_service = LinkedInAPIService()
        service = SocialPublishService(db, oauth_service=oauth_service, linkedin_api_service=linkedin_api_service)

        state_payload = oauth_service.verify_state(state)
        if state_payload.get("platform") != platform.value:
            raise ValueError("OAuth state platform mismatch")

        token_payload = linkedin_api_service.exchange_code_for_token(code)
        userinfo = linkedin_api_service.get_user_info(token_payload["access_token"])

        external_id = userinfo.get("sub") or userinfo.get("id")
        account_name = userinfo.get("name") or userinfo.get("localizedFirstName") or "LinkedIn Account"
        scopes = token_payload.get("scope", "").split()
        account = service.store_linkedin_account(
            platform=platform,
            account_type=state_payload.get("account_type", "personal"),
            external_id=external_id,
            account_name=account_name,
            access_token=token_payload["access_token"],
            refresh_token=token_payload.get("refresh_token"),
            expires_in=token_payload.get("expires_in"),
            scopes=scopes,
        )

        return OAuthCallbackResponse(
            account_id=str(account.account_uuid),
            platform=platform,
            external_id=account.external_id,
            account_name=account.account_name,
            scopes=scopes,
            expires_at=account.expires_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/linkedin/connection-status", response_model=ConnectionStatusResponse)
def linkedin_connection_status(social_account_id: str | None = None, db: Session = Depends(get_db)) -> ConnectionStatusResponse:
    try:
        service = SocialPublishService(db)
        return service.get_connection_status(SocialPlatform.LINKEDIN, social_account_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/linkedin/publish", response_model=PublishPostResponse)
def publish_linkedin_post(request: PublishPostRequest, db: Session = Depends(get_db)) -> PublishPostResponse:
    try:
        service = SocialPublishService(db)
        return service.publish_post(request)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/x/auth/start", response_model=StartAuthResponse)
def start_x_auth(request: StartAuthRequest) -> StartAuthResponse:
    try:
        oauth_service = SocialOAuthService()
        authorization_url, state = oauth_service.build_authorization_url(
            platform=SocialPlatform.X,
            account_type=request.account_type,
        )
        return StartAuthResponse(authorization_url=authorization_url, state=state)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/x/auth/callback", response_model=OAuthCallbackResponse)
def x_auth_callback(
    code: str,
    state: str,
    platform: SocialPlatform = SocialPlatform.X,
    db: Session = Depends(get_db),
) -> OAuthCallbackResponse:
    try:
        oauth_service = SocialOAuthService()
        x_api_service = XAPIService()
        service = SocialPublishService(db, oauth_service=oauth_service, x_api_service=x_api_service)

        state_payload = oauth_service.verify_state(state)
        if state_payload.get("platform") != platform.value:
            raise ValueError("OAuth state platform mismatch")

        code_verifier = state_payload.get("code_verifier")
        if not code_verifier:
            raise ValueError("OAuth state missing PKCE verifier")

        token_payload = x_api_service.exchange_code_for_token(code, code_verifier)
        userinfo = x_api_service.get_authenticated_user(token_payload["access_token"])
        user_data = userinfo.get("data") or {}

        external_id = user_data.get("id")
        if not external_id:
            raise ValueError("X user id was not returned")
        account_name = user_data.get("username") or user_data.get("name") or "X Account"
        scopes = token_payload.get("scope", "").split()
        account = service.store_x_account(
            platform=platform,
            account_type=state_payload.get("account_type", "personal"),
            external_id=external_id,
            account_name=account_name,
            access_token=token_payload["access_token"],
            refresh_token=token_payload.get("refresh_token"),
            expires_in=token_payload.get("expires_in"),
            scopes=scopes,
        )

        return OAuthCallbackResponse(
            account_id=str(account.account_uuid),
            platform=platform,
            external_id=account.external_id,
            account_name=account.account_name,
            scopes=scopes,
            expires_at=account.expires_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/x/connection-status", response_model=ConnectionStatusResponse)
def x_connection_status(social_account_id: str | None = None, db: Session = Depends(get_db)) -> ConnectionStatusResponse:
    try:
        service = SocialPublishService(db)
        return service.get_connection_status(SocialPlatform.X, social_account_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc