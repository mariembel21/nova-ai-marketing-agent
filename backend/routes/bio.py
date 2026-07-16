from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.agents.bio_agent import BioAgent
from backend.schemas.bio_schema import BioRequest, BioResponse
from backend.services.llm_factory import get_llm_provider


router = APIRouter(prefix="/bio", tags=["bio"])


@router.post("/optimize", response_model=BioResponse)
def optimize_bio(request: BioRequest) -> BioResponse:
	try:
		agent = BioAgent(llm_provider=get_llm_provider())
		return agent.run(request)
	except Exception as exc:
		raise HTTPException(
			status_code=500,
			detail=f"Bio optimization failed: {exc}"
		) from exc
