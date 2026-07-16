from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.schemas.strategy_schema import StrategyRequest, StrategyResponse
from backend.services.llm_provider import BaseLLMProvider


class StrategyState(TypedDict, total=False):
    request: StrategyRequest
    system_prompt: str
    user_prompt: str
    llm_output: Any
    response: StrategyResponse
    client_feedback: str | None
    previous_response: StrategyResponse | None


class StrategyAgent:
    """LangGraph-based strategy agent for planning-only output."""

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self.llm_provider = llm_provider
        self.system_prompt = _load_system_prompt()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(StrategyState)
        workflow.add_node("build_prompt", self._build_prompt_node)
        workflow.add_node("revise_prompt", self._build_revise_prompt_node)
        workflow.add_node("call_llm", self._call_llm_node)
        workflow.add_node("build_response", self._build_response_node)

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

    def run(
        self,
        request: StrategyRequest,
        feedback: str | None = None,
        previous_response: StrategyResponse | None = None,
    ) -> StrategyResponse:
        state: StrategyState = {"request": request}
        if feedback is not None:
            state["client_feedback"] = feedback
        if previous_response is not None:
            state["previous_response"] = previous_response
        result = self.graph.invoke(state)
        return result["response"]

    def _build_prompt_node(self, state: StrategyState) -> StrategyState:
        request = state["request"]
        user_payload = {
            "business_name": request.business_name,
            "business_description": request.business_description,
            "product_service": request.product_service,
            "industry": request.industry,
            "target_audience": request.target_audience,
            "additional_context": request.additional_context,
        }

        return {
            "system_prompt": self.system_prompt,
            "user_prompt": json.dumps(user_payload, ensure_ascii=True, indent=2),
        }

    def _call_llm_node(self, state: StrategyState) -> StrategyState:
        llm_output = self.llm_provider.generate_json(
            system_prompt=state["system_prompt"],
            user_prompt=state["user_prompt"],
        )
        return {"llm_output": llm_output}

    def _build_revise_prompt_node(self, state: StrategyState) -> StrategyState:
        previous_strategy = state.get("previous_response")
        if previous_strategy is None and "response" in state:
            previous_strategy = state["response"]

        client_feedback = (state.get("client_feedback") or "").strip()
        revision_payload = {
            "previous_strategy": previous_strategy.model_dump(by_alias=True) if previous_strategy else {},
            "client_feedback": client_feedback,
            "instruction": (
                "Revise the previous strategy by keeping everything that was not criticized. "
                "Only change what the feedback explicitly targets. Return a full updated JSON strategy."
            ),
        }

        return {
            "system_prompt": state["system_prompt"],
            "user_prompt": json.dumps(revision_payload, ensure_ascii=True, indent=2),
            "client_feedback": None,
            "previous_response": previous_strategy,
        }

    def _build_response_node(self, state: StrategyState) -> StrategyState:
        output = dict(state["llm_output"])
    
        funnel = output.get("conversion_funnel", {})
        if isinstance(funnel, dict):
          email_seq = funnel.get("email_sequence")
          if isinstance(email_seq, list):
              funnel["email_sequence"] = " | ".join(str(s) for s in email_seq)
          output["conversion_funnel"] = funnel

        response = StrategyResponse.model_validate(output)
        return {"response": response}

    def _route_after_build_response(self, state: StrategyState):
        client_feedback = state.get("client_feedback")
        if isinstance(client_feedback, str) and client_feedback.strip():
            return "revise_prompt"
        return END


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "strategy_prompt.txt"
    if prompt_path.exists():
        content = prompt_path.read_text(encoding="utf-8").strip()
        if content:
            return content

    return (
        "Tu es un stratège marketing senior. Retourne uniquement du JSON valide "
        "correspondant exactement au schéma demandé."
    )