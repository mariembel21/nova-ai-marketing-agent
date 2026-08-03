from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SocialPlatform(str, Enum):
    LINKEDIN = "linkedin"


class SocialAccountType(str, Enum):
    PERSONAL = "personal"
    ORGANIZATION = "organization"


class SocialConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"


class StartAuthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: SocialPlatform = Field(default=SocialPlatform.LINKEDIN, description="Target platform")
    account_type: SocialAccountType = Field(default=SocialAccountType.PERSONAL, description="Type of connected account")


class StartAuthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authorization_url: str = Field(..., description="LinkedIn authorization URL")
    state: str = Field(..., description="Signed OAuth state value")


class OAuthCallbackResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(..., description="Internal social account identifier")
    platform: SocialPlatform = Field(..., description="Connected platform")
    external_id: str = Field(..., description="Provider account identifier")
    account_name: str = Field(..., description="Display name of the connected account")
    scopes: list[str] = Field(default_factory=list, description="Granted OAuth scopes")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiry timestamp")


class ConnectionStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: SocialPlatform = Field(..., description="Platform being checked")
    status: SocialConnectionStatus = Field(..., description="Connection state")
    account_id: Optional[str] = Field(default=None, description="Internal social account identifier")
    account_name: Optional[str] = Field(default=None, description="Connected account display name")
    external_id: Optional[str] = Field(default=None, description="Provider account identifier")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiry timestamp")
    scopes: list[str] = Field(default_factory=list, description="Granted OAuth scopes")


class PublishPostRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: SocialPlatform = Field(default=SocialPlatform.LINKEDIN, description="Target platform")
    social_account_id: str = Field(..., description="Internal social account identifier")
    text: str = Field(..., min_length=1, description="Post text")
    hashtags: list[str] = Field(default_factory=list, description="List of hashtags")
    media_url: Optional[str] = Field(default=None, description="Optional media URL")


class PublishPostResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publish_record_id: str = Field(..., description="Internal publish record identifier")
    platform: SocialPlatform = Field(..., description="Platform used for publication")
    status: str = Field(..., description="Publish status")
    linkedin_post_urn: Optional[str] = Field(default=None, description="LinkedIn post URN")
    error_details: Optional[str] = Field(default=None, description="Error details if publishing failed")