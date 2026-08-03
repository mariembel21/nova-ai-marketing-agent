from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.schemas.presentation_schema import (
	PresentationRequest,
	PresentationResponse,
)
from backend.services.llm_provider import BaseLLMProvider


class PresentationState(TypedDict, total=False):
	request: PresentationRequest
	system_prompt: str
	user_prompt: str
	llm_output: Any
	response_payload: dict[str, Any]
	response: PresentationResponse
	validation_errors: list[dict[str, Any]]
	validation_warnings: list[dict[str, Any]]
	retry_count: int
	revision_mode: bool


class PresentationAgent:
	"""LangGraph-based presentation agent for planning-only output."""

	def __init__(self, llm_provider: BaseLLMProvider) -> None:
		self.llm_provider = llm_provider
		self.system_prompt = _load_system_prompt()
		self.graph = self._build_graph()

	def _build_graph(self):
		workflow = StateGraph(PresentationState)
		workflow.add_node("build_prompt", self._build_prompt_node)
		workflow.add_node("call_llm", self._call_llm_node)
		workflow.add_node("build_response", self._build_response_node)
		workflow.add_node("revise_prompt", self._build_revise_prompt_node)

		workflow.add_edge(START, "build_prompt")
		workflow.add_edge("build_prompt", "call_llm")
		workflow.add_edge("call_llm", "build_response")
		workflow.add_conditional_edges(
			"build_response",
			self._route_after_build_response,
			{
				"revise_prompt": "revise_prompt",
				END: END,
			},
		)
		workflow.add_edge("revise_prompt", "call_llm")

		return workflow.compile()

	def run(self, request: PresentationRequest) -> PresentationResponse:
		result = self.graph.invoke(
			{
				"request": request,
				"retry_count": 0,
				"validation_warnings": [],
			}
		)

		return result["response"]

	def _build_prompt_node(self, state: PresentationState) -> PresentationState:
		request = state["request"]
		user_payload = {
			"topic": request.topic,
			"target": request.target,
			"objective": request.objective,
			"technical_level": request.technical_level,
			"business_name": request.business_name,
			"business_description": request.business_description,
			"industry": request.industry,
			"target_audience": request.target_audience,
			"additional_context": request.additional_context,
		}

		return {
			"system_prompt": self.system_prompt,
			"user_prompt": json.dumps(user_payload, ensure_ascii=True, indent=2),
		}

	def _call_llm_node(self, state: PresentationState) -> PresentationState:
		llm_output = self.llm_provider.generate_json(
			system_prompt=state["system_prompt"],
			user_prompt=state["user_prompt"],
		)
		return {"llm_output": llm_output}

	def _build_response_node(self, state: PresentationState) -> PresentationState:
		base_payload = state.get("response_payload")
		response_payload = _normalize_presentation_output(
			state["llm_output"],
			state["request"],
			base_payload=base_payload,
			revision_mode=bool(state.get("revision_mode")),
		)
		validation_errors = _validate_presentation_output(response_payload)
		if validation_errors:
			if state.get("retry_count", 0) < 2:
				return {
					"response_payload": response_payload,
					"validation_errors": validation_errors,
					"validation_warnings": [],
				}

			response = PresentationResponse.model_validate(
				{
					**response_payload,
					"validation_warnings": validation_errors,
				}
			)
			return {
				"response": response,
				"response_payload": response_payload,
				"validation_errors": validation_errors,
				"validation_warnings": validation_errors,
			}

		response = PresentationResponse.model_validate(
			{
				**response_payload,
				"validation_warnings": [],
			}
		)
		return {
			"response": response,
			"response_payload": response_payload,
			"validation_errors": [],
			"validation_warnings": [],
		}

	def _build_revise_prompt_node(self, state: PresentationState) -> PresentationState:
		errors = state.get("validation_errors", [])
		base_payload = state.get("response_payload") or {}
		revision_payload = {
			"instruction": f"Corrige uniquement les slides suivantes pour les raisons indiquées : {errors}",
			"previous_json": base_payload,
			"errors": errors,
			"expected_slide_roles": [
				"hook",
				"problem",
				"insight",
				"consequences",
				"solution",
				"dev_1",
				"dev_2",
				"dev_3",
				"case_study",
				"transformation",
				"cta",
			],
			"output_requirements": (
				"Retourne uniquement les slides corrigées sous forme de JSON. "
				"Ne modifie pas les slides non concernées."
			),
		}

		return {
			"system_prompt": state["system_prompt"],
			"user_prompt": json.dumps(revision_payload, ensure_ascii=True, indent=2),
			"revision_mode": True,
			"retry_count": state.get("retry_count", 0) + 1,
			"validation_errors": [],
		}

	def _route_after_build_response(self, state: PresentationState):
		validation_errors = state.get("validation_errors", [])
		if validation_errors and state.get("retry_count", 0) < 2:
			return "revise_prompt"
		return END


