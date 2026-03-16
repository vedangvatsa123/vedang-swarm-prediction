"""
In-memory knowledge graph — no external graph database needed.
Stores entities (nodes) and relationships (edges) extracted by the LLM.
Provides search and traversal helpers for the report agent.
"""
import uuid
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict


@dataclass
class Entity:
    """A node in the knowledge graph."""
    uid: str
    name: str
    entity_type: str
    summary: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Relationship:
    """A directed edge between two entities."""
    uid: str
    source_uid: str
    target_uid: str
    relation_type: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class KnowledgeGraph:
    """
    Lightweight in-memory graph.
    Thread-safe enough for a single-server Flask app.
    """

    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        # Adjacency indices
        self._outgoing: Dict[str, Set[str]] = {}   # entity_uid → set of rel uids
        self._incoming: Dict[str, Set[str]] = {}

    # ── mutations ──────────────────────────────────────────────

    def add_entity(
        self,
        name: str,
        entity_type: str,
        summary: str = "",
        attributes: Optional[Dict[str, str]] = None,
    ) -> Entity:
        uid = f"e_{uuid.uuid4().hex[:10]}"
        ent = Entity(
            uid=uid,
            name=name,
            entity_type=entity_type,
            summary=summary,
            attributes=attributes or {},
        )
        self.entities[uid] = ent
        self._outgoing.setdefault(uid, set())
        self._incoming.setdefault(uid, set())
        return ent

    def add_relationship(
        self,
        source_uid: str,
        target_uid: str,
        relation_type: str,
        description: str = "",
    ) -> Relationship:
        uid = f"r_{uuid.uuid4().hex[:10]}"
        rel = Relationship(
            uid=uid,
            source_uid=source_uid,
            target_uid=target_uid,
            relation_type=relation_type,
            description=description,
        )
        self.relationships[uid] = rel
        self._outgoing.setdefault(source_uid, set()).add(uid)
        self._incoming.setdefault(target_uid, set()).add(uid)
        return rel

    # ── queries ────────────────────────────────────────────────

    def find_entity_by_name(self, name: str) -> Optional[Entity]:
        name_lower = name.lower()
        for ent in self.entities.values():
            if ent.name.lower() == name_lower:
                return ent
        return None

    def entities_of_type(self, etype: str) -> List[Entity]:
        return [e for e in self.entities.values() if e.entity_type == etype]

    def neighbours(self, entity_uid: str) -> List[Dict[str, Any]]:
        """Return all directly connected entities with edge info."""
        results = []
        for rid in self._outgoing.get(entity_uid, []):
            rel = self.relationships[rid]
            target = self.entities.get(rel.target_uid)
            if target:
                results.append({"direction": "outgoing", "relation": rel.to_dict(), "entity": target.to_dict()})
        for rid in self._incoming.get(entity_uid, []):
            rel = self.relationships[rid]
            source = self.entities.get(rel.source_uid)
            if source:
                results.append({"direction": "incoming", "relation": rel.to_dict(), "entity": source.to_dict()})
        return results

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Simple keyword search across entity names and summaries."""
        query_lower = query.lower()
        scored = []
        for ent in self.entities.values():
            score = 0
            if query_lower in ent.name.lower():
                score += 3
            if query_lower in ent.summary.lower():
                score += 1
            if query_lower in ent.entity_type.lower():
                score += 1
            if score > 0:
                scored.append((score, ent))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e.to_dict() for _, e in scored[:limit]]

    # ── serialisation ──────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities.values()],
            "relationships": [r.to_dict() for r in self.relationships.values()],
            "entity_count": len(self.entities),
            "relationship_count": len(self.relationships),
        }

    def entity_type_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.entities.values():
            counts[e.entity_type] = counts.get(e.entity_type, 0) + 1
        return counts
