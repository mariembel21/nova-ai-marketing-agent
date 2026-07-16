from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.agents.strategy_agent import StrategyAgent
from backend.schemas.strategy_schema import (
	StrategyRequest,
	StrategyRevisionRequest,
	StrategyResponse,
)
from backend.services.llm_factory import get_llm_provider


router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.post("/generate", response_model=StrategyResponse)
def generate_strategy(request: StrategyRequest) -> StrategyResponse:
	try:
		agent = StrategyAgent(llm_provider=get_llm_provider())
		return agent.run(request)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Strategy generation failed: {exc}") from exc


@router.post("/revise", response_model=StrategyResponse)
def revise_strategy(request: StrategyRevisionRequest) -> StrategyResponse:
	try:
		agent = StrategyAgent(llm_provider=get_llm_provider())
		return agent.run(
			request.original_request,
			feedback=request.client_feedback,
			previous_response=request.previous_strategy,
		)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Strategy revision failed: {exc}") from exc
