"""
Real Multi-Agent Simulation Engine

Each agent is an independent LLM persona that:
- Sees the social feed from previous rounds
- Decides what to post based on personality, stance, and relationships
- Can shift stance based on compelling arguments from others
- Maintains memory of the full conversation

This produces emergent behavior: clusters form, opinions shift,
consensus or polarization emerges naturally.
"""
import uuid
import threading
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..utils.llm_client import LLM
from ..models.knowledge_graph import KnowledgeGraph


# Per-agent system prompt
AGENT_SYSTEM = """You are {name}, a {entity_type}.
Background: {bio}
Personality: {personality}
Your initial stance on the topic: {stance}

You are participating in a social media discussion about:
"{topic}"

Rules:
- Stay in character. Your posts should reflect your background and personality.
- Write 1-2 sentences per post, like real social media.
- You may reply to specific people by starting with "@TheirName:"
- You can agree, disagree, add new information, or ask questions.
- If someone makes a compelling point, you can shift your position.
- Be specific and substantive. No vague platitudes.
- Never use em-dashes. Write plainly.

After reading the feed, write your next post. Return ONLY JSON:
{{
  "post": "your message",
  "reply_to": null or "name of person you're replying to",
  "current_stance": "supportive/opposing/neutral/shifted",
  "stance_reason": "1 sentence why you hold this stance now"
}}"""


_sim_states: Dict[str, Dict[str, Any]] = {}


def get_sim_state(sim_id: str) -> Optional[Dict[str, Any]]:
    return _sim_states.get(sim_id)


@dataclass
class Agent:
    """An individual agent in the simulation."""
    agent_id: int
    name: str
    entity_type: str
    bio: str
    personality: str
    stance: str
    influence: float = 0.5
    connections: List[str] = field(default_factory=list)
    memory: List[str] = field(default_factory=list)
    stance_history: List[Dict[str, str]] = field(default_factory=list)
    post_count: int = 0


