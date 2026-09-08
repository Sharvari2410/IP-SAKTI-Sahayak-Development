import unittest
from pathlib import Path

from invention_comparison import (
    assess_overall,
    build_retrieval_queries,
    compare_candidate,
    extract_feature_evidence,
    retrieve_comparison_candidates,
)


class Profile:
    product_type = "Ayurvedic oil"
    ingredients = ["A", "B", "C", "D"]
    proportions = "20:10:30:40"
    intended_use = "Body massage"
    target_application = "Muscles"
    preparation_method = "Process X"
    claimed_effect = "Muscle relaxation"


class SyntheticBodyOilProfile:
    product_type = "Ayurvedic Body Oil"
    ingredients = ["Ashwagandha", "sesame oil"]
    proportions = "20:10"
    intended_use = "Body massage"
    target_application = "Muscles"
    preparation_method = "Boiling"
    claimed_effect = "Relaxation"


SYNTHETIC_RECORD_A_TEXT = """SYNTHETIC TEST DATA / NOT REAL PRIOR ART
Synthetic Prior-Art Record A
Product Type: Ayurvedic Hair Oil
Ingredients: Ashwagandha, sesame oil
Proportions: 20:10
Intended Use: Hair care
Target Application: Scalp and hair follicles
Preparation Method: Boiling the herbal ingredients in sesame oil
Claimed Effect: Supports hair growth"""

SYNTHETIC_RECORD_B_TEXT = """SYNTHETIC TEST DATA / NOT REAL PRIOR ART
Synthetic Prior-Art Record B
Product Type: Ayurvedic Body Oil
Ingredients: Ashwagandha, sesame oil
Proportions: 20:10
Intended Use: Body massage
Target Application: Muscles
Preparation Method: Boiling
Claimed Effect: Promotes relaxation"""

SYNTHETIC_RECORD_C_TEXT = """SYNTHETIC TEST DATA / NOT REAL PRIOR ART
Synthetic Prior-Art Record C
Product Type: Herbal powder
Ingredients: Turmeric, neem leaf
Proportions: 5:1
Intended Use: Skin cleansing
Target Application: Facial skin
Preparation Method: Grinding and drying
Claimed Effect: Reduces surface irritation"""


def raw_candidate(text, chunk_id="1"):
    return {
        "id": f"source.pdf-p1-c{chunk_id}",
        "text": text,
        "metadata": {
            "document_name": "source.pdf",
            "page_num": "1",
            "chunk_id": chunk_id,
        },
        "distance": 0.1,
        "relevance_score": 0.9,
    }


def synthetic_candidate(text, document_name, page_num, chunk_id):
    candidate = raw_candidate(text, chunk_id)
    candidate["metadata"] = {
        "document_name": document_name,
        "page_num": page_num,
        "chunk_id": chunk_id,
    }
    candidate["id"] = f"{document_name}-p{page_num}-c{chunk_id}"
    return candidate


