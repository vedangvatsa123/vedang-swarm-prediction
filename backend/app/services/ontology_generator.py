"""
Ontology Generator
Lightweight version for local LLMs. Produces a simple schema of entity/relationship types.
"""
from typing import List, Dict, Any, Optional
from ..utils.llm_client import LLM

SYSTEM_PROMPT = """You are an ontology designer for social simulations.
Given text and a prediction goal, identify the types of actors and their connections.

Return JSON:
{
  "entity_types": [{"name": "TypeName", "description": "short description"}],
  "edge_types": [{"name": "RELATION_NAME", "description": "short description"}],
  "analysis_summary": "1 sentence about the source material"
}

Rules:
- 4-6 entity types (real actors who can speak: people, orgs, officials, etc.)
- 3-5 relationship types
- Keep descriptions under 50 characters
- Return JSON only, no markdown"""


class OntologyGenerator:
    def __init__(self, llm: Optional[LLM] = None):
        self._llm = llm or LLM()

    def generate(self, texts: List[str], prediction_goal: str, extra_context: str = "") -> Dict[str, Any]:
        combined = "\n\n".join(texts)
        if len(combined) > 6000:
            combined = combined[:6000] + "\n...(truncated)"

        user_msg = f"Goal: {prediction_goal}\n\nText:\n{combined}\n\nDesign the ontology. JSON only."

        result = self._llm.complete_json(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        return self._validate(result)

    @staticmethod
    def _validate(data: Dict[str, Any]) -> Dict[str, Any]:
        data.setdefault("entity_types", [])
        data.setdefault("edge_types", [])
        data.setdefault("analysis_summary", "")

        # Ensure fallbacks
        names = {e.get("name", "") for e in data["entity_types"]}
        if "Person" not in names:
            data["entity_types"].append({"name": "Person", "description": "Individual person"})
        if "Organization" not in names:
            data["entity_types"].append({"name": "Organization", "description": "Organisation or group"})

        data["entity_types"] = data["entity_types"][:8]
        data["edge_types"] = data["edge_types"][:8]
        return data
