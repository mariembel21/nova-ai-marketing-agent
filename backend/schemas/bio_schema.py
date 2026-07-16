from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class BioRequest(BaseModel):
	current_bio: str = Field(..., description="Biographie actuelle de l'utilisateur {A}")


class BioAnalysis(BaseModel):
	strengths: List[str]
	weaknesses: List[str]
	strategic_angle: str


class BioBonusVariants(BaseModel):
	authority_angle: str
	disruptive_angle: str


class BioResponse(BaseModel):
	bio_id: str
	version_concise: str
	version_standard: str
	version_punchy: str
	analysis: BioAnalysis
	bonus_variants: BioBonusVariants
	tone_valid: bool
	retry_count: int