class RawTextComparisonTest(unittest.TestCase):
    def test_synthetic_mentor_scenario_preserves_multidimensional_difference(self):
        candidate = synthetic_candidate(SYNTHETIC_RECORD_A_TEXT, "synthetic-record-a.pdf", "1", "a-1")

        comparisons = compare_candidate(SyntheticBodyOilProfile(), candidate)
        by_feature = {comparison.feature_name: comparison for comparison in comparisons}

        self.assertEqual(by_feature["product_type"].assessment, "difference")
        self.assertEqual(by_feature["ingredients"].assessment, "overlap")
        self.assertEqual(by_feature["proportions"].assessment, "overlap")
        self.assertEqual(by_feature["intended_use"].assessment, "difference")
        self.assertEqual(by_feature["target_application"].assessment, "difference")
        self.assertEqual(by_feature["preparation_method"].assessment, "overlap")
        self.assertEqual(by_feature["claimed_effect"].assessment, "difference")
        self.assertIn(assess_overall(comparisons), {"partial_overlap", "distinguishable"})
        self.assertNotEqual(assess_overall(comparisons), "strong_overlap")

    def test_synthetic_matching_record_can_produce_strong_overlap(self):
        candidate = synthetic_candidate(SYNTHETIC_RECORD_B_TEXT, "synthetic-record-b.pdf", "1", "b-1")

        comparisons = compare_candidate(SyntheticBodyOilProfile(), candidate)

        self.assertTrue(all(item.assessment == "overlap" for item in comparisons))
        self.assertEqual(assess_overall(comparisons), "strong_overlap")

    def test_synthetic_different_formulation_is_not_strong_overlap(self):
        candidate = synthetic_candidate(SYNTHETIC_RECORD_C_TEXT, "synthetic-record-c.pdf", "3", "c-1")

        comparisons = compare_candidate(SyntheticBodyOilProfile(), candidate)

        self.assertNotEqual(assess_overall(comparisons), "strong_overlap")
        self.assertEqual(
            sum(item.assessment == "difference" for item in comparisons),
            7,
        )

    def test_synthetic_fixture_metadata_contains_only_chroma_identifiers(self):
        candidate = synthetic_candidate(SYNTHETIC_RECORD_A_TEXT, "synthetic-record-a.pdf", "1", "a-1")

        self.assertEqual(set(candidate["metadata"]), {"document_name", "page_num", "chunk_id"})
        evidence = extract_feature_evidence(candidate)
        self.assertIn("product_type", evidence)
        self.assertIn("ingredients", evidence)

    def test_synthetic_evidence_traceability_preserves_all_source_fields(self):
        candidate = synthetic_candidate(SYNTHETIC_RECORD_A_TEXT, "synthetic-record-a.pdf", "1", "a-1")

        comparisons = compare_candidate(SyntheticBodyOilProfile(), candidate)

        for comparison in comparisons:
            self.assertEqual(len(comparison.evidence_references), 1)
            reference = comparison.evidence_references[0]
            self.assertEqual(reference.document_name, "synthetic-record-a.pdf")
            self.assertEqual(reference.page_num, "1")
            self.assertEqual(reference.chunk_id, "a-1")
            self.assertEqual(reference.text, SYNTHETIC_RECORD_A_TEXT)
            if comparison.feature_name in extract_feature_evidence(candidate):
                self.assertTrue(reference.extracted_evidence)

    def test_regulatory_additive_row_is_not_formulation_evidence(self):
        evidence = extract_feature_evidence(raw_candidate("Rosemary oil 1% Antioxidant"))

        self.assertNotIn("product_type", evidence)
        self.assertNotIn("proportions", evidence)
        comparisons = compare_candidate(Profile(), raw_candidate("Rosemary oil 1% Antioxidant"))
        self.assertTrue(all(item.assessment == "not_disclosed" for item in comparisons))

    def test_actual_formulation_prose_extracts_meaningful_features(self):
        text = (
            "An Ayurvedic hair oil composition comprising sesame oil 70%, coconut oil 20% "
            "and Ashwagandha extract 10%, prepared by heating the ingredients and used for "
            "scalp application."
        )
        evidence = extract_feature_evidence(raw_candidate(text))

        self.assertEqual(evidence["product_type"], "hair oil")
        self.assertIn("sesame oil 70%", evidence["ingredients"].lower())
        self.assertIn("70%", evidence["proportions"])
        self.assertEqual(evidence["preparation_method"], "heating the ingredients")
        self.assertEqual(evidence["intended_use"], "scalp application")

    def test_same_ingredients_different_use_and_effect(self):
        candidate = raw_candidate(
            "Product type: Ayurvedic oil\n"
            "Ingredients: A, B, C, D\n"
            "Proportions: 25:10:25:40\n"
            "Intended use: Hair care\n"
            "Target application: Scalp\n"
            "Preparation method: Process Y\n"
            "Claimed effect: Hair growth"
        )

        comparisons = compare_candidate(Profile(), candidate)
        by_feature = {comparison.feature_name: comparison for comparison in comparisons}

        self.assertEqual(by_feature["ingredients"].assessment, "overlap")
        self.assertEqual(by_feature["proportions"].assessment, "difference")
        self.assertEqual(by_feature["intended_use"].assessment, "difference")
        self.assertEqual(by_feature["target_application"].assessment, "difference")
        self.assertEqual(by_feature["preparation_method"].assessment, "difference")
        self.assertEqual(by_feature["claimed_effect"].assessment, "difference")
        self.assertNotEqual(assess_overall(comparisons), "strong_overlap")

    def test_raw_text_matching_most_dimensions_can_be_strong_overlap(self):
        candidate = raw_candidate(
            "Product type: Ayurvedic oil\n"
            "Ingredients: a, B, c, D\n"
            "Proportions: 20:10:30:40\n"
            "Intended use: used for body massage therapy\n"
            "Target application: muscles\n"
            "Preparation method: Process X\n"
            "Claimed effect: muscle relaxation"
        )

        comparisons = compare_candidate(Profile(), candidate)

        self.assertGreaterEqual(
            sum(item.assessment == "overlap" for item in comparisons),
            5,
        )
        self.assertEqual(assess_overall(comparisons), "strong_overlap")

    def test_only_ingredient_disclosure_leaves_other_features_undisclosed(self):
        candidate = raw_candidate("Ingredients: A, B")

        comparisons = compare_candidate(Profile(), candidate)
        by_feature = {comparison.feature_name: comparison for comparison in comparisons}

        self.assertEqual(by_feature["ingredients"].assessment, "overlap")
        self.assertEqual(by_feature["intended_use"].assessment, "not_disclosed")
        self.assertEqual(by_feature["claimed_effect"].assessment, "not_disclosed")
        self.assertEqual(assess_overall(comparisons), "insufficient_evidence")

    def test_irrelevant_raw_text_is_insufficient(self):
        comparisons = compare_candidate(Profile(), raw_candidate("This document discusses a historical archive."))

        self.assertTrue(all(item.assessment == "not_disclosed" for item in comparisons))
        self.assertEqual(assess_overall(comparisons), "insufficient_evidence")

    def test_conflicting_disclosures_are_uncertain(self):
        comparisons = compare_candidate(
            Profile(),
            raw_candidate("Intended use: Hair care\nIntended use: Body massage"),
        )

        intended_use = next(item for item in comparisons if item.feature_name == "intended_use")
        self.assertEqual(intended_use.assessment, "uncertain")

    def test_ingredient_only_overlaps_across_candidates_are_not_strong(self):
        comparisons = []
        for index in range(5):
            comparisons.extend(compare_candidate(Profile(), raw_candidate("Ingredients: A, B", str(index))))

        self.assertNotEqual(assess_overall(comparisons), "strong_overlap")

    def test_evidence_traceability_preserves_chunk_and_extracted_text(self):
        original_text = "Ingredients: A, B, C, D\nClaimed effect: muscle relaxation"
        comparisons = compare_candidate(Profile(), raw_candidate(original_text, "chunk-7"))
        ingredient_reference = next(item for item in comparisons if item.feature_name == "ingredients").evidence_references[0]

        self.assertEqual(ingredient_reference.document_name, "source.pdf")
        self.assertEqual(ingredient_reference.page_num, "1")
        self.assertEqual(ingredient_reference.chunk_id, "chunk-7")
        self.assertEqual(ingredient_reference.text, original_text)
        self.assertEqual(ingredient_reference.extracted_evidence, "A, B, C, D")

    def test_guideline_example_is_rejected_as_formulation_evidence(self):
        guideline_text = (
            "The claims of alleged invention relate to a composition comprising Karanj "
            "and Heena in a specified ratio, prepared by boiling, used for ulcer/wound treatment. "
            "This is an illustrative example of a patent application involving traditional knowledge."
        )
        evidence = extract_feature_evidence(raw_candidate(guideline_text))
        self.assertEqual(evidence, {})

    def test_legitimate_labeled_formulation_evidence_is_accepted(self):
        formulation_text = (
            "Product type: Ayurvedic oil\n"
            "Ingredients: Ashwagandha, sesame oil\n"
            "Proportions: 20:10\n"
            "Intended use: body massage\n"
            "Target application: muscles\n"
            "Preparation method: boiling\n"
            "Claimed effect: relaxation"
        )
        evidence = extract_feature_evidence(raw_candidate(formulation_text))
        self.assertNotEqual(evidence, {})
        self.assertIn("product_type", evidence)
        self.assertIn("ingredients", evidence)

    def test_legitimate_formulation_with_such_as_is_not_rejected(self):
        formulation_text = (
            "An Ayurvedic oil composition comprising sesame oil and Ashwagandha extract, "
            "prepared by heating ingredients such as herbal extracts, used for body massage."
        )
        evidence = extract_feature_evidence(raw_candidate(formulation_text))
        self.assertNotEqual(evidence, {})


