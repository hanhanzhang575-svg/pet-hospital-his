"""NetworkX兽医知识图谱与推理模块。"""

from __future__ import annotations

from collections import defaultdict

import networkx as nx

SPECIES_FORBIDDEN: dict[str, list[str]] = {
    "猫": ["对乙酰氨基酚", "阿司匹林", "布洛芬"],
    "犬": ["木糖醇", "葡萄提取物"],
    "兔": ["青霉素类抗生素"],
}


def add_ontology_node(graph: nx.DiGraph, node_id: str, node_type: str, **attrs) -> None:
    graph.add_node(node_id, node_type=node_type, **attrs)


def add_ontology_edge(
    graph: nx.DiGraph,
    source: str,
    target: str,
    relation: str,
    confidence: float,
) -> None:
    graph.add_edge(source, target, relation=relation, weight=confidence, confidence=confidence)


def _seed_species_nodes(graph: nx.DiGraph) -> None:
    for species_name in ["犬", "猫", "兔", "其他"]:
        add_ontology_node(
            graph,
            f"species:{species_name}",
            "SpeciesNode",
            zh_name=species_name,
            en_name={"犬": "dog", "猫": "cat", "兔": "rabbit", "其他": "other"}.get(species_name, "other"),
        )


def build_pet_medical_graph() -> nx.DiGraph:
    """构建异构兽医图谱：症状/疾病/治疗/检查/药物/物种。"""
    graph = nx.DiGraph()
    _seed_species_nodes(graph)

    symptom_nodes = [
        ("symptom:vomiting", "呕吐", "vomiting", ["犬", "猫"], "消化系统"),
        ("symptom:diarrhea", "腹泻", "diarrhea", ["犬", "猫", "兔"], "消化系统"),
        ("symptom:fever", "发热", "fever", ["犬", "猫", "兔"], "全身"),
        ("symptom:cough", "咳嗽", "cough", ["犬", "猫"], "呼吸系统"),
        ("symptom:anorexia", "食欲废绝", "anorexia", ["犬", "猫", "兔"], "消化系统"),
        ("symptom:lameness", "跛行", "lameness", ["犬", "猫"], "运动系统"),
        ("symptom:jaundice", "黄疸", "jaundice", ["犬", "猫"], "肝胆系统"),
    ]
    for node_id, zh_name, en_name, species, organ_system in symptom_nodes:
        add_ontology_node(
            graph,
            node_id,
            "SymptomNode",
            zh_name=zh_name,
            en_name=en_name,
            applicable_species=species,
            organ_system=organ_system,
        )

    disease_nodes = [
        ("disease:parvovirus", "犬细小病毒", "canine parvovirus", ["犬"], True, "critical"),
        ("disease:distemper", "犬瘟热", "canine distemper", ["犬"], True, "high"),
        ("disease:pancreatitis", "胰腺炎", "pancreatitis", ["犬", "猫"], False, "high"),
        ("disease:hepatitis", "肝炎", "hepatitis", ["犬", "猫"], False, "high"),
        ("disease:osteoarthritis", "骨关节炎", "osteoarthritis", ["犬", "猫"], False, "medium"),
        ("disease:uti", "尿路感染", "urinary tract infection", ["犬", "猫"], False, "medium"),
        ("disease:feline_uri", "猫上呼吸道感染", "feline URI", ["猫"], True, "medium"),
    ]
    for node_id, zh_name, en_name, species, infectious, severity in disease_nodes:
        add_ontology_node(
            graph,
            node_id,
            "DiseaseNode",
            zh_name=zh_name,
            en_name=en_name,
            high_incidence_species=species,
            infectious=infectious,
            severity_level=severity,
        )

    treatment_nodes = [
        ("treatment:fluid_support", "补液支持", "fluid support"),
        ("treatment:respiratory_support", "呼吸支持", "respiratory support"),
        ("treatment:liver_protection", "保肝治疗", "liver protection"),
        ("treatment:pain_control", "镇痛治疗", "pain control"),
    ]
    for node_id, zh_name, en_name in treatment_nodes:
        add_ontology_node(graph, node_id, "TreatmentNode", zh_name=zh_name, en_name=en_name)

    exam_nodes = [
        ("exam:wbc", "白细胞", "WBC", {"dog": [6.0, 17.0], "cat": [5.5, 19.5], "rabbit": [5.0, 12.0]}),
        ("exam:alt", "谷丙转氨酶", "ALT", {"dog": [10.0, 90.0], "cat": [20.0, 100.0], "rabbit": [20.0, 80.0]}),
    ]
    for node_id, zh_name, en_name, reference_range in exam_nodes:
        add_ontology_node(
            graph,
            node_id,
            "ExamNode",
            zh_name=zh_name,
            en_name=en_name,
            reference_range=reference_range,
        )

    drug_nodes = [
        ("drug:ceftriaxone", "头孢曲松", "ceftriaxone", "抗菌药", [], ["阿莫西林"]),
        ("drug:amoxicillin", "阿莫西林", "amoxicillin", "抗菌药", [], ["头孢曲松"]),
        ("drug:metronidazole", "甲硝唑", "metronidazole", "抗菌药", [], []),
        ("drug:meloxicam", "美洛昔康", "meloxicam", "NSAIDs", [], ["阿司匹林"]),
        ("drug:hepatoprotective", "保肝药", "hepatoprotective", "保肝药", [], []),
        ("drug:antiemetic", "止吐药", "antiemetic", "对症支持", [], []),
        ("drug:acetaminophen", "对乙酰氨基酚", "acetaminophen", "解热镇痛", ["猫"], []),
        ("drug:aspirin", "阿司匹林", "aspirin", "NSAIDs", ["猫"], ["美洛昔康", "布洛芬"]),
        ("drug:ibuprofen", "布洛芬", "ibuprofen", "NSAIDs", ["猫"], ["阿司匹林"]),
        ("drug:xylitol", "木糖醇", "xylitol", "其他", ["犬"], []),
        ("drug:grape_extract", "葡萄提取物", "grape extract", "其他", ["犬"], []),
        ("drug:penicillin", "青霉素类抗生素", "penicillin", "抗菌药", ["兔"], []),
    ]
    for node_id, zh_name, en_name, category, forbidden_species, incompatibility in drug_nodes:
        add_ontology_node(
            graph,
            node_id,
            "DrugNode",
            zh_name=zh_name,
            en_name=en_name,
            drug_category=category,
            forbidden_species=forbidden_species,
            compatibility_issues=incompatibility,
        )

    symptom_to_disease = [
        ("symptom:vomiting", "disease:parvovirus", 0.92),
        ("symptom:diarrhea", "disease:parvovirus", 0.90),
        ("symptom:fever", "disease:distemper", 0.87),
        ("symptom:cough", "disease:feline_uri", 0.82),
        ("symptom:anorexia", "disease:pancreatitis", 0.80),
        ("symptom:jaundice", "disease:hepatitis", 0.88),
        ("symptom:lameness", "disease:osteoarthritis", 0.78),
    ]
    for symptom, disease, confidence in symptom_to_disease:
        add_ontology_edge(graph, symptom, disease, "symptom_indicates_disease", confidence)

    exam_to_disease = [
        ("exam:alt", "disease:hepatitis", 0.85),
        ("exam:wbc", "disease:uti", 0.70),
    ]
    for exam, disease, confidence in exam_to_disease:
        add_ontology_edge(graph, exam, disease, "exam_supports_disease", confidence)

    disease_to_treatment = [
        ("disease:parvovirus", "treatment:fluid_support", 0.95),
        ("disease:distemper", "treatment:respiratory_support", 0.90),
        ("disease:hepatitis", "treatment:liver_protection", 0.93),
        ("disease:osteoarthritis", "treatment:pain_control", 0.89),
    ]
    for disease, treatment, confidence in disease_to_treatment:
        add_ontology_edge(graph, disease, treatment, "disease_recommends_treatment", confidence)

    disease_to_drug = [
        ("disease:parvovirus", "drug:antiemetic", 0.86),
        ("disease:uti", "drug:ceftriaxone", 0.84),
        ("disease:pancreatitis", "drug:metronidazole", 0.72),
        ("disease:osteoarthritis", "drug:meloxicam", 0.81),
        ("disease:hepatitis", "drug:hepatoprotective", 0.90),
    ]
    for disease, drug, confidence in disease_to_drug:
        add_ontology_edge(graph, disease, drug, "disease_recommends_drug", confidence)

    treatment_to_drug = [
        ("treatment:fluid_support", "drug:antiemetic", 0.70),
        ("treatment:liver_protection", "drug:hepatoprotective", 0.92),
        ("treatment:pain_control", "drug:meloxicam", 0.80),
    ]
    for treatment, drug, confidence in treatment_to_drug:
        add_ontology_edge(graph, treatment, drug, "treatment_uses_drug", confidence)

    contraindications = [
        ("drug:ceftriaxone", "drug:amoxicillin", -0.85),
        ("drug:meloxicam", "drug:aspirin", -0.92),
        ("drug:ibuprofen", "drug:aspirin", -0.90),
    ]
    for drug_a, drug_b, confidence in contraindications:
        add_ontology_edge(graph, drug_a, drug_b, "drug_contraindication", confidence)
        add_ontology_edge(graph, drug_b, drug_a, "drug_contraindication", confidence)

    for species, forbidden_drugs in SPECIES_FORBIDDEN.items():
        species_node = f"species:{species}"
        for drug_zh in forbidden_drugs:
            for node_id, attrs in graph.nodes(data=True):
                if attrs.get("node_type") == "DrugNode" and attrs.get("zh_name") == drug_zh:
                    add_ontology_edge(graph, species_node, node_id, "species_drug_forbidden", -1.0)

    return graph


