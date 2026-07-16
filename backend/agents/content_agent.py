from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.schemas.content_schema import (
    ContentPiece,
    ContentRequest,
    ContentResponse,
    SocialPlatform,
)
from backend.services.llm_provider import BaseLLMProvider


class ContentState(TypedDict, total=False):
    request: ContentRequest
    system_prompt: str
    user_prompt: str
    content_id: str
    llm_output: Dict[str, Any]
    tone_score: float
    tone_feedback: str
    retry_count: int
    response: ContentResponse


class ContentAgent:

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ContentState)

        workflow.add_node("build_brief", self._build_brief_node)
        workflow.add_node("generate_content", self._generate_content_node)
        workflow.add_node("check_tone", self._check_tone_node)
        workflow.add_node("generate_media", self._generate_media_node)
        workflow.add_node("build_response", self._build_response_node)

        workflow.add_edge(START, "build_brief")
        workflow.add_edge("build_brief", "generate_content")
        workflow.add_edge("generate_content", "check_tone")

        workflow.add_conditional_edges(
            "check_tone",
            self._route_after_check_tone,
            {
                "generate_content": "generate_content",
                "generate_media": "generate_media",
            },
        )

        workflow.add_edge("generate_media", "build_response")
        workflow.add_edge("build_response", END)

        return workflow.compile()

    def run(self, request: ContentRequest) -> ContentResponse:
        result = self.graph.invoke(
            {
                "request": request,
                "retry_count": 0,
            }
        )

        return result["response"]

    def _build_brief_node(self, state: ContentState) -> ContentState:
        request = state["request"]

        content_id = f"content_{uuid.uuid4().hex[:12]}"

        system_prompt = _load_system_prompt(request.platform)

        system_prompt = (
            system_prompt.replace("{topic}", request.topic)
            .replace("{target}", request.target)
            .replace("{objective}", request.objective)
            .replace("{tech_level}", request.tech_level)
        )

        language_instruction = (
            "The variables above are in English. "
            "You MUST write the entire post in English. "
            "Do not write in French under any circumstances."
        ) if _is_english(request.topic) else (
            "Les variables ci-dessus sont en français. "
            "Rédige l'intégralité du post en français."
        )

        user_prompt = json.dumps(
            {
                "topic": request.topic,
                "target": request.target,
                "objective": request.objective,
                "tech_level": request.tech_level,
                "language_instruction": language_instruction,
                "platform_reminder": (
                    "STRICT 280 character limit on caption. Count every character."
                ) if request.platform.value == "x" else None,
            },
             indent=2,
            ensure_ascii=False,
        )

        return {
            "content_id": content_id,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }

    def _generate_content_node(self, state: ContentState) -> ContentState:
        llm_output = self.llm_provider.generate_json(
            system_prompt=state["system_prompt"],
            user_prompt=state["user_prompt"],
        )

        return {
            "llm_output": llm_output,
            "tone_score": _coerce_tone_score(
                llm_output.get("tone_score")
            ),
            "tone_feedback": str(
                llm_output.get("tone_feedback") or ""
            ),
            "retry_count": int(state.get("retry_count", 0)) + 1,
        }

    def _check_tone_node(self, state: ContentState) -> ContentState:
        return {}

    def _generate_media_node(self, state: ContentState) -> ContentState:
        return {}

    def _build_response_node(self, state: ContentState) -> ContentState:
        request = state["request"]

        llm_output = state.get("llm_output", {})

        hashtags = llm_output.get("hashtags")

        if not isinstance(hashtags, list):
            hashtags = []

        hashtags = [str(tag) for tag in hashtags]

        piece = ContentPiece(
            platform=request.platform,
            caption=str(llm_output.get("caption", "")),
            cta=str(llm_output.get("cta", "")),
            hashtags=hashtags,
        )

        response = ContentResponse(
            content_id=state["content_id"],
            platform=request.platform,
            piece=piece,
            tone_valid=_coerce_tone_score(
                state.get("tone_score")
            ) >= 0.8,
            retry_count=int(state.get("retry_count", 0)),
        )

        return {
            "response": response
        }

    def _route_after_check_tone(self, state: ContentState):
        tone_score = _coerce_tone_score(
            state.get("tone_score")
        )

        retry_count = int(state.get("retry_count", 0))

        if tone_score < 0.8 and retry_count < 3:
            return "generate_content"

        return "generate_media"


def _load_system_prompt(platform: SocialPlatform | None = None) -> str:
    if platform:
        prompt_path = (
            Path(__file__).resolve().parents[1]
            / "prompts"
            / f"content_{platform.value}_prompt.txt"
        )

        if prompt_path.exists():
            return prompt_path.read_text(
                encoding="utf-8"
            ).strip()

    return (
        "You are an expert social media copywriter. "
        "Return only valid JSON."
    )


def _coerce_tone_score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _is_english(text: str) -> bool:
    french_markers = (
        " le ", " la ", " les ", " un ", " une ", " des ",
        " est ", " sont ", " pour ", " avec ", " sur ",
        "l'", "d'", "n'", "c'", "j'",
    )
    lowered = text.lower()
    return not any(marker in lowered for marker in french_markers)