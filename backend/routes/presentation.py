from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.agents.presentation_agent import PresentationAgent
from backend.schemas.presentation_schema import (
	PresentationRequest,
	PresentationResponse,
)
from backend.services.llm_factory import get_llm_provider
from backend.services.llm_provider import BaseLLMProvider


router = APIRouter(prefix="/presentation", tags=["presentation"])


def get_presentation_llm_provider() -> BaseLLMProvider:
	return get_llm_provider()


@router.post("/generate", response_model=PresentationResponse)
def generate_presentation(
	request: PresentationRequest,
	llm_provider: BaseLLMProvider = Depends(get_presentation_llm_provider),
) -> PresentationResponse:
	try:
		agent = PresentationAgent(llm_provider=llm_provider)
		return agent.run(request)
	except Exception as exc:
		raise HTTPException(
			status_code=500,
			detail=f"Presentation generation failed: {exc}"
		) from exc
