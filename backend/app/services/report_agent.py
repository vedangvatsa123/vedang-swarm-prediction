"""
Report Agent — single-call mode.
Generates the entire report in ONE LLM call.
"""
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLM
from ..models.knowledge_graph import KnowledgeGraph

REPORT_SYSTEM = """You are writing a prediction report based on a simulated discussion.
You have simulation data showing how different agents reacted to a scenario.

Write a structured report in Markdown with:
1. An executive summary (2-3 sentences)
2. Key findings (what the agents predicted/debated)
3. Points of agreement and disagreement
4. Risk factors identified
5. Overall prediction

Rules:
- Use > blockquotes to cite agent statements
- Use **bold** for key terms
- Write 400-800 words total
- Be specific, reference actual agent positions
- No heading for the title (it's added separately)

Writing style rules (MANDATORY):
- NEVER use em-dashes. Use commas, periods, or semicolons instead.
- NEVER use these words: delve, tapestry, landscape, utilize, leverage, multifaceted, nuanced, paradigm, synergy, holistic, robust, ecosystem, stakeholder, streamline, pivotal, moreover, furthermore, comprehensive, intricate, foster, underscore, realm
- Write plainly and directly like a journalist, not like a corporate report
- Short sentences. No filler. Every sentence must add information."""

CHAT_SYSTEM = """You are the Vedang Report Agent. Answer questions about this simulation.
Be specific, cite agent posts when relevant.
NEVER use em-dashes. Write plainly and directly. No corporate jargon.

Simulation data:
{context}"""


class ReportAgent:
    def __init__(self, llm: Optional[LLM] = None):
        self._llm = llm or LLM()

    def generate_full_report(
        self,
        prediction_goal: str,
        sim_summary: Dict[str, Any],
        graph: KnowledgeGraph,
        progress_cb=None,
    ) -> Dict[str, Any]:
        if progress_cb:
            progress_cb(0, "Writing report...")

        facts = self._gather_facts(sim_summary, graph)

        user_msg = (
            f"Prediction goal: {prediction_goal}\n\n"
            f"Simulation data:\n{facts[:8000]}\n\n"
            f"Write the full prediction report in Markdown."
        )

        markdown = self._llm.complete(
            messages=[
                {"role": "system", "content": REPORT_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.5,
            max_tokens=3000,
        )

        # Strip em-dashes and clean up
        markdown = self._clean_text(markdown)

        # Add title
        full_md = f"# Prediction Report\n\n{markdown}"

        if progress_cb:
            progress_cb(100, "Report complete")

        return {
            "outline": {"title": "Prediction Report"},
            "markdown": full_md,
        }

    def chat(
        self,
        question: str,
        sim_summary: Dict[str, Any],
        graph: KnowledgeGraph,
        history: List[Dict[str, str]] = None,
    ) -> str:
        context = self._gather_facts(sim_summary, graph)
        system = CHAT_SYSTEM.format(context=context[:8000])

        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": question})

        answer = self._llm.complete(messages=messages, temperature=0.6, max_tokens=1500)
        return self._clean_text(answer)

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove em-dashes and AI slop patterns."""
        # Replace em-dashes with commas or hyphens
        text = text.replace('\u2014', ', ')   # —
        text = text.replace('\u2013', '-')     # –
        text = text.replace(' , ,', ',')       # clean double commas
        text = text.replace(',,', ',')
        return text

    @staticmethod
    def _gather_facts(sim_summary: Dict[str, Any], graph: KnowledgeGraph) -> str:
        lines = []

        # Entity overview
        for etype, cnt in graph.entity_type_counts().items():
            lines.append(f"- {etype}: {cnt}")

        # Posts
        posts = sim_summary.get("posts", [])
        if posts:
            lines.append("\n## Discussion Posts")
            for p in posts[-40:]:
                stance_tag = f" [{p.get('stance','')}]" if p.get('stance') else ""
                reply_tag = f" (replying to {p.get('reply_to')})" if p.get('reply_to') else ""
                lines.append(f"[R{p.get('round_num',0)}] {p.get('agent_name','?')}{stance_tag}{reply_tag}: {p.get('content','')}")

        # Stance shifts
        shifts = sim_summary.get("stance_shifts", [])
        if shifts:
            lines.append("\n## Stance Shifts (agents who changed position)")
            for s in shifts:
                lines.append(f"- {s['agent']} shifted from {s['from']} to {s['to']} in round {s['round']}: {s.get('reason','')}")

        # Clusters
        clusters = sim_summary.get("clusters", {})
        if clusters:
            lines.append("\n## Final Stance Clusters")
            for stance, members in clusters.items():
                lines.append(f"- {stance}: {', '.join(members)}")

        # Action counts
        actions = sim_summary.get("actions", [])
        if actions:
            counts: Dict[str, int] = {}
            for a in actions:
                at = a.get("action_type", "UNKNOWN")
                counts[at] = counts.get(at, 0) + 1
            lines.append("\n## Action Summary")
            for at, cnt in counts.items():
                lines.append(f"- {at}: {cnt}")

        return "\n".join(lines)
