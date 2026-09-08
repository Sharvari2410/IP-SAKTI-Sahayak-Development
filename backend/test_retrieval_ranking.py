import unittest

from backend.retrieval_ranking import (
    hybrid_rank_retrieved_chunks,
    lexical_retrieve,
    rank_retrieved_chunks,
)


class RetrievalRankingTest(unittest.TestCase):
    def test_lexical_only_candidate_is_discovered_from_existing_chunks(self):
        class Collection:
            def get(self, include):
                return {
                    "ids": ["legal-only"],
                    "documents": ["Section 3(p) excludes inventions based on traditional knowledge."],
                    "metadatas": [{"document_name": "patents.pdf", "page_num": "10", "chunk_id": "100"}],
                }

        class Store:
            collection = Collection()

        candidates = lexical_retrieve(
            "How does Section 3(p) affect traditional knowledge?",
            Store(),
            limit=5,
        )

        self.assertEqual([candidate["id"] for candidate in candidates], ["legal-only"])

    def test_hybrid_ranking_surfaces_lexical_only_exact_section_evidence(self):
        semantic_results = {
            "ids": [["generic"]],
            "documents": [["A generally relevant legal discussion."]],
            "metadatas": [[{}]],
            "distances": [[0.25]],
        }
        lexical_candidates = [{
            "id": "section",
            "text": "Section 3(p) excludes inventions based on traditional knowledge.",
            "metadata": {"document_name": "patents.pdf", "page_num": "10", "chunk_id": "100"},
            "distance": None,
            "relevance_score": None,
            "lexical_score": 1.0,
        }]

        ranked = hybrid_rank_retrieved_chunks(
            "How does Section 3(p) affect traditional knowledge?",
            semantic_results,
            lexical_candidates,
            limit=2,
        )

        self.assertEqual(ranked[0]["id"], "section")

    def test_semantic_only_candidate_remains_available(self):
        semantic_results = {
            "ids": [["semantic"]],
            "documents": [["A highly relevant discussion of the requested subject."]],
            "metadatas": [[{}]],
            "distances": [[0.05]],
        }

        ranked = hybrid_rank_retrieved_chunks("unrelated lexical wording", semantic_results, [], limit=1)

        self.assertEqual(ranked[0]["id"], "semantic")

    def test_candidate_found_by_both_retrievers_gets_overlap_bonus(self):
        semantic_results = {
            "ids": [["shared", "other"]],
            "documents": [["Patent application requirements and novelty.", "A related document."]],
            "metadatas": [[{}, {}]],
            "distances": [[0.2, 0.19]],
        }
        lexical_candidates = [{
            "id": "shared",
            "text": "Patent application requirements and novelty.",
            "metadata": {},
            "distance": None,
            "relevance_score": None,
            "lexical_score": 0.8,
        }]

        ranked = hybrid_rank_retrieved_chunks(
            "patent application requirements novelty",
            semantic_results,
            lexical_candidates,
            limit=2,
        )

        self.assertEqual(ranked[0]["id"], "shared")

    def test_exact_section_and_phrase_evidence_ranks_above_same_document_unrelated_text(self):
        results = {
            "ids": [["section", "government-use", "other-section"]],
            "documents": [[
                "Section 3(p) excludes inventions based on traditional knowledge.",
                "The invention may be used by or for the purposes of Government.",
                "Section 20 concerns further information supplied by the applicant.",
            ]],
            "metadatas": [[
                {"document_name": "patents.pdf", "page_num": "1", "chunk_id": "1"},
                {"document_name": "patents.pdf", "page_num": "2", "chunk_id": "2"},
                {"document_name": "patents.pdf", "page_num": "3", "chunk_id": "3"},
            ]],
            "distances": [[0.2, 0.1, 0.11]],
        }

        ranked = rank_retrieved_chunks(
            "How does Section 3(p) of the Patents Act affect inventions based on traditional knowledge?",
            results,
            limit=3,
        )

        self.assertEqual(ranked[0]["id"], "section")

    def test_pdf_extracted_parenthetical_section_with_context_ranks(self):
        results = {
            "ids": [["section-fragment", "unrelated"]],
            "documents": [[
                "(p) an invention which, in effect, is traditional knowledge.",
                "The invention may be used by or for the purposes of Government.",
            ]],
            "metadatas": [[{}, {}]],
            "distances": [[0.3, 0.2]],
        }

        ranked = rank_retrieved_chunks(
            "How does Section 3(p) affect traditional knowledge?",
            results,
            limit=2,
        )

        self.assertEqual(ranked[0]["id"], "section-fragment")

    def test_patent_query_prefers_patent_content_over_aahara_only_content(self):
        results = {
            "ids": [["patent", "aahara"]],
            "documents": [[
                "Patent requirements include novelty, inventive step, prior art, and patent application requirements.",
                "Ayurveda Aahara food business operator labelling and regulatory requirements.",
            ]],
            "metadatas": [[{}, {}]],
            "distances": [[0.3, 0.3]],
        }

        ranked = rank_retrieved_chunks(
            "What are the specific requirements for patenting an Ayurvedic formulation in India?",
            results,
            limit=2,
        )

        self.assertEqual(ranked[0]["id"], "patent")

    def test_aahara_query_preserves_aahara_content(self):
        results = {
            "ids": [["aahara", "patent"]],
            "documents": [[
                "Ayurveda Aahara regulatory requirements for food business operators and food labelling.",
                "Patent novelty and inventive step requirements for inventions.",
            ]],
            "metadatas": [[{}, {}]],
            "distances": [[0.3, 0.3]],
        }

        ranked = rank_retrieved_chunks(
            "What regulatory requirements apply to Ayurvedic food products under the Ayurveda Aahara framework?",
            results,
            limit=2,
        )

        self.assertEqual(ranked[0]["id"], "aahara")

    def test_generic_word_overlap_has_only_small_effect(self):
        results = {
            "ids": [["generic", "semantic"]],
            "documents": [[
                "What is and how does the system work in the document.",
                "A discussion of a related technical topic with no repeated query keywords.",
            ]],
            "metadatas": [[{}, {}]],
            "distances": [[0.3, 0.31]],
        }

        ranked = rank_retrieved_chunks("What is the system and how does it work?", results, limit=2)

        self.assertEqual(ranked[0]["id"], "generic")
        self.assertLess(ranked[0]["relevance_score"] - ranked[1]["relevance_score"], 0.02)

    def test_semantic_relevance_remains_primary(self):
        results = {
            "ids": [["semantic", "lexical"]],
            "documents": [[
                "A relevant discussion of the invention and its requirements.",
                "Section 3(p) traditional knowledge patent prior art novelty inventive step patent application.",
            ]],
            "metadatas": [[{}, {}]],
            "distances": [[0.05, 0.25]],
        }

        ranked = rank_retrieved_chunks(
            "How does Section 3(p) affect traditional knowledge patent requirements?",
            results,
            limit=2,
        )

        self.assertEqual(ranked[0]["id"], "semantic")

    def test_duplicate_and_malformed_rows_are_safe(self):
        results = {
            "ids": [["duplicate", "duplicate", None, "valid"]],
            "documents": [["Section 3(p) text", "duplicate text", None, "traditional knowledge text"]],
            "metadatas": [[{}, None, None, {"document_name": "source.pdf"}]],
            "distances": [[0.2, None, 0.1, None]],
        }

        ranked = rank_retrieved_chunks("Section 3(p) traditional knowledge", results, limit=5)

        self.assertEqual({item["id"] for item in ranked}, {"duplicate", "valid"})
        self.assertEqual(len(ranked), 2)
        valid_item = next(item for item in ranked if item["id"] == "valid")
        self.assertEqual(valid_item["metadata"], {"document_name": "source.pdf"})


if __name__ == "__main__":
    unittest.main()
