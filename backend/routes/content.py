from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.agents.content_agent import ContentAgent
from backend.schemas.content_schema import ContentRequest, ContentResponse
from backend.services.llm_factory import get_llm_provider


router = APIRouter(prefix="/content", tags=["content"])


@router.post("/generate", response_model=ContentResponse)
def generate_content(request: ContentRequest) -> ContentResponse:
    try:
        agent = ContentAgent(llm_provider=get_llm_provider())
        return agent.run(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {exc}") from exc