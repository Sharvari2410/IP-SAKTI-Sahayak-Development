from typing import Any, Dict, List, Literal, Optional, Sequence, Set
import re

from pydantic import BaseModel


COMPARISON_FEATURES = (
    "product_type",
    "ingredients",
    "proportions",
    "intended_use",
    "target_application",
    "preparation_method",
    "claimed_effect",
)

FeatureAssessment = Literal["overlap", "difference", "not_disclosed", "uncertain"]
OverallAssessment = Literal[
    "distinguishable",
    "partial_overlap",
    "strong_overlap",
    "insufficient_evidence",
]


class EvidenceReference(BaseModel):
    document_name: str
    page_num: str
    chunk_id: str
    text: str
    extracted_evidence: str


class FeatureComparison(BaseModel):
    feature_name: str
    applicant_value: Any
    evidence_value: Any
    assessment: FeatureAssessment
    evidence_references: List[EvidenceReference]


class EvidenceItem(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any]
    distance: float
    relevance_score: float


class InventionComparisonResponse(BaseModel):
    product_profile: Dict[str, Any]
    evidence_items: List[EvidenceItem]
    feature_comparisons: List[FeatureComparison]
    overall_assessment: OverallAssessment
    explanation: str


def build_retrieval_queries(profile: Any) -> List[str]:
    """Build focused retrieval queries for the comparison dimensions."""
    ingredients = ", ".join(profile.ingredients)
    return [
        f"{profile.product_type} ingredients {ingredients}",
        f"ingredients {ingredients} intended use {profile.intended_use}",
        f"ingredients {ingredients} target application {profile.target_application}",
        f"ingredients {ingredients} preparation method {profile.preparation_method}",
        f"ingredients {ingredients} claimed effect {profile.claimed_effect}",
        f"{profile.product_type} intended use {profile.intended_use} claimed effect {profile.claimed_effect}",
    ]


def _result_list(results: Dict[str, Any], key: str) -> List[Any]:
    value = results.get(key)
    if not isinstance(value, list) or not value or not isinstance(value[0], list):
        return []
    return value[0]


