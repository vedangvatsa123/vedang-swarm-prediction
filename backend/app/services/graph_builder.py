"""
Graph Builder
Single-pass extraction — sends the entire text (truncated to fit) in ONE LLM call.
"""
import threading
from typing import Dict, Any, List, Optional

from ..utils.llm_client import LLM
from ..models.knowledge_graph import KnowledgeGraph

EXTRACTION_SYSTEM = """You are an entity and relationship extractor.
Given text and a schema, extract ALL entities and relationships.

For each entity: name, type (from schema), summary (1 sentence).
For each relationship: source, target, type (from schema), description.

Return JSON:
{
  "entities": [{"name": "...", "type": "...", "summary": "..."}],
  "relationships": [{"source": "...", "target": "...", "type": "...", "description": "..."}]
}"""

_graphs: Dict[str, KnowledgeGraph] = {}
_build_progress: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def get_graph(graph_id: str) -> Optional[KnowledgeGraph]:
    return _graphs.get(graph_id)


def get_build_progress(graph_id: str) -> Optional[Dict[str, Any]]:
    return _build_progress.get(graph_id)


class GraphBuilder:
    def __init__(self, llm: Optional[LLM] = None):
        self._llm = llm or LLM()

    def build_async(self, graph_id: str, text: str, ontology: Dict[str, Any]) -> str:
        _build_progress[graph_id] = {
            "status": "processing",
            "progress": 10,
            "message": "Extracting entities (single pass)…",
            "error": None,
        }
        t = threading.Thread(
            target=self._worker,
            args=(graph_id, text, ontology),
            daemon=True,
        )
        t.start()
        return graph_id

    def _worker(self, graph_id, text, ontology):
        try:
            graph = KnowledgeGraph()

            # Truncate to ~12k chars — fits in most local model contexts
            if len(text) > 12000:
                text = text[:12000] + "\n…(truncated)"

            type_names = [et["name"] for et in ontology.get("entity_types", [])]
            rel_names = [ed["name"] for ed in ontology.get("edge_types", [])]
            schema_desc = (
                f"Entity types: {', '.join(type_names)}\n"
                f"Relationship types: {', '.join(rel_names)}"
            )

            _build_progress[graph_id].update(progress=30, message="Waiting for LLM response…")

            user_msg = f"## Schema\n{schema_desc}\n\n## Full Text\n{text}\n\nExtract all entities and relationships. Return JSON only."
            extracted = self._llm.complete_json(
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=4000,
            )

            _build_progress[graph_id].update(progress=80, message="Building graph…")

            # Populate graph
            name_to_uid: Dict[str, str] = {}

            for ent in extracted.get("entities", []):
                name = ent.get("name", "").strip()
                if not name:
                    continue
                key = name.lower()
                if key not in name_to_uid:
                    e = graph.add_entity(name, ent.get("type", "Person"), ent.get("summary", ""))
                    name_to_uid[key] = e.uid

            for rel in extracted.get("relationships", []):
                src = rel.get("source", "").strip().lower()
                tgt = rel.get("target", "").strip().lower()
                if name_to_uid.get(src) and name_to_uid.get(tgt):
                    graph.add_relationship(
                        name_to_uid[src], name_to_uid[tgt],
                        rel.get("type", "RELATED_TO"),
                        rel.get("description", ""),
                    )

            with _lock:
                _graphs[graph_id] = graph

            _build_progress[graph_id] = {
                "status": "completed",
                "progress": 100,
                "message": f"Done — {len(graph.entities)} entities, {len(graph.relationships)} relationships",
                "error": None,
            }

        except Exception as exc:
            _build_progress[graph_id] = {
                "status": "failed",
                "progress": 0,
                "message": str(exc),
                "error": str(exc),
            }