def _load_system_prompt() -> str:
	prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "presentation_prompt.txt"
	if prompt_path.exists():
		content = prompt_path.read_text(encoding="utf-8").strip()
		if content:
			return content

	return (
		"Tu es un expert en présentations marketing. Retourne uniquement du JSON valide "
		"correspondant exactement au schéma demandé."
	)


def _normalize_presentation_output(
	llm_output: Any,
	request: PresentationRequest,
	base_payload: dict[str, Any] | None = None,
	revision_mode: bool = False,
) -> dict[str, Any]:
	if not isinstance(llm_output, dict):
		raise ValueError("LLM output must be a JSON object")

	def _coalesce(*keys: str, default: Any = None) -> Any:
		for key in keys:
			value = llm_output.get(key)
			if value is not None:
				return value
		if revision_mode and base_payload is not None:
			for key in keys:
				value = base_payload.get(key)
				if value is not None:
					return value
		return default

	def _normalize_slide(slide: Any) -> dict[str, Any]:
		if not isinstance(slide, dict):
			raise ValueError("Each slide must be a JSON object")

		slide_number = slide.get("slide_number", slide.get("numero"))
		slide_role = slide.get("slide_role", slide.get("role", slide.get("rôle")))
		title = slide.get("title", slide.get("titre"))
		bullet_points = slide.get("bullet_points", slide.get("points"))
		visual_suggestion = slide.get("visual_suggestion", slide.get("visuel"))

		if slide_number is None or slide_role is None or title is None or bullet_points is None or visual_suggestion is None:
			raise ValueError("Each slide must include number, role, title, bullet points, and visual suggestion")

		if not isinstance(bullet_points, list):
			raise ValueError("Slide bullet points must be a list")

		return {
			"slide_number": slide_number,
			"slide_role": slide_role,
			"title": title,
			"bullet_points": bullet_points,
			"visual_suggestion": visual_suggestion,
		}

	if revision_mode and base_payload is not None and "slides" in llm_output:
		slides = _merge_revision_slides(base_payload, llm_output.get("slides", []))
	else:
		slides = llm_output.get("slides", [])

	if not isinstance(slides, list):
		raise ValueError("Slides must be a list")

	return {
		"presentation_title": _coalesce("presentation_title", "titre", "title", default=request.topic),
		"presentation_summary": _coalesce(
			"presentation_summary",
			"summary",
			"resume",
			default=f"Présentation stratégique sur {request.topic}",
		),
		"target": _coalesce("target", default=request.target),
		"objective": _coalesce("objective", default=request.objective),
		"slides": [_normalize_slide(slide) for slide in slides],
	}


def _merge_revision_slides(
	base_payload: dict[str, Any],
	revision_slides: Any,
) -> list[Any]:
	base_slides = base_payload.get("slides", [])
	if not isinstance(base_slides, list):
		raise ValueError("Base slides must be a list")

	if not isinstance(revision_slides, list):
		raise ValueError("Revision slides must be a list")

	merged_by_number: dict[Any, Any] = {}
	for slide in revision_slides:
		if not isinstance(slide, dict):
			continue
		number = slide.get("slide_number", slide.get("numero"))
		if number is None:
			continue
		merged_by_number[number] = slide

	merged_slides: list[Any] = []
	for slide in base_slides:
		if not isinstance(slide, dict):
			merged_slides.append(slide)
			continue
		number = slide.get("slide_number", slide.get("numero"))
		if number in merged_by_number:
			merged_slides.append(merged_by_number[number])
		else:
			merged_slides.append(slide)

	return merged_slides