class RetrievalTest(unittest.TestCase):
    def test_duplicate_ids_are_returned_once_and_six_queries_execute(self):
        class Embeddings:
            def __init__(self):
                self.queries = []

            def generate_query_embedding(self, query):
                self.queries.append(query)
                return [query]

        class Store:
            def __init__(self):
                self.calls = []

            def query(self, query_embedding, n_results):
                self.calls.append((query_embedding[0], n_results))
                return {
                    "ids": [["same-id"]],
                    "documents": [["Ingredients: A, B"]],
                    "metadatas": [[{"document_name": "source.pdf", "page_num": "1", "chunk_id": "1"}]],
                    "distances": [[0.1]],
                }

        embeddings = Embeddings()
        store = Store()
        candidates = retrieve_comparison_candidates(Profile(), embeddings, store, per_query=2)

        self.assertEqual(len(embeddings.queries), 6)
        self.assertEqual(len(store.calls), 6)
        self.assertEqual([candidate["id"] for candidate in candidates], ["same-id"])

    def test_malformed_empty_result_rows_are_skipped(self):
        class Embeddings:
            def generate_query_embedding(self, query):
                return [query]

        class Store:
            def query(self, query_embedding, n_results):
                return {
                    "ids": [["missing-document"]],
                    "documents": [[]],
                    "metadatas": [[]],
                    "distances": [[]],
                }

        self.assertEqual(retrieve_comparison_candidates(Profile(), Embeddings(), Store()), [])

    def test_regulatory_rows_are_filtered_from_comparison_candidates(self):
        class Embeddings:
            def generate_query_embedding(self, query):
                return [query]

        class Store:
            def query(self, query_embedding, n_results):
                return {
                    "ids": [["regulatory-row"]],
                    "documents": [["Rosemary oil 1% Antioxidant"]],
                    "metadatas": [[{"document_name": "gazette.pdf", "page_num": "2", "chunk_id": "1"}]],
                    "distances": [[0.1]],
                }

        self.assertEqual(retrieve_comparison_candidates(Profile(), Embeddings(), Store()), [])


class RegressionContractTest(unittest.TestCase):
    def test_existing_endpoints_and_response_models_remain_declared(self):
        main_source = Path(__file__).with_name("main.py").read_text(encoding="utf-8")

        self.assertIn('@app.post("/query", response_model=QueryResponse)', main_source)
        self.assertIn('@app.post("/analyze-product", response_model=ProductAnalysisResponse)', main_source)
        self.assertIn('status="profile_created"', main_source)
        self.assertIn("class QueryResponse(BaseModel):", main_source)
        self.assertIn("class ProductAnalysisResponse(BaseModel):", main_source)

    def test_focused_query_set_contains_six_representations(self):
        self.assertEqual(len(build_retrieval_queries(Profile())), 6)


if __name__ == "__main__":
    unittest.main()
