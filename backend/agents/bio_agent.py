from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.schemas.bio_schema import (
	BioAnalysis,
	BioBonusVariants,
	BioRequest,
	BioResponse,
)
from backend.services.llm_provider import BaseLLMProvider


class BioState(TypedDict, total=False):
	request: BioRequest
	system_prompt: str
	user_prompt: str
	bio_id: str
	llm_output: Dict[str, Any]
	tone_score: float
	tone_feedback: str
	retry_count: int
	response: BioResponse


class BioAgent:

	def __init__(self, llm_provider: BaseLLMProvider):
		self.llm_provider = llm_provider
		self.graph = self._build_graph()

	def _build_graph(self):
		workflow = StateGraph(BioState)

		workflow.add_node("build_prompt", self._build_prompt_node)
		workflow.add_node("generate_bio", self._generate_bio_node)
		workflow.add_node("check_tone", self._check_tone_node)
		workflow.add_node("build_response", self._build_response_node)

		workflow.add_edge(START, "build_prompt")
		workflow.add_edge("build_prompt", "generate_bio")
		workflow.add_edge("generate_bio", "check_tone")

		workflow.add_conditional_edges(
			"check_tone",
			self._route_after_check_tone,
			{
				"generate_bio": "generate_bio",
				"build_response": "build_response",
			},
		)

		workflow.add_edge("build_response", END)

		return workflow.compile()

	def run(self, request: BioRequest) -> BioResponse:
		result = self.graph.invoke(
			{
				"request": request,
				"retry_count": 0,
			}
		)

		return result["response"]

	def _build_prompt_node(self, state: BioState) -> BioState:
		request = state["request"]

		bio_id = f"bio_{uuid.uuid4().hex[:12]}"

		system_prompt = _load_system_prompt()
		system_prompt = system_prompt.replace("{current_bio}", request.current_bio)

		language_instruction = (
			"The variables above are in English. "
			"You MUST write the entire response in English. "
			"Do not write in French under any circumstances."
		) if _is_english(request.current_bio) else (
			"Les variables ci-dessus sont en français. "
			"Rédige l'intégralité de la réponse en français."
		)

		user_prompt = json.dumps(
			{
				"current_bio": request.current_bio,
				"language_instruction": language_instruction,
			},
			indent=2,
			ensure_ascii=False,
		)

		return {
			"bio_id": bio_id,
			"system_prompt": system_prompt,
			"user_prompt": user_prompt,
		}

	def _generate_bio_node(self, state: BioState) -> BioState:
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

	def _check_tone_node(self, state: BioState) -> BioState:
		return {}

	def _build_response_node(self, state: BioState) -> BioState:
		llm_output = state.get("llm_output", {})

		try:
			analysis = BioAnalysis(**llm_output.get("analysis", {}))
		except Exception:
			analysis = BioAnalysis(
				strengths=[],
				weaknesses=[],
				strategic_angle="",
			)

		try:
			bonus_variants = BioBonusVariants(**llm_output.get("bonus_variants", {}))
		except Exception:
			bonus_variants = BioBonusVariants(
				authority_angle="",
				disruptive_angle="",
			)

		response = BioResponse(
			bio_id=str(state.get("bio_id", "")),
			version_concise=str(llm_output.get("version_concise", "")),
			version_standard=str(llm_output.get("version_standard", "")),
			version_punchy=str(llm_output.get("version_punchy", "")),
			analysis=analysis,
			bonus_variants=bonus_variants,
			tone_valid=_coerce_tone_score(
				state.get("tone_score")
			) >= 0.8,
			retry_count=int(state.get("retry_count", 0)),
		)

		return {
			"response": response
		}

	def _route_after_check_tone(self, state: BioState):
		tone_score = _coerce_tone_score(
			state.get("tone_score")
		)

		retry_count = int(state.get("retry_count", 0))

		if tone_score < 0.8 and retry_count < 3:
			return "generate_bio"

		return "build_response"


def _load_system_prompt() -> str:
	prompt_path = (
		Path(__file__).resolve().parents[1]
		/ "prompts"
		/ "bio_prompt.txt"
	)

	if prompt_path.exists():
		return prompt_path.read_text(
			encoding="utf-8"
		).strip()

	return (
		"You are an expert social media bio strategist. "
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