def _validate_presentation_output(payload: dict[str, Any]) -> list[dict[str, Any]]:
	errors: list[dict[str, Any]] = []
	slides = payload.get("slides")
	if not isinstance(slides, list):
		return [{"slide_number": 0, "field": "slides", "reason": "slides must be a list"}]

	expected_roles = [
		"hook",
		"problem",
		"insight",
		"consequences",
		"solution",
		"dev_1",
		"dev_2",
		"dev_3",
		"case_study",
		"transformation",
		"cta",
	]
	if len(slides) != len(expected_roles):
		errors.append(
			{
				"slide_number": 0,
				"field": "slides",
				"reason": f"Expected exactly 11 slides, got {len(slides)}",
			}
		)

	blacklist = [
		"gain de temps",
		"meilleurs résultats",
		"amélioration de la productivité",
		"optimisation des performances",
		"efficacité accrue",
	]
	verb_pattern = re.compile(
		r"\b(?:est|sont|fait|font|permet|permettent|génère|génèrent|augmente|augmentent|réduit|réduisent|améliore|améliorent|optimise|optimisent|automatise|automatisent|convertit|convertissent|pilote|pilotent|mesure|mesurent|déploie|déploient|cible|ciblent|renforce|renforcent|simplifie|simplifient|active|activent|crée|créent|structure|structurent|analyse|analysent|alimente|alimentent)\b",
		re.IGNORECASE,
	)
	seen_visuals: list[tuple[int, str]] = []
	for index, slide in enumerate(slides):
		slide_number = _safe_slide_number(slide, index)
		if not isinstance(slide, dict):
			errors.append({"slide_number": slide_number, "field": "slide", "reason": "Slide must be an object"})
			continue

		expected_role = expected_roles[index] if index < len(expected_roles) else None
		actual_role = str(slide.get("slide_role", "")).strip()
		if expected_role is not None and actual_role != expected_role:
			errors.append(
				{
					"slide_number": slide_number,
					"field": "slide_role",
					"reason": f"Expected slide_role '{expected_role}' at position {index + 1}, got '{actual_role or 'missing'}'",
				}
			)

		bullet_points = slide.get("bullet_points")
		if isinstance(bullet_points, list):
			for bullet_index, bullet in enumerate(bullet_points):
				bullet_text = str(bullet).strip()
				bullet_lower = _strip_accents(bullet_text).lower()
				if any(phrase in bullet_lower for phrase in blacklist):
					errors.append(
						{
							"slide_number": slide_number,
							"field": "bullet_points",
							"reason": f"Bullet point {bullet_index + 1} contains a blacklisted phrase",
						}
					)

				word_count = len([word for word in re.split(r"\s+", bullet_text) if word])
				has_digit = bool(re.search(r"\d", bullet_text))
				has_verb = bool(verb_pattern.search(bullet_text))
				if word_count < 3 or (not has_digit and not has_verb and word_count < 4):
					errors.append(
						{
							"slide_number": slide_number,
							"field": "bullet_points",
							"reason": f"Bullet point {bullet_index + 1} is too short or too generic",
						}
					)
		else:
			errors.append({"slide_number": slide_number, "field": "bullet_points", "reason": "bullet_points must be a list"})

		visual_suggestion = str(slide.get("visual_suggestion", "")).strip()
		visual_normalized = _normalize_visual_text(visual_suggestion)
		for previous_slide_number, previous_visual in seen_visuals:
			similarity = SequenceMatcher(None, visual_normalized, previous_visual).ratio()
			if visual_normalized and (visual_normalized == previous_visual or similarity > 0.8):
				errors.append(
					{
						"slide_number": slide_number,
						"field": "visual_suggestion",
						"reason": f"Visual suggestion is too similar to slide {previous_slide_number}",
					}
				)
				break
		seen_visuals.append((slide_number, visual_normalized))

	return errors


def _safe_slide_number(slide: Any, index: int) -> int:
	if isinstance(slide, dict):
		number = slide.get("slide_number", slide.get("numero"))
		if isinstance(number, int):
			return number
		try:
			return int(number)
		except (TypeError, ValueError):
			return index + 1
	return index + 1


def _strip_accents(value: str) -> str:
	decomposed = unicodedata.normalize("NFKD", value)
	return "".join(char for char in decomposed if not unicodedata.combining(char))


def _normalize_visual_text(value: str) -> str:
	text = _strip_accents(value).lower()
	return re.sub(r"[^a-z0-9]+", " ", text).strip()
