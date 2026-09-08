from groq import Groq
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqClient:
    """Client for Groq API to generate answers."""
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-20b"  # Supported production model on Groq
        logger.info("Groq client initialized")
    
    def generate_answer(self, query: str, context_chunks: List[Dict[str, any]]) -> Dict[str, any]:
        """
        Generate a grounded answer using retrieved context.
        
        Args:
            query: User's question
            context_chunks: Retrieved chunks with metadata
            
        Returns:
            Dictionary with answer and metadata
        """
        # Build context from retrieved chunks
        context = self._build_context(context_chunks)
        
        # Create prompt
        prompt = self._create_prompt(query, context)
        
        try:
            logger.info(f"Generating answer for query: {query[:50]}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a STRICTLY FACTUAL AI assistant for Intellectual Property law in Ayurveda and Traditional Knowledge. CRITICAL RULES: 1) Use ONLY information from the provided context - NO outside knowledge 2) NEVER invent, guess, or hallucinate any laws, sections, case names, dates, or citations 3) If information is missing, explicitly say it's not in the context 4) Every factual claim MUST be traceable to a specific source from the context 5) Do not use phrases like 'typically', 'generally', or 'usually' unless explicitly stated in context 6) If you're uncertain, state uncertainty rather than guessing. Accuracy is more important than completeness."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1024
            )
            
            answer = response.choices[0].message.content
            logger.info("Answer generated successfully")
            
            return {
                'answer': answer,
                'context_used': context_chunks,
                'has_sufficient_evidence': self._check_sufficient_evidence(answer)
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                'answer': "I apologize, but I encountered an error generating the answer. Please try again.",
                'context_used': context_chunks,
                'has_sufficient_evidence': False
            }
    
    def _build_context(self, chunks: List[Dict[str, any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get('metadata', {})
            doc_name = metadata.get('document_name', 'Unknown')
            page_num = metadata.get('page_num', '?')
            text = chunk.get('text', '')
            context_parts.append(f"[Source {i}: {doc_name}, Page {page_num}]\n{text}")
        return '\n\n'.join(context_parts)
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create the prompt for the LLM."""
        return f"""CONTEXT:
{context}

QUESTION: {query}

STRICT INSTRUCTIONS:
1. Answer using ONLY the provided context - NO external knowledge
2. Every factual statement MUST be supported by the context above
3. Cite specific source and page for each claim (e.g., "According to [Source X, Page Y]...")
4. If information is missing, explicitly state: "This information is not available in the provided context"
5. NEVER invent, guess, or assume any laws, sections, dates, or citations
6. Avoid speculative language (typically, usually, generally) unless in context
7. If uncertain about any detail, state uncertainty rather than guessing
8. Accuracy is priority - it's better to say "not mentioned" than to guess

ANSWER:"""
    
    def _check_sufficient_evidence(self, answer: str) -> bool:
        """Check if the answer indicates sufficient evidence was found."""
        insufficient_phrases = [
            "insufficient information",
            "not mentioned in the context",
            "context does not contain",
            "cannot be determined from the provided context"
        ]
        answer_lower = answer.lower()
        return not any(phrase in answer_lower for phrase in insufficient_phrases)
