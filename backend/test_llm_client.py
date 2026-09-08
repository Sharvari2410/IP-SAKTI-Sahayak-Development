import unittest
from llm_client import GroqClient


class TestGroqClientEvidenceCheck(unittest.TestCase):
    def setUp(self):
        self.client = GroqClient(api_key="test_key")

    def test_not_available_phrase_returns_false(self):
        """Test that the exact phrase from prompt instructions is detected as insufficient evidence."""
        answer = "This information is not available in the provided context."
        result = self.client._check_sufficient_evidence(answer)
        self.assertFalse(result)

    def test_other_insufficient_phrases_return_false(self):
        """Test that other insufficient phrases are still detected."""
        insufficient_answers = [
            "There is insufficient information in the context.",
            "This is not mentioned in the context.",
            "The context does not contain this information.",
            "This cannot be determined from the provided context.",
        ]
        for answer in insufficient_answers:
            with self.subTest(answer=answer):
                result = self.client._check_sufficient_evidence(answer)
                self.assertFalse(result)

    def test_normal_grounded_answer_returns_true(self):
        """Test that a normal grounded answer with actual content returns True."""
        answer = "According to [Source 1, Page 5], Section 3(p) of the Patents Act excludes traditional knowledge from patentability."
        result = self.client._check_sufficient_evidence(answer)
        self.assertTrue(result)

    def test_answer_with_citations_returns_true(self):
        """Test that an answer with proper citations is considered sufficient."""
        answer = "The Biological Diversity Act requires prior approval for accessing biological resources. According to [Source 2, Page 12], this is mandatory for Ayurvedic products using indigenous resources."
        result = self.client._check_sufficient_evidence(answer)
        self.assertTrue(result)

    def test_case_insensitive_matching(self):
        """Test that phrase matching is case-insensitive."""
        answer = "THIS INFORMATION IS NOT AVAILABLE IN THE PROVIDED CONTEXT."
        result = self.client._check_sufficient_evidence(answer)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