def _result_to_candidate(results: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
    ids = _result_list(results, "ids")
    documents = _result_list(results, "documents")
    if index >= len(ids) or index >= len(documents) or ids[index] in (None, ""):
        return None

    metadatas = _result_list(results, "metadatas")
    distances = _result_list(results, "distances")
    metadata = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
    distance = distances[index] if index < len(distances) and isinstance(distances[index], (int, float)) else 0.0
    return {
        "id": str(ids[index]),
        "text": str(documents[index]),
        "metadata": metadata,
        "distance": distance,
        "relevance_score": 1 - distance,
    }


def retrieve_comparison_candidates(
    profile: Any,
    embedding_generator: Any,
    vector_store: Any,
    per_query: int = 3,
    max_candidates: int = 12,
) -> List[Dict[str, Any]]:
    """Retrieve and deduplicate candidates using focused query representations."""
    candidates: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for query in build_retrieval_queries(profile):
        query_embedding = embedding_generator.generate_query_embedding(query)
        results = vector_store.query(query_embedding, n_results=per_query)
        if not isinstance(results, dict):
            continue
        result_ids = _result_list(results, "ids")
        for index in range(min(len(result_ids), per_query)):
            candidate = _result_to_candidate(results, index)
            if candidate is None:
                continue
            if not extract_feature_evidence(candidate):
                continue
            if candidate["id"] in seen_ids:
                continue
            seen_ids.add(candidate["id"])
            candidates.append(candidate)
            if len(candidates) >= max_candidates:
                return candidates

    return candidates


def _profile_value(profile: Any, feature: str) -> Any:
    if isinstance(profile, dict):
        return profile.get(feature)
    return getattr(profile, feature)


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _normalize_ingredients(value: Any) -> Set[str]:
    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = re.split(r"[,;\n|]", str(value))
    return {_normalize_text(item) for item in values if _normalize_text(item)}


def _clean_evidence(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t\r\n.;")


def _labeled_value(text: str, labels: str) -> str:
    matches = re.findall(
        rf"(?:^|\n)\s*(?:{labels})\s*:?\s*(.+?)(?=\n\s*[A-Za-z][A-Za-z /_-]*\s*:?\s|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    values = [_clean_evidence(value) for value in matches if _clean_evidence(value)]
    if not values:
        return ""
    unique_values = list(dict.fromkeys(values))
    if len(unique_values) > 1:
        return "[ambiguous] " + " | ".join(unique_values)
    return unique_values[0]


def _sentence_with_terms(text: str, terms: Sequence[str]) -> str:
    sentences = [
        _clean_evidence(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+|\n", text)
        if any(re.search(term, sentence, re.IGNORECASE) for term in terms)
    ]
    unique_sentences = list(dict.fromkeys(sentences))
    if len(unique_sentences) > 1:
        return "[ambiguous] " + " | ".join(unique_sentences)
    return unique_sentences[0] if unique_sentences else ""


def _has_formulation_context(text: str) -> bool:
    return bool(re.search(
        r"\b(?:composition|formulation|ingredients?|comprising|consisting of|prepared from|prepared by)\b",
        text,
        re.IGNORECASE,
    ))


def _is_guideline_example(text: str) -> bool:
    """Detect if text is a generic guideline example, not actual formulation evidence."""
    guideline_patterns = (
        r"\bclaims of alleged invention relate to\b",
        r"\bexample involving\b",
        r"\billustrative example\b",
        r"\bexemplary embodiment\b",
        r"\bfor instance\b",
    )
    return bool(re.search("|".join(guideline_patterns), text, re.IGNORECASE))


def _is_regulatory_fragment(text: str) -> bool:
    regulatory_terms = (
        r"\bflavouring agent\b",
        r"\bflavoring agent\b",
        r"\bantioxidant\b",
        r"\bmaximum permitted\b",
        r"\bpermitted limit\b",
        r"\bmicrobiological\b",
        r"\bfood additive\b",
        r"\bpreservative\b",
    )
    return bool(re.search("|".join(regulatory_terms), text, re.IGNORECASE)) and not _has_formulation_context(text)


def _extract_formulation_prose(text: str) -> Dict[str, str]:
    extracted: Dict[str, str] = {}
    composition_match = re.search(
        r"(?:an?\s+)?(?:ayurvedic\s+)?(?P<product>[a-z][a-z -]+?)\s+composition\s+(?:comprising|consisting of)\s+(?P<ingredients>.+?)(?=,?\s+prepared by\b|,?\s+used for\b|,?\s+applied to\b|\.|$)",
        text,
        re.IGNORECASE,
    )
    if composition_match:
        extracted["product_type"] = _clean_evidence(composition_match.group("product"))
        extracted["ingredients"] = _clean_evidence(composition_match.group("ingredients"))
        proportion_values = re.findall(
            r"\b\d+(?:\.\d+)?\s*(?:%|g|kg|ml|l)\b|(?:\b\d+\s*:\s*)+\d+",
            composition_match.group("ingredients"),
            re.IGNORECASE,
        )
        if proportion_values:
            extracted["proportions"] = ", ".join(proportion_values)

    preparation_match = re.search(r"\bprepared by\s+(.+?)(?=\.|\s+and\s+used\b|$)", text, re.IGNORECASE)
    if preparation_match:
        extracted["preparation_method"] = _clean_evidence(preparation_match.group(1))

    use_match = re.search(r"\bused for\s+(.+?)(?=\.|\s+and\s+applied\b|$)", text, re.IGNORECASE)
    if use_match:
        extracted["intended_use"] = _clean_evidence(use_match.group(1))

    application_match = re.search(r"\b(?:applied to|application to)\s+(.+?)(?=\.|$)", text, re.IGNORECASE)
    if application_match:
        extracted["target_application"] = _clean_evidence(application_match.group(1))

    return extracted


def extract_feature_evidence(candidate: Dict[str, Any]) -> Dict[str, str]:
    """Extract only explicitly supported feature evidence from raw chunk text."""
    text = str(candidate.get("text", ""))
    if not text.strip() or _is_regulatory_fragment(text) or _is_guideline_example(text):
        return {}

    formulation_prose = _extract_formulation_prose(text)
    extracted = {
        "product_type": _labeled_value(text, r"product type|product|formulation type"),
        "ingredients": _labeled_value(
            text,
            r"ingredients?|contains|containing|composition|formulation comprises|prepared from",
        ),
        "proportions": _labeled_value(text, r"proportions?|ratios?|parts|quantity|quantities"),
        "intended_use": _labeled_value(
            text,
            r"intended use|used for|traditionally used for|intended for|indicated for|use in|utilized for",
        ),
        "target_application": _labeled_value(text, r"target application|application|applied to|topical application to|target"),
        "preparation_method": _labeled_value(text, r"preparation method|prepared by|preparation|process|method"),
        "claimed_effect": _labeled_value(text, r"claimed effect|effect|efficacy|provides|helps|promotes|reduces|relieves"),
    }
    for feature, value in formulation_prose.items():
        if not extracted.get(feature):
            extracted[feature] = value

    if not extracted["product_type"] and _has_formulation_context(text):
        extracted["product_type"] = _sentence_with_terms(
            text,
            [r"\boil\b", r"\bformulation\b", r"\bpaste\b", r"\bpowder\b", r"\btablet\b", r"\bdecoction\b", r"\bcream\b"],
        )
    if not extracted["proportions"] and _has_formulation_context(text):
        ratio_match = re.search(r"(?:\b\d+\s*:\s*)+\d+|\b\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*(?:g|kg|ml|l)\b", text, re.IGNORECASE)
        if ratio_match:
            extracted["proportions"] = _clean_evidence(ratio_match.group(0))
    if not extracted["target_application"] and _has_formulation_context(text):
        extracted["target_application"] = _sentence_with_terms(
            text,
            [r"\bscalp\b", r"\bhair\b", r"\bskin\b", r"\bmuscle\w*\b", r"\bjoints?\b", r"\bwound\w*\b", r"\bbody\b", r"\bface\b"],
        )
    if not extracted["preparation_method"] and _has_formulation_context(text):
        extracted["preparation_method"] = _sentence_with_terms(
            text,
            [r"\bdecoction\b", r"\bextract\w*\b", r"\bheating\b", r"\bboil\w*\b", r"\bferment\w*\b", r"\bgrind\w*\b"],
        )
    if not extracted["claimed_effect"] and _has_formulation_context(text):
        extracted["claimed_effect"] = _sentence_with_terms(
            text,
            [r"\banti-inflammatory\b", r"\banalgesic\b", r"\breliev\w*\b", r"\breduc\w*\b", r"\bpromot\w*\b", r"\bhelp\w*\b"],
        )

    return {feature: value for feature, value in extracted.items() if value}


def _compare_feature(feature: str, applicant_value: Any, evidence_value: Any) -> str:
    if evidence_value in (None, "", []):
        return "not_disclosed"
    if isinstance(evidence_value, str) and evidence_value.startswith("[ambiguous]"):
        return "uncertain"

    if feature == "ingredients":
        applicant_items = _normalize_ingredients(applicant_value)
        evidence_items = _normalize_ingredients(evidence_value)
        if not applicant_items or not evidence_items:
            return "uncertain"
        return "overlap" if applicant_items & evidence_items else "difference"

    applicant_text = _normalize_text(applicant_value)
    evidence_text = _normalize_text(evidence_value)
    if not applicant_text or not evidence_text:
        return "uncertain"
    if applicant_text == evidence_text:
        return "overlap"

    stop_words = {"a", "an", "and", "for", "in", "of", "the", "to", "use", "used", "with"}
    applicant_tokens = {token for token in re.findall(r"[a-z0-9-]+", applicant_text) if token not in stop_words}
    evidence_tokens = {token for token in re.findall(r"[a-z0-9-]+", evidence_text) if token not in stop_words}
    shared_tokens = applicant_tokens & evidence_tokens
    if shared_tokens and (applicant_tokens <= evidence_tokens or evidence_tokens <= applicant_tokens):
        return "overlap"
    return "difference"


def compare_candidate(profile: Any, candidate: Dict[str, Any]) -> List[FeatureComparison]:
    evidence_profile = extract_feature_evidence(candidate)
    metadata = candidate.get("metadata") or {}
    comparisons = []
    for feature in COMPARISON_FEATURES:
        extracted_evidence = str(evidence_profile.get(feature, ""))
        reference = EvidenceReference(
            document_name=str(metadata.get("document_name", "Unknown")),
            page_num=str(metadata.get("page_num", "?")),
            chunk_id=str(metadata.get("chunk_id", candidate.get("id", "Unknown"))),
            text=str(candidate.get("text", "")),
            extracted_evidence=extracted_evidence,
        )
        comparisons.append(
            FeatureComparison(
                feature_name=feature,
                applicant_value=_profile_value(profile, feature),
                evidence_value=evidence_profile.get(feature),
                assessment=_compare_feature(feature, _profile_value(profile, feature), evidence_profile.get(feature)),
                evidence_references=[reference],
            )
        )
    return comparisons


def assess_overall(comparisons: Sequence[FeatureComparison]) -> str:
    assessments = [comparison.assessment for comparison in comparisons]
    overlaps = assessments.count("overlap")
    differences = assessments.count("difference")
    disclosed = overlaps + differences

    if disclosed < 2:
        return "insufficient_evidence"
    candidate_assessments: Dict[str, List[str]] = {}
    for comparison in comparisons:
        candidate_id = comparison.evidence_references[0].chunk_id if comparison.evidence_references else "unknown"
        candidate_assessments.setdefault(candidate_id, []).append(comparison.assessment)

    has_strong_candidate = any(
        candidate_results.count("overlap") >= 5
        and len({
            comparisons[index].feature_name
            for index, item in enumerate(comparisons)
            if item.assessment == "overlap"
            and item.evidence_references
            and item.evidence_references[0].chunk_id == candidate_id
        }) >= 5
        and "difference" not in candidate_results
        for candidate_id, candidate_results in candidate_assessments.items()
    )
    if has_strong_candidate:
        return "strong_overlap"
    if overlaps and differences:
        return "partial_overlap"
    if differences > overlaps:
        return "distinguishable"
    return "partial_overlap"


def build_explanation(overall_assessment: str, comparisons: Sequence[FeatureComparison]) -> str:
    overlap_features = [item.feature_name for item in comparisons if item.assessment == "overlap"]
    difference_features = [item.feature_name for item in comparisons if item.assessment == "difference"]
    undisclosed_features = [item.feature_name for item in comparisons if item.assessment == "not_disclosed"]

    parts = [f"The structured comparison assessment is {overall_assessment.replace('_', ' ')}."]
    if overlap_features:
        parts.append(f"Explicit overlap is disclosed for: {', '.join(overlap_features)}.")
    if difference_features:
        parts.append(f"Explicit differences are disclosed for: {', '.join(difference_features)}.")
    if undisclosed_features:
        parts.append(f"The evidence does not disclose: {', '.join(undisclosed_features)}.")
    parts.append("Ingredient overlap alone does not establish invention overlap, and this comparison does not determine legal patentability.")
    return " ".join(parts)
