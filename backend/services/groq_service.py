from __future__ import annotations

import json
import os
from typing import Any, Dict

from groq import Groq

from backend.services.llm_provider import BaseLLMProvider


class GroqLLMProvider(BaseLLMProvider):
	"""Groq implementation behind the provider abstraction."""

	def __init__(self) -> None:
		api_key = os.getenv("GROQ_API_KEY")
		if not api_key:
			raise ValueError("GROQ_API_KEY is not set")

		self.model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
		self.client = Groq(api_key=api_key)

	def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
		completion = self.client.chat.completions.create(
			model=self.model_name,
			temperature=0.3,
			messages=[
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
			response_format={"type": "json_object"},
		)
		content = completion.choices[0].message.content or "{}"
		return _safe_json_loads(content)


def _safe_json_loads(content: str) -> Dict[str, Any]:
	"""Parse JSON and return an empty object on malformed output."""
	try:
		parsed = json.loads(content)
		return parsed if isinstance(parsed, dict) else {}
	except json.JSONDecodeError:
		return {}
