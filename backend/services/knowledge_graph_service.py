"""知识图谱加载、持久化与动态扩充服务。"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

import networkx as nx
from sqlalchemy.orm import Session

from ai_module.knowledge_graph import add_ontology_edge, add_ontology_node, build_pet_medical_graph, export_graph_for_viz, multi_hop_reasoning
from backend.models.core import KnowledgeEdge, KnowledgeNode

_GRAPH: nx.DiGraph | None = None


def get_graph() -> nx.DiGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_pet_medical_graph()
    return _GRAPH


def _safe_json(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {"value": value}
    return {"value": str(value)}


def _node_name(attrs: dict[str, object], node_id: str) -> str:
    return str(attrs.get("zh_name") or attrs.get("en_name") or node_id)


def seed_graph_to_db(db: Session) -> None:
    graph = get_graph()
    node_exists = db.query(KnowledgeNode.id).first() is not None
    edge_exists = db.query(KnowledgeEdge.id).first() is not None
    if node_exists and edge_exists:
        return

    now = datetime.utcnow()
    if not node_exists:
        node_rows = []
        for node_id, attrs in graph.nodes(data=True):
            node_rows.append(
                KnowledgeNode(
                    id=node_id,
                    node_type=str(attrs.get("node_type", "Unknown")),
                    data={k: v for k, v in attrs.items() if k != "node_type"},
                    created_at=now,
                    updated_at=now,
                )
            )
        db.bulk_save_objects(node_rows)

    if not edge_exists:
        edge_rows = []
        for source, target, attrs in graph.edges(data=True):
            edge_rows.append(
                KnowledgeEdge(
                    id=f"edge:{uuid4().hex}",
                    source_id=source,
                    target_id=target,
                    relation=str(attrs.get("relation", "related_to")),
                    confidence=float(attrs.get("confidence", attrs.get("weight", 1.0))),
                    data={k: v for k, v in attrs.items() if k not in {"relation", "confidence", "weight"}},
                    created_at=now,
                    updated_at=now,
                )
            )
        db.bulk_save_objects(edge_rows)

    db.commit()


def load_graph_from_db(db: Session) -> nx.DiGraph:
    graph = build_pet_medical_graph()

    for row in db.query(KnowledgeNode).all():
        attrs = _safe_json(row.data)
        add_ontology_node(graph, row.id, row.node_type, **attrs)

    for row in db.query(KnowledgeEdge).all():
        confidence = float(row.confidence or 0.0)
        add_ontology_edge(graph, row.source_id, row.target_id, row.relation, confidence)
        extra = _safe_json(row.data)
        for key, value in extra.items():
            graph.edges[row.source_id, row.target_id][key] = value

    global _GRAPH
    _GRAPH = graph
    return graph


def bootstrap_graph(db: Session) -> nx.DiGraph:
    seed_graph_to_db(db)
    return load_graph_from_db(db)


def add_node(db: Session, *, node_type: str, data: dict[str, object], node_id: str | None = None) -> dict[str, object]:
    graph = get_graph()
    node_id = node_id or f"{node_type.lower()}:{uuid4().hex[:12]}"
    add_ontology_node(graph, node_id, node_type, **data)
    row = KnowledgeNode(id=node_id, node_type=node_type, data=data)
    db.add(row)
    db.commit()
    return {"id": node_id, "node_type": node_type, "data": data}


def add_edge(
    db: Session,
    *,
    source_id: str,
    target_id: str,
    relation: str,
    confidence: float,
    data: dict[str, object] | None = None,
) -> dict[str, object]:
    graph = get_graph()
    add_ontology_edge(graph, source_id, target_id, relation, confidence)
    payload = data or {}
    for key, value in payload.items():
        graph.edges[source_id, target_id][key] = value

    row = KnowledgeEdge(
        id=f"edge:{uuid4().hex}",
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        confidence=confidence,
        data=payload,
    )
    db.add(row)
    db.commit()
    return {
        "id": row.id,
        "source_id": source_id,
        "target_id": target_id,
        "relation": relation,
        "confidence": confidence,
        "data": payload,
    }


def get_graph_viz(species: str | None = None, path: list[dict[str, object]] | None = None) -> dict[str, list[dict[str, object]]]:
    graph = get_graph()
    return export_graph_for_viz(graph, species_filter=species, highlighted_path=path)


def run_reasoning(symptoms: list[str], species: str, exam_results: dict[str, float] | None = None) -> dict[str, object]:
    graph = get_graph()
    result = multi_hop_reasoning(graph, symptoms, species, exam_results)

    id_to_name: dict[str, str] = {}
    for node_id, attrs in graph.nodes(data=True):
        id_to_name[node_id] = _node_name(attrs, node_id)

    named_path = []
    for item in result.get("graph_reasoning_path", []):
        source_id = str(item.get("from", ""))
        target_id = str(item.get("to", ""))
        named_path.append(
            {
                **item,
                "from_id": source_id,
                "to_id": target_id,
                "from_name": id_to_name.get(source_id, source_id),
                "to_name": id_to_name.get(target_id, target_id),
            }
        )
    result["graph_reasoning_path"] = named_path
    return result