def parse_knowledge_item(item: str) -> tuple[list[str], str, str, str]:
    """解析“症状→疾病→推荐用药→禁忌药物”文本。"""
    parts = item.split("→")
    while len(parts) < 4:
        parts.append("")
    symptom_text, disease, recommendation, forbidden = parts[:4]
    symptoms = [x.strip() for x in symptom_text.split("+") if x.strip()]
    return symptoms, disease.strip(), recommendation.strip(), forbidden.strip()


def validate_with_graph(
    graph: nx.DiGraph,
    species: str,
    knowledge_items: list[str],
) -> dict[str, list[str]]:
    """将候选疾病/用药通过图谱约束过滤。"""
    disease_candidates: list[str] = []
    recommended_drugs: list[str] = []
    forbidden_drugs = set(SPECIES_FORBIDDEN.get(species, []))

    for item in knowledge_items:
        _symptoms, disease, recommendation, forbidden = parse_knowledge_item(item)
        if disease:
            disease_candidates.append(disease)
        for token in recommendation.replace("、", "+").replace("/", "+").split("+"):
            token = token.strip()
            if token:
                recommended_drugs.append(token)
        for token in forbidden.replace("、", "+").replace("/", "+").split("+"):
            token = token.strip()
            if token:
                forbidden_drugs.add(token)

    dedup_diseases = list(dict.fromkeys(disease_candidates))
    dedup_drugs = list(dict.fromkeys(recommended_drugs))
    dedup_forbidden = list(dict.fromkeys(forbidden_drugs))
    legal_drugs = [drug for drug in dedup_drugs if drug not in dedup_forbidden]
    blocked_drugs = [drug for drug in dedup_drugs if drug in dedup_forbidden]

    return {
        "disease_candidates": dedup_diseases,
        "recommended_drugs": legal_drugs,
        "blocked_drugs": blocked_drugs,
        "species_forbidden_drugs": SPECIES_FORBIDDEN.get(species, []),
    }


