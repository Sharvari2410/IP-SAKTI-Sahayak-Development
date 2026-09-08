from typing import Any, Dict, List, Set, Tuple
import re


STOP_WORDS = {
    "a", "an", "and", "are", "does", "for", "how", "in", "is", "of", "the", "to", "what"
}

MEANINGFUL_PHRASES = (
    "traditional knowledge",
    "inventive step",
    "prior art",
    "patent application",
    "patent requirements",
    "regulatory requirements",
    "ayurveda aahara",
    "food business operator",
    "section 3(p)",
    "section 3(a)",
    "section 3(d)",
)

MEANINGFUL_TERMS = {
    "ayurveda", "aahara", "formulation", "patent", "patenting", "patented", "patents",
    "novelty", "regulatory", "requirements", "invention", "inventions", "food", "business",
    "operator", "traditional", "knowledge", "prior", "art", "inventive", "step",
}

SECTION_PATTERN = re.compile(r"\b(?:section\s+)?\d+[a-z]?\s*\([a-z]\)", re.IGNORECASE)
BARE_SECTION_PATTERN = re.compile(r"\(\s*[a-z]\s*\)", re.IGNORECASE)


def _normalize(text: Any) -> str:
    return re.sub(r"[^a-z0-9()/%\s]", " ", str(text or "").lower())


def _related_term(term: str) -> str:
    if term in {"patents", "patenting", "patented"}:
        return "patent"
    if term in {"inventions"}:
        return "invention"
    return term


def _query_sections(query: str) -> Set[str]:
    return {
        re.sub(r"\s+", "", match.group(0).lower().replace("section", ""))
        for match in SECTION_PATTERN.finditer(query)
    }


def _text_sections(text: str) -> Set[str]:
    sections = _query_sections(text)
    if re.search(r"\b(?:traditional knowledge|invention|patent)\w*\b", text, re.IGNORECASE):
        sections.update(match.group(0).replace(" ", "").lower() for match in BARE_SECTION_PATTERN.finditer(text))
    return sections


def _lexical_boost(query: str, text: str) -> float:
    normalized_query = _normalize(query)
    normalized_text = _normalize(text)
    if not normalized_query or not normalized_text:
        return 0.0

    boost = 0.0
    query_sections = _query_sections(query)
    text_sections = _text_sections(text)
    contextual_parenthetical_match = any(
        section[-3:] in text_sections
        for section in query_sections
    )
    if query_sections & text_sections or contextual_parenthetical_match:
        boost += 0.12

    matched_phrases = {
        phrase for phrase in MEANINGFUL_PHRASES
        if phrase in normalized_query and phrase in normalized_text
    }
    boost += min(0.08, 0.04 * len(matched_phrases))

    query_terms = {
        _related_term(term)
        for term in re.findall(r"[a-z0-9]+", normalized_query)
        if term not in STOP_WORDS and (_related_term(term) in MEANINGFUL_TERMS)
    }
    text_terms = set(re.findall(r"[a-z0-9]+", normalized_text))
    matched_terms = {term for term in query_terms if term in text_terms or term == "patent" and any(item.startswith("patent") for item in text_terms)}
    boost += min(0.10, 0.025 * len(matched_terms))

    return min(0.15, boost)


def lexical_score(query: str, text: str) -> float:
    """Return a normalized lexical/domain score for a chunk."""
    normalized_query = _normalize(query)
    normalized_text = _normalize(text)
    if not normalized_query or not normalized_text:
        return 0.0

    score = 0.0
    query_sections = _query_sections(query)
    text_sections = _text_sections(text)
    if query_sections & text_sections or any(section[-3:] in text_sections for section in query_sections):
        score += 0.65

    matched_phrases = {
        phrase for phrase in MEANINGFUL_PHRASES
        if phrase in normalized_query and phrase in normalized_text
    }
    score += min(0.30, 0.15 * len(matched_phrases))

    query_terms = {
        _related_term(term)
        for term in re.findall(r"[a-z0-9]+", normalized_query)
        if term not in STOP_WORDS and _related_term(term) in MEANINGFUL_TERMS
    }
    text_terms = set(re.findall(r"[a-z0-9]+", normalized_text))
    matched_terms = {
        term for term in query_terms
        if term in text_terms or term == "patent" and any(item.startswith("patent") for item in text_terms)
    }
    score += min(0.25, 0.05 * len(matched_terms))
    return min(1.0, score)


def _result_list(results: Dict[str, Any], key: str) -> List[Any]:
    value = results.get(key)
    if not isinstance(value, list) or not value or not isinstance(value[0], list):
        return []
    return value[0]


