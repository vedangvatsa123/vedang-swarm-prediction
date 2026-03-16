"""
Agent Generator - batch mode with scale.
Generates 20-50 agent profiles from extracted entities.
For entities beyond what was extracted, generates additional
stakeholder archetypes to fill the simulation.
"""
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLM
from ..models.knowledge_graph import KnowledgeGraph

BATCH_SYSTEM = """You create social-media persona profiles for a multi-agent simulation.
Given entities and a prediction goal, create a profile for EACH entity.
Also generate ADDITIONAL agents (analysts, critics, insiders, public voices)
to fill the simulation up to the target count.

Return a JSON array:
[
  {
    "entity_name": "...",
    "entity_type": "Person or Organization or Analyst or Insider etc",
    "username": "a plausible handle",
    "bio": "1-2 sentences of background",
    "personality": "dominant trait (analytical, emotional, contrarian, pragmatic, idealistic, skeptical, etc.)",
    "stance": "supportive / opposing / neutral / cautious",
    "activity_level": 0.0-1.0,
    "influence": 0.0-1.0
  }
]

Rules:
- Create diverse personalities. Mix of supportive, opposing, neutral, cautious.
- Include contrarians and skeptics. Not everyone agrees.
- Give each agent a distinct voice. No two agents should sound alike.
- Bios should be specific. "Former regulator turned consultant" not "a person".
- Never use em-dashes in bios."""


EXPAND_SYSTEM = """Generate additional agent profiles for a social simulation.
These agents are stakeholder archetypes who would realistically participate in
a discussion about the given topic. Create diverse, specific, realistic personas.

Return a JSON array of profiles with the same format:
[{"entity_name": "...", "entity_type": "...", "username": "...", "bio": "...", "personality": "...", "stance": "...", "activity_level": 0.0-1.0, "influence": 0.0-1.0}]

Rules:
- Each agent must have a unique perspective
- Include: industry insiders, critics, analysts, affected citizens, journalists, academics, lobbyists
- Mix stances: some supportive, some opposing, some neutral, some shifting
- Personalities should vary: analytical, emotional, contrarian, pragmatic, skeptical, idealistic
- Never use em-dashes"""


class AgentGenerator:
    def __init__(self, llm: Optional[LLM] = None):
        self._llm = llm or LLM()

    def generate_profiles(
        self,
        graph: KnowledgeGraph,
        prediction_goal: str,
        target_count: int = 30,
        progress_cb=None,
    ) -> List[Dict[str, Any]]:
        entities = list(graph.entities.values())

        if progress_cb:
            progress_cb(0, target_count, "Generating agent profiles...")

        # Step 1: Generate profiles for extracted entities
        profiles = []
        if entities:
            entity_lines = []
            for e in entities:
                entity_lines.append(f"- {e.name} ({e.entity_type}): {e.summary[:120]}")

            user_msg = (
                f"Prediction goal: {prediction_goal}\n\n"
                f"Entities ({len(entities)}):\n" + "\n".join(entity_lines) +
                f"\n\nCreate a profile for each entity. If there are fewer than {target_count}, "
                f"add more stakeholder archetypes to reach {target_count} total agents. "
                f"Return a JSON array."
            )

            try:
                result = self._llm.complete_json(
                    messages=[
                        {"role": "system", "content": BATCH_SYSTEM},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.7,
                    max_tokens=6000,
                )
            except Exception:
                result = []

            if isinstance(result, dict):
                result = result.get("profiles", result.get("agents", []))
            if isinstance(result, list):
                for p in result:
                    if isinstance(p, dict) and p.get("entity_name"):
                        profiles.append(p)

        if progress_cb:
            progress_cb(len(profiles), target_count, f"Generated {len(profiles)} profiles...")

        # Step 2: If we still need more agents, generate additional ones
        if len(profiles) < target_count:
            remaining = target_count - len(profiles)
            existing_names = [p.get("entity_name", "") for p in profiles]

            user_msg = (
                f"Topic: {prediction_goal}\n\n"
                f"Existing agents: {', '.join(existing_names)}\n\n"
                f"Generate {remaining} MORE unique agents who would participate in this discussion. "
                f"They should have different backgrounds and perspectives from the existing agents. "
                f"Return a JSON array."
            )

            try:
                extra = self._llm.complete_json(
                    messages=[
                        {"role": "system", "content": EXPAND_SYSTEM},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.8,
                    max_tokens=5000,
                )
            except Exception:
                extra = []

            if isinstance(extra, dict):
                extra = extra.get("profiles", extra.get("agents", []))
            if isinstance(extra, list):
                for p in extra:
                    if isinstance(p, dict) and p.get("entity_name"):
                        profiles.append(p)

        if progress_cb:
            progress_cb(len(profiles), target_count, f"{len(profiles)} agents ready")

        # Build final profiles with IDs
        final = []
        seen_names = set()
        for idx, p in enumerate(profiles):
            name = p.get("entity_name", f"Agent_{idx}")
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())

            # Match to graph entity if possible
            entity_uid = None
            entity_summary = p.get("bio", "")
            for e in entities:
                if e.name.lower() == name.lower():
                    entity_uid = e.uid
                    entity_summary = e.summary
                    break

            final.append({
                "agent_id": idx,
                "entity_uid": entity_uid,
                "entity_name": name,
                "entity_type": p.get("entity_type", "Person"),
                "entity_summary": entity_summary,
                "username": p.get("username", name.lower().replace(" ", "_")),
                "bio": p.get("bio", ""),
                "personality": p.get("personality", "neutral"),
                "stance": p.get("stance", "neutral"),
                "activity_level": p.get("activity_level", 0.5),
                "influence": p.get("influence", 0.5),
            })

        return final
