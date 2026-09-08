from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import shutil
from datetime import datetime

from config import settings
from pdf_processor import PDFProcessor
from chunker import Chunker
from embeddings import EmbeddingGenerator
from vector_store import VectorStore
from llm_client import GroqClient
from invention_comparison import (
    EvidenceItem,
    FeatureComparison,
    InventionComparisonResponse,
    assess_overall,
    build_explanation,
    compare_candidate,
    retrieve_comparison_candidates,
)
from retrieval_ranking import hybrid_rank_retrieved_chunks, lexical_retrieve

app = FastAPI(title="IP-SAKTI Sahayak API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pdf_processor = PDFProcessor()
chunker = Chunker(chunk_size=500, chunk_overlap=50)
embedding_generator = EmbeddingGenerator(settings.embedding_model)
vector_store = VectorStore(settings.chroma_persist_directory)
llm_client = GroqClient(settings.groq_api_key)

# Create uploads directory
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class QueryRequest(BaseModel):
    question: str
    show_rag_process: bool = False
    jurisdiction: str = "india"
    ip_regime: str = "all"


class QueryResponse(BaseModel):
    answer: str
    retrieved_chunks: List[dict]
    has_sufficient_evidence: bool
    confidence_score: float
    rag_process: Optional[dict] = None


class InventionProfile(BaseModel):
    product_type: str = Field(..., min_length=1)
    ingredients: List[str] = Field(..., min_length=1)
    proportions: str = Field(..., min_length=1)
    intended_use: str = Field(..., min_length=1)
    target_application: str = Field(..., min_length=1)
    preparation_method: str = Field(..., min_length=1)
    claimed_effect: str = Field(..., min_length=1)


class ProductAnalysisResponse(BaseModel):
    product_profile: InventionProfile
    status: str


class CompareInventionRequest(BaseModel):
    product_profile: InventionProfile


class DocumentInfo(BaseModel):
    document_name: str
    page_count: int
    chunk_count: int
    indexed_date: str


class SystemStatus(BaseModel):
    vector_index_loaded: bool
    documents_indexed: int
    total_chunks: int


@app.get("/")
async def root():
    return {"message": "IP-SAKTI Sahayak API", "status": "running"}


@app.get("/status")
async def get_status():
    """Get system status including indexed documents."""
    stats = vector_store.get_collection_stats()
    documents = vector_store.get_all_documents()
    return SystemStatus(
        vector_index_loaded=True,
        documents_indexed=len(documents),
        total_chunks=stats['chunk_count']
    )


@app.get("/documents")
async def get_documents():
    """Get list of all indexed documents."""
    documents = vector_store.get_all_documents()
    return {
        "documents": [
            {
                "name": doc,
                "indexed_date": datetime.now().strftime("%d %b %Y")
            }
            for doc in documents
        ]
    }


@app.post("/analyze-product", response_model=ProductAnalysisResponse)
async def analyze_product(profile: InventionProfile):
    """Validate and return a structured product profile for future analysis."""
    return ProductAnalysisResponse(
        product_profile=profile,
        status="profile_created"
    )


@app.post("/compare-invention", response_model=InventionComparisonResponse)
async def compare_invention(request: CompareInventionRequest):
    """Retrieve and compare evidence across the invention's key dimensions."""
    try:
        candidates = retrieve_comparison_candidates(
            request.product_profile,
            embedding_generator,
            vector_store,
        )
        feature_comparisons: List[FeatureComparison] = []
        for candidate in candidates:
            feature_comparisons.extend(compare_candidate(request.product_profile, candidate))

        overall_assessment = assess_overall(feature_comparisons)
        return InventionComparisonResponse(
            product_profile=request.product_profile.model_dump(),
            evidence_items=[EvidenceItem(**candidate) for candidate in candidates],
            feature_comparisons=feature_comparisons,
            overall_assessment=overall_assessment,
            explanation=build_explanation(overall_assessment, feature_comparisons),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing invention: {str(e)}")


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file for indexing."""
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text
        pages = pdf_processor.extract_text(file_path)
        doc_info = pdf_processor.get_document_info(file_path)
        
        # Create chunks
        chunks = chunker.create_chunks(pages, file.filename)
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = embedding_generator.generate_embeddings(texts)
        
        # Store in vector database
        vector_store.add_chunks(chunks, embeddings)
        
        return {
            "message": "Document indexed successfully",
            "document_name": file.filename,
            "page_count": doc_info['page_count'],
            "chunk_count": len(chunks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the RAG system with a question."""
    try:
        # Generate query embedding
        query_embedding = embedding_generator.generate_query_embedding(request.question)
        
        # Retrieve relevant chunks
        results = vector_store.query(query_embedding, n_results=30)

        # Merge semantic retrieval with a lightweight lexical scan of existing Chroma chunks.
        lexical_candidates = lexical_retrieve(request.question, vector_store, limit=30)
        retrieved_chunks = hybrid_rank_retrieved_chunks(
            request.question,
            results,
            lexical_candidates,
            limit=5,
        )
        
        # Generate answer using LLM
        llm_response = llm_client.generate_answer(request.question, retrieved_chunks)
        
        # Calculate confidence score based on retrieval quality
        avg_relevance = sum(chunk['relevance_score'] for chunk in retrieved_chunks) / len(retrieved_chunks) if retrieved_chunks else 0
        confidence_score = avg_relevance if llm_response['has_sufficient_evidence'] else avg_relevance * 0.5
        
        # Build RAG process visualization if requested
        rag_process = None
        if request.show_rag_process:
            rag_process = {
                "question": request.question,
                "retrieval_count": len(retrieved_chunks),
                "top_chunks": [
                    {
                        "text": chunk['text'][:200] + "...",
                        "document": chunk['metadata']['document_name'],
                        "page": chunk['metadata']['page_num'],
                        "relevance": round(chunk['relevance_score'], 3)
                    }
                    for chunk in retrieved_chunks
                ],
                "context_length": sum(len(chunk['text']) for chunk in retrieved_chunks),
                "llm_model": "openai/gpt-oss-20b"
            }
        
        return QueryResponse(
            answer=llm_response['answer'],
            retrieved_chunks=retrieved_chunks,
            has_sufficient_evidence=llm_response['has_sufficient_evidence'],
            confidence_score=round(confidence_score, 3),
            rag_process=rag_process
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
