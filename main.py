"""
FastAPI server for MineCatalog RAG system.
Exposes endpoints for semantic search and LLM-based question answering.
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from rag_pipeline import RAGPipeline

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize RAG pipeline
rag_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    global rag_pipeline
    
    # Startup
    logger.info("Starting MineCatalog RAG API...")
    docs_dir = os.getenv("DOCS_DIR_PATH", "./docs")
    chunk_size = int(os.getenv("CHUNK_SIZE", 500))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 50))
    
    rag_pipeline = RAGPipeline(docs_dir, chunk_size, chunk_overlap)
    
    if not rag_pipeline.initialize():
        logger.error("Failed to initialize RAG pipeline")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MineCatalog RAG API...")


app = FastAPI(
    title="MineCatalog RAG API",
    description="Semantic search and retrieval for MineCatalog documentation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SearchRequest(BaseModel):
    """Request model for document search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: Optional[int] = Field(3, ge=1, le=10, description="Number of results to return")
    threshold: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Similarity threshold")


class SearchResult(BaseModel):
    """Single search result."""
    rank: int
    content: str
    similarity_score: float


class SearchResponse(BaseModel):
    """Response model for document search."""
    success: bool
    results: list[SearchResult]
    total_results: int
    query: str


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool
    error: str
    details: Optional[str] = None


@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint."""
    is_ready = rag_pipeline is not None and rag_pipeline.is_initialized
    
    return {
        "status": "healthy" if is_ready else "initializing",
        "rag_initialized": is_ready
    }


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Semantic search endpoint.
    
    Returns the most relevant document chunks for a given query.
    """
    if rag_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized"
        )
    
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )
    
    try:
        logger.info(f"Searching for: {request.query}")
        
        results = rag_pipeline.search(
            query=request.query.strip(),
            k=request.top_k,
            threshold=request.threshold
        )
        
        if "error" in results:
            raise HTTPException(
                status_code=500,
                detail=results["error"]
            )
        
        formatted_results = [
            SearchResult(
                rank=result["rank"],
                content=result["content"],
                similarity_score=result["similarity_score"]
            )
            for result in results
        ]
        
        return SearchResponse(
            success=True,
            results=formatted_results,
            total_results=len(formatted_results),
            query=request.query
        )
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.post("/context", response_model=dict)
async def get_context(request: SearchRequest) -> dict:
    """
    Get contextual information for LLM prompt injection.
    
    Returns formatted context string suitable for system prompts.
    """
    if rag_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized"
        )
    
    try:
        results = rag_pipeline.search(
            query=request.query.strip(),
            k=request.top_k,
            threshold=request.threshold
        )
        
        if "error" in results:
            return {
                "success": False,
                "error": results["error"],
                "context": ""
            }
        
        # Format context for LLM
        if not results:
            context_text = "No relevant information found in the documentation."
        else:
            context_parts = []
            for result in results:
                context_parts.append(f"- {result['content']}")
            context_text = "\n".join(context_parts)
        
        return {
            "success": True,
            "query": request.query,
            "context": context_text,
            "num_results": len(results),
            "threshold_used": request.threshold
        }
    
    except Exception as e:
        logger.error(f"Context retrieval error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "context": ""
        }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if os.getenv("API_DEBUG") == "true" else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