def _candidate_from_result(results: Dict[str, Any], index: int) -> Dict[str, Any] | None:
    identifiers = _result_list(results, "ids")
    documents = _result_list(results, "documents")
    if index >= len(identifiers) or index >= len(documents) or identifiers[index] in (None, ""):
        return None
    metadatas = _result_list(results, "metadatas")
    distances = _result_list(results, "distances")
    distance = distances[index] if index < len(distances) and isinstance(distances[index], (int, float)) else 0.0
    return {
        "id": str(identifiers[index]),
        "text": str(documents[index] or ""),
        "metadata": metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {},
        "distance": distance,
        "relevance_score": 1 - distance,
    }


def lexical_retrieve(query: str, vector_store: Any, limit: int = 30) -> List[Dict[str, Any]]:
    """Scan the existing Chroma documents for deterministic lexical candidates."""
    try:
        stored = vector_store.collection.get(include=["documents", "metadatas"])
    except Exception:
        return []

    identifiers = stored.get("ids") if isinstance(stored, dict) else []
    documents = stored.get("documents") if isinstance(stored, dict) else []
    metadatas = stored.get("metadatas") if isinstance(stored, dict) else []
    if not isinstance(identifiers, list) or not isinstance(documents, list):
        return []

    candidates: List[Tuple[float, int, Dict[str, Any]]] = []
    for index, identifier in enumerate(identifiers):
        if index >= len(documents) or identifier in (None, ""):
            continue
        text = str(documents[index] or "")
        score = lexical_score(query, text)
        if score <= 0:
            continue
        metadata = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
        candidates.append((score, index, {
            "id": str(identifier),
            "text": text,
            "metadata": metadata,
            "distance": None,
            "relevance_score": 0.0,
        }))

    candidates.sort(key=lambda item: (-item[0], item[1]))
    for score, _, candidate in candidates[:limit]:
        candidate["lexical_score"] = score
    return [candidate for _, _, candidate in candidates[:limit]]


def hybrid_rank_retrieved_chunks(
    query: str,
    semantic_results: Dict[str, Any],
    lexical_candidates: List[Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Merge semantic and lexical candidates and return transparently reranked results."""
    merged: Dict[str, Dict[str, Any]] = {}
    semantic_rows = [_candidate_from_result(semantic_results, index) for index in range(len(_result_list(semantic_results, "ids")))]
    for candidate in semantic_rows:
        if candidate is not None:
            candidate["semantic_score"] = candidate["relevance_score"]
            candidate["lexical_score"] = lexical_score(query, candidate["text"])
            merged[candidate["id"]] = candidate

    for candidate in lexical_candidates:
        identifier = candidate.get("id")
        if not identifier:
            continue
        if identifier in merged:
            merged[identifier]["lexical_score"] = max(merged[identifier].get("lexical_score", 0.0), candidate.get("lexical_score", 0.0))
            merged[identifier]["retrieval_overlap"] = True
        else:
            lexical_candidate = dict(candidate)
            lexical_candidate["semantic_score"] = 0.0
            lexical_candidate["lexical_score"] = candidate.get("lexical_score", lexical_score(query, candidate.get("text", "")))
            lexical_candidate["retrieval_overlap"] = False
            merged[identifier] = lexical_candidate

    ranked = []
    for index, candidate in enumerate(merged.values()):
        semantic_score = candidate.get("semantic_score") or 0.0
        lexical_value = candidate.get("lexical_score") or 0.0
        overlap_bonus = 0.05 if candidate.get("retrieval_overlap") else 0.0
        candidate["_hybrid_score"] = 0.50 * semantic_score + 0.45 * lexical_value + overlap_bonus
        ranked.append((candidate["_hybrid_score"], index, candidate))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [{key: value for key, value in candidate.items() if key != "_hybrid_score"} for _, _, candidate in ranked[:limit]]


def rank_retrieved_chunks(
    query: str,
    results: Dict[str, Any],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Apply a capped lexical/domain adjustment to semantic Chroma results."""
    identifiers = _result_list(results, "ids")
    documents = _result_list(results, "documents")
    metadatas = _result_list(results, "metadatas")
    distances = _result_list(results, "distances")
    ranked: List[Tuple[float, int, Dict[str, Any]]] = []
    seen: Set[str] = set()

    for index, raw_identifier in enumerate(identifiers):
        candidate = _candidate_from_result(results, index)
        if candidate is None or candidate["id"] in seen:
            continue
        seen.add(candidate["id"])
        semantic_relevance = candidate["relevance_score"]
        final_score = semantic_relevance + _lexical_boost(query, candidate["text"])
        ranked.append((final_score, index, candidate))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [candidate for _, _, candidate in ranked[:limit]]
