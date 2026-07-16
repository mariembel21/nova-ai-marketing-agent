from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SocialPlatform(str, Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    X = "x"


class ContentRequest(BaseModel):
    platform: SocialPlatform = Field(..., description="Target social platform")
    topic: str = Field(..., description="Post topic")
    target: str = Field(..., description="Target audience")
    objective: str = Field(..., description="Marketing objective")
    tech_level: str = Field(..., description="Technicality level")


class ContentPiece(BaseModel):
    platform: SocialPlatform
    caption: str
    cta: str
    hashtags: Optional[List[str]] = None


class ContentResponse(BaseModel):
    content_id: str
    platform: SocialPlatform
    piece: ContentPiece
    tone_valid: bool
    retry_count: int