def _find_node_ids_by_names(graph: nx.DiGraph, names: list[str], node_type: str) -> list[str]:
    normalized = {n.strip().lower() for n in names if n.strip()}
    matched = []
    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("node_type") != node_type:
            continue
        zh_name = str(attrs.get("zh_name", "")).strip().lower()
        en_name = str(attrs.get("en_name", "")).strip().lower()
        if zh_name in normalized or en_name in normalized:
            matched.append(node_id)
    return matched


def multi_hop_reasoning(
    graph: nx.DiGraph,
    symptom_list: list[str],
    species: str,
    exam_results: dict[str, float] | None = None,
) -> dict[str, object]:
    """输出 症状->疾病->治疗->药物->禁忌 的多跳链路。"""
    exam_results = exam_results or {}
    symptom_nodes = _find_node_ids_by_names(graph, symptom_list, "SymptomNode")
    if not symptom_nodes:
        return {
            "candidate_diseases": [],
            "recommended_treatments": [],
            "recommended_drugs": [],
            "forbidden_drugs": SPECIES_FORBIDDEN.get(species, []),
            "graph_reasoning_path": [],
        }

    disease_score: dict[str, float] = defaultdict(float)
    path_edges: list[dict[str, object]] = []

    for symptom in symptom_nodes:
        for _, disease, edge in graph.out_edges(symptom, data=True):
            if edge.get("relation") != "symptom_indicates_disease":
                continue
            disease_score[disease] += float(edge.get("confidence", edge.get("weight", 0.0)))
            path_edges.append({
                "from": symptom,
                "to": disease,
                "relation": edge.get("relation"),
                "confidence": round(float(edge.get("confidence", edge.get("weight", 0.0))), 4),
            })

    if exam_results:
        for exam_key, exam_value in exam_results.items():
            exam_nodes = _find_node_ids_by_names(graph, [exam_key], "ExamNode")
            for exam_node in exam_nodes:
                reference_range = graph.nodes[exam_node].get("reference_range", {})
                sp_key = {"犬": "dog", "猫": "cat", "兔": "rabbit"}.get(species, "dog")
                ranges = reference_range.get(sp_key) or []
                abnormal = False
                if len(ranges) == 2:
                    abnormal = float(exam_value) < float(ranges[0]) or float(exam_value) > float(ranges[1])
                for _, disease, edge in graph.out_edges(exam_node, data=True):
                    if edge.get("relation") == "exam_supports_disease" and abnormal:
                        disease_score[disease] += float(edge.get("confidence", edge.get("weight", 0.0)))
                        path_edges.append({
                            "from": exam_node,
                            "to": disease,
                            "relation": edge.get("relation"),
                            "confidence": round(float(edge.get("confidence", edge.get("weight", 0.0))), 4),
                        })

    ranked_diseases_raw = [k for k, _ in sorted(disease_score.items(), key=lambda x: x[1], reverse=True)]
    ranked_diseases: list[str] = []
    for disease in ranked_diseases_raw:
        incidence = graph.nodes[disease].get("high_incidence_species", [])
        if species in {"犬", "猫"} and isinstance(incidence, list) and incidence and species not in incidence:
            continue
        ranked_diseases.append(disease)
        if len(ranked_diseases) >= 5:
            break

    recommended_treatments: list[str] = []
    recommended_drugs: list[str] = []
    forbidden_drugs: set[str] = set(SPECIES_FORBIDDEN.get(species, []))

    for disease in ranked_diseases:
        disease_attrs = graph.nodes[disease]
        for _, treatment, edge in graph.out_edges(disease, data=True):
            if edge.get("relation") == "disease_recommends_treatment":
                recommended_treatments.append(str(graph.nodes[treatment].get("zh_name", treatment)))
                path_edges.append({
                    "from": disease,
                    "to": treatment,
                    "relation": edge.get("relation"),
                    "confidence": round(float(edge.get("confidence", edge.get("weight", 0.0))), 4),
                })
                for _, tdrug, tedge in graph.out_edges(treatment, data=True):
                    if tedge.get("relation") == "treatment_uses_drug":
                        recommended_drugs.append(str(graph.nodes[tdrug].get("zh_name", tdrug)))
                        path_edges.append({
                            "from": treatment,
                            "to": tdrug,
                            "relation": tedge.get("relation"),
                            "confidence": round(float(tedge.get("confidence", tedge.get("weight", 0.0))), 4),
                        })

        for _, drug, edge in graph.out_edges(disease, data=True):
            if edge.get("relation") == "disease_recommends_drug":
                drug_name = str(graph.nodes[drug].get("zh_name", drug))
                recommended_drugs.append(drug_name)
                path_edges.append({
                    "from": disease,
                    "to": drug,
                    "relation": edge.get("relation"),
                    "confidence": round(float(edge.get("confidence", edge.get("weight", 0.0))), 4),
                })
                for forbidden_species in graph.nodes[drug].get("forbidden_species", []):
                    if forbidden_species == species:
                        forbidden_drugs.add(drug_name)
                        path_edges.append({
                            "from": f"species:{species}",
                            "to": drug,
                            "relation": "species_drug_forbidden",
                            "confidence": -1.0,
                        })
                for _, conflict_drug, cedge in graph.out_edges(drug, data=True):
                    if cedge.get("relation") == "drug_contraindication":
                        conflict_name = str(graph.nodes[conflict_drug].get("zh_name", conflict_drug))
                        forbidden_drugs.add(conflict_name)
                        path_edges.append({
                            "from": drug,
                            "to": conflict_drug,
                            "relation": "drug_contraindication",
                            "confidence": round(float(cedge.get("confidence", cedge.get("weight", -1.0))), 4),
                        })

        if species not in disease_attrs.get("high_incidence_species", [species]):
            disease_score[disease] *= 0.85

    candidate_diseases = [
        {
            "name": str(graph.nodes[disease].get("zh_name", disease)),
            "score": round(float(disease_score.get(disease, 0.0)), 4),
            "severity_level": graph.nodes[disease].get("severity_level", "medium"),
            "infectious": bool(graph.nodes[disease].get("infectious", False)),
        }
        for disease in ranked_diseases
    ]

    dedup_treatments = list(dict.fromkeys(recommended_treatments))
    dedup_drugs = list(dict.fromkeys(recommended_drugs))
    dedup_forbidden = list(dict.fromkeys(forbidden_drugs))
    legal_drugs = [d for d in dedup_drugs if d not in dedup_forbidden]

    return {
        "candidate_diseases": candidate_diseases,
        "recommended_treatments": dedup_treatments,
        "recommended_drugs": legal_drugs,
        "forbidden_drugs": dedup_forbidden,
        "graph_reasoning_path": path_edges,
    }


