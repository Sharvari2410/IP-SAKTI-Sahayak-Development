import unittest
from pathlib import Path

from backend.invention_comparison import (
    assess_overall,
    build_retrieval_queries,
    compare_candidate,
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


class RawTextComparisonTest(unittest.TestCase):
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