class SimulationEngine:
    def __init__(self, llm: Optional[LLM] = None):
        self._llm = llm or LLM()

    def start(
        self,
        sim_id: str,
        profiles: List[Dict[str, Any]],
        graph: KnowledgeGraph,
        prediction_goal: str,
        total_rounds: int = 8,
        agents_per_round: int = 6,
        initial_prompt: str = "",
    ) -> Dict[str, Any]:
        state = {
            "sim_id": sim_id,
            "status": "running",
            "current_round": 0,
            "total_rounds": total_rounds,
            "posts": [],
            "actions": [],
            "started_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "error": None,
            "summary": "",
            "stance_shifts": [],
            "clusters": {},
        }
        _sim_states[sim_id] = state

        t = threading.Thread(
            target=self._run_simulation,
            args=(sim_id, profiles, graph, prediction_goal, total_rounds, agents_per_round, initial_prompt),
            daemon=True,
        )
        t.start()
        return state

    def _run_simulation(
        self, sim_id, profiles, graph, prediction_goal,
        total_rounds, agents_per_round, initial_prompt,
    ):
        state = _sim_states[sim_id]

        try:
            # Build agents from profiles
            agents = []
            for p in profiles:
                agent = Agent(
                    agent_id=p.get("agent_id", len(agents)),
                    name=p.get("entity_name", f"Agent_{len(agents)}"),
                    entity_type=p.get("entity_type", "Person"),
                    bio=p.get("bio", p.get("entity_summary", "")),
                    personality=p.get("personality", "analytical"),
                    stance=p.get("stance", "neutral"),
                    influence=p.get("influence", 0.5),
                    connections=[],
                )
                # Record initial stance
                agent.stance_history.append({
                    "round": 0,
                    "stance": agent.stance,
                    "reason": "Initial position",
                })
                agents.append(agent)

            # Build connections from graph relationships
            name_to_idx = {a.name.lower(): i for i, a in enumerate(agents)}
            for rel in graph.relationships.values():
                src_entity = graph.entities.get(rel.source_uid)
                tgt_entity = graph.entities.get(rel.target_uid)
                if src_entity and tgt_entity:
                    si = name_to_idx.get(src_entity.name.lower())
                    ti = name_to_idx.get(tgt_entity.name.lower())
                    if si is not None and ti is not None:
                        agents[si].connections.append(agents[ti].name)
                        agents[ti].connections.append(agents[si].name)

            all_posts = []
            feed_text = f"[SCENARIO] {initial_prompt or prediction_goal}"

            # Run rounds
            for round_num in range(1, total_rounds + 1):
                state["current_round"] = round_num

                # Select agents for this round
                # Prioritize agents with connections to recent posters, plus some random
                recent_names = set()
                for p in all_posts[-10:]:
                    recent_names.add(p["agent_name"])

                # Score agents: connected to recent posters get priority
                scored = []
                for a in agents:
                    score = random.random() * 0.3  # base randomness
                    if any(c in recent_names for c in a.connections):
                        score += 0.5  # connected to recent posters
                    if a.post_count == 0:
                        score += 0.3  # haven't spoken yet
                    scored.append((score, a))

                scored.sort(key=lambda x: -x[0])
                round_agents = [a for _, a in scored[:agents_per_round]]

                # Each agent posts independently
                round_posts = []
                for agent in round_agents:
                    try:
                        post_data = self._agent_post(
                            agent, prediction_goal, feed_text, round_num
                        )
                        if post_data and post_data.get("post"):
                            post = {
                                "post_id": f"p_{uuid.uuid4().hex[:8]}",
                                "round_num": round_num,
                                "agent_id": agent.agent_id,
                                "agent_name": agent.name,
                                "agent_type": agent.entity_type,
                                "content": post_data["post"],
                                "reply_to": post_data.get("reply_to"),
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "stance": post_data.get("current_stance", agent.stance),
                            }
                            round_posts.append(post)
                            agent.post_count += 1

                            # Track stance shifts
                            new_stance = post_data.get("current_stance", agent.stance)
                            if new_stance != agent.stance:
                                state["stance_shifts"].append({
                                    "agent": agent.name,
                                    "round": round_num,
                                    "from": agent.stance,
                                    "to": new_stance,
                                    "reason": post_data.get("stance_reason", ""),
                                })
                                agent.stance = new_stance

                            agent.stance_history.append({
                                "round": round_num,
                                "stance": new_stance,
                                "reason": post_data.get("stance_reason", ""),
                            })

                            # Add to agent memory
                            agent.memory.append(f"R{round_num}: I said: {post_data['post']}")

                    except Exception as e:
                        # Skip agent on error, don't crash simulation
                        print(f"Agent {agent.name} error in round {round_num}: {e}")
                        continue

                    # Delay between agent calls to respect rate limits
                    time.sleep(2)

                # Update feed with new posts
                for p in round_posts:
                    reply_prefix = f" (replying to @{p['reply_to']})" if p.get("reply_to") else ""
                    feed_text += f"\n[R{round_num}] {p['agent_name']}{reply_prefix}: {p['content']}"

                all_posts.extend(round_posts)
                state["posts"] = all_posts.copy()

                # Delay between rounds
                if round_num < total_rounds:
                    time.sleep(3)

            # Compute final clusters
            stance_groups = {}
            for a in agents:
                s = a.stance.lower()
                if s not in stance_groups:
                    stance_groups[s] = []
                stance_groups[s].append(a.name)
            state["clusters"] = stance_groups

            # Build actions list
            state["actions"] = [
                {
                    "round_num": p["round_num"],
                    "agent_id": p["agent_id"],
                    "agent_name": p["agent_name"],
                    "action_type": "POST",
                    "content": p["content"],
                }
                for p in all_posts
            ]

            state["status"] = "completed"
            state["completed_at"] = datetime.utcnow().isoformat() + "Z"

        except Exception as exc:
            state["status"] = "failed"
            state["error"] = str(exc)

    def _agent_post(self, agent: Agent, topic: str, feed: str, round_num: int) -> Dict:
        """Make a single agent post by calling the LLM with the agent's persona."""
        system = AGENT_SYSTEM.format(
            name=agent.name,
            entity_type=agent.entity_type,
            bio=agent.bio,
            personality=agent.personality,
            stance=agent.stance,
            topic=topic,
        )

        # Build context: recent feed + agent's own memory
        memory_text = ""
        if agent.memory:
            memory_text = "\n\nYour previous posts:\n" + "\n".join(agent.memory[-5:])

        connections_text = ""
        if agent.connections:
            connections_text = f"\n\nYou know these people: {', '.join(agent.connections[:10])}"

        user_msg = (
            f"Round {round_num}. Here is the discussion so far:\n\n"
            f"{feed[-3000:]}"  # Last 3000 chars of feed
            f"{memory_text}"
            f"{connections_text}"
            f"\n\nWrite your next post. Return JSON only."
        )

        result = self._llm.complete_json(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.8,
            max_tokens=300,
        )

        return result if isinstance(result, dict) else {}