def export_graph_for_viz(
    graph: nx.DiGraph,
    species_filter: str | None = None,
    highlighted_path: list[dict[str, object]] | None = None,
) -> dict[str, list[dict[str, object]]]:
    """导出前端ECharts需要的节点边结构，支持物种过滤和路径高亮。"""
    highlighted_path = highlighted_path or []
    highlighted_pairs = {(p.get("from"), p.get("to")) for p in highlighted_path}

    hidden_drugs = set(SPECIES_FORBIDDEN.get(species_filter or "", []))
    nodes: list[dict[str, object]] = []
    for node_id, attrs in graph.nodes(data=True):
        zh_name = str(attrs.get("zh_name", node_id))
        if attrs.get("node_type") == "DrugNode" and species_filter and zh_name in hidden_drugs:
            continue
        if attrs.get("node_type") == "SymptomNode" and species_filter:
            applicable = attrs.get("applicable_species", [])
            if isinstance(applicable, list) and applicable and species_filter not in applicable:
                continue
        if attrs.get("node_type") == "DiseaseNode" and species_filter:
            incidence = attrs.get("high_incidence_species", [])
            if isinstance(incidence, list) and incidence and species_filter not in incidence:
                continue
        if attrs.get("node_type") == "SpeciesNode" and species_filter:
            if str(attrs.get("zh_name", "")) != species_filter:
                continue
        nodes.append(
            {
                "id": node_id,
                "name": zh_name,
                "zh_name": attrs.get("zh_name", zh_name),
                "en_name": attrs.get("en_name", ""),
                "node_type": attrs.get("node_type", "Unknown"),
                "severity_level": attrs.get("severity_level", ""),
                "applicable_species": attrs.get("applicable_species") or attrs.get("high_incidence_species") or [],
                "highlighted": any(pair[0] == node_id or pair[1] == node_id for pair in highlighted_pairs),
            }
        )

    visible_node_ids = {n["id"] for n in nodes}
    links: list[dict[str, object]] = []
    for source, target, attrs in graph.edges(data=True):
        if source not in visible_node_ids or target not in visible_node_ids:
            continue
        links.append(
            {
                "source": source,
                "target": target,
                "relation": attrs.get("relation"),
                "confidence": attrs.get("confidence", attrs.get("weight", 0.0)),
                "highlighted": (source, target) in highlighted_pairs,
            }
        )

    return {"nodes": nodes, "links": links}


