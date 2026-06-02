"""
Document ingestion and processing module for MineCatalog RAG system.
Handles multi-format document loading, chunking, and embedding generation.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import re
import math

import numpy as np
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document loading, cleaning, and chunking."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents = []
    
    def load_documents(self, docs_dir: str) -> List[Dict[str, str]]:
        """Load documents from multiple formats."""
        docs_path = Path(docs_dir)
        
        if not docs_path.exists():
            logger.warning(f"Documentation directory not found: {docs_dir}")
            return []
        
        all_docs = []
        
        for file_path in docs_path.glob("**/*"):
            if file_path.is_file():
                try:
                    if file_path.suffix.lower() == ".pdf":
                        docs = self._load_pdf(file_path)
                    elif file_path.suffix.lower() == ".txt":
                        docs = self._load_txt(file_path)
                    elif file_path.suffix.lower() == ".md":
                        docs = self._load_md(file_path)
                    elif file_path.suffix.lower() == ".json":
                        docs = self._load_json(file_path)
                    else:
                        logger.debug(f"Skipping unsupported format: {file_path}")
                        continue
                    
                    all_docs.extend(docs)
                    logger.info(f"Loaded {len(docs)} chunks from {file_path.name}")
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {str(e)}")
        
        self.documents = all_docs
        return all_docs
    
    def _load_pdf(self, file_path: Path) -> List[Dict[str, str]]:
        """Extract text from PDF."""
        docs = []
        try:
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    cleaned_text = self._clean_text(text)
                    chunks = self._chunk_text(cleaned_text)
                    for chunk in chunks:
                        docs.append({
                            "content": chunk,
                            "source": f"{file_path.name} (page {page_num + 1})",
                            "type": "pdf"
                        })
        except Exception as e:
            logger.error(f"Error extracting PDF: {str(e)}")
        
        return docs
    
    def _load_txt(self, file_path: Path) -> List[Dict[str, str]]:
        """Load text from TXT file."""
        docs = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            cleaned_text = self._clean_text(text)
            chunks = self._chunk_text(cleaned_text)
            
            for chunk in chunks:
                docs.append({
                    "content": chunk,
                    "source": file_path.name,
                    "type": "txt"
                })
        except Exception as e:
            logger.error(f"Error loading TXT: {str(e)}")
        
        return docs
    
    def _load_md(self, file_path: Path) -> List[Dict[str, str]]:
        """Load text from Markdown file."""
        docs = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            cleaned_text = self._clean_text(text)
            chunks = self._chunk_text(cleaned_text)
            
            for chunk in chunks:
                docs.append({
                    "content": chunk,
                    "source": file_path.name,
                    "type": "md"
                })
        except Exception as e:
            logger.error(f"Error loading MD: {str(e)}")
        
        return docs
    
    def _load_json(self, file_path: Path) -> List[Dict[str, str]]:
        """Load structured content from JSON file."""
        docs = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Handle array of objects
            if isinstance(data, list):
                items = data
            # Handle nested structure with 'contenido' key
            elif isinstance(data, dict) and "contenido" in data:
                items = data["contenido"]
            else:
                # Convert entire JSON to string
                text = json.dumps(data, ensure_ascii=False, indent=2)
                cleaned_text = self._clean_text(text)
                chunks = self._chunk_text(cleaned_text)
                for chunk in chunks:
                    docs.append({
                        "content": chunk,
                        "source": file_path.name,
                        "type": "json"
                    })
                return docs
            
            # Process each content item
            for item in items:
                text = self._json_to_text(item)
                cleaned_text = self._clean_text(text)
                chunks = self._chunk_text(cleaned_text)
                
                for chunk in chunks:
                    docs.append({
                        "content": chunk,
                        "source": file_path.name,
                        "type": "json"
                    })
        except Exception as e:
            logger.error(f"Error loading JSON: {str(e)}")
        
        return docs
    
    def _json_to_text(self, obj: any) -> str:
        """Convert JSON object to readable text."""
        if isinstance(obj, dict):
            lines = []
            for key, value in obj.items():
                if key not in ["id"]:
                    if isinstance(value, list):
                        lines.append(f"{key}:")
                        for item in value:
                            lines.append(f"  - {item}")
                    else:
                        lines.append(f"{key}: {value}")
            return "\n".join(lines)
        return str(obj)
    
    def _clean_text(self, text: str) -> str:
        """Normalize and clean text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
        # Remove URLs if any
        text = re.sub(r'http\S+|www\S+', '', text)
        return text.strip()
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        words = text.split()
        
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1
            
            if current_size + word_size > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Keep overlap
                overlap_words = int(len(current_chunk) * self.chunk_overlap / self.chunk_size)
                current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                current_size = sum(len(w) + 1 for w in current_chunk)
            
            current_chunk.append(word)
            current_size += word_size
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks


class EmbeddingManager:
    """Manages embeddings and similarity search using cosine similarity."""
    
    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai
        self.embeddings = {}
        self.documents = []
        self.vocab_index = {}
        
        if use_openai:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            except ImportError:
                logger.warning("OpenAI not available, using fallback embedding method")
                self.use_openai = False
    
    def generate_embeddings(self, documents: List[Dict[str, str]]) -> Dict[int, np.ndarray]:
        """Generate embeddings for documents."""
        self.documents = documents
        embeddings = {}
        
        if self.use_openai:
            embeddings = self._generate_openai_embeddings(documents)
        else:
            embeddings = self._generate_fallback_embeddings(documents)
        
        self.embeddings = embeddings
        return embeddings
    
    def _generate_openai_embeddings(self, documents: List[Dict[str, str]]) -> Dict[int, np.ndarray]:
        """Generate embeddings using OpenAI API."""
        embeddings = {}
        batch_size = 100
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [doc["content"] for doc in batch]
            
            try:
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.model
                )
                
                for j, embedding_obj in enumerate(response.data):
                    embeddings[i + j] = np.array(embedding_obj.embedding)
            except Exception as e:
                logger.error(f"Error generating embeddings: {str(e)}")
                # Fallback to simple embeddings
                for j, doc in enumerate(batch):
                    embeddings[i + j] = self._simple_embedding(doc["content"])
        
        return embeddings
    
    def _generate_fallback_embeddings(self, documents: List[Dict[str, str]]) -> Dict[int, np.ndarray]:
        """Generate simple embeddings (TF-IDF-like) for documents."""
        embeddings = {}
        
        # Build vocabulary
        vocabulary = set()
        for doc in documents:
            words = doc["content"].lower().split()
            vocabulary.update(words)
        
        vocab_list = sorted(list(vocabulary))
        self.vocab_index = {word: idx for idx, word in enumerate(vocab_list)}
        
        # Generate TF vectors
        for idx, doc in enumerate(documents):
            vector = np.zeros(len(vocab_list))
            words = doc["content"].lower().split()
            
            for word in words:
                if word in self.vocab_index:
                    vector[self.vocab_index[word]] += 1
            
            # Normalize
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            embeddings[idx] = vector
        
        return embeddings

    def _fallback_query_embedding(self, query: str) -> np.ndarray:
        """Generate a query vector in the same TF space as fallback document embeddings."""
        if not self.vocab_index:
            return self._simple_embedding(query)

        vector = np.zeros(len(self.vocab_index))
        for word in query.lower().split():
            if word in self.vocab_index:
                vector[self.vocab_index[word]] += 1

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """Create a simple embedding for text."""
        words = text.lower().split()
        # Create a simple hash-based embedding
        vector = np.zeros(128)
        for word in words:
            hash_val = hash(word) % 128
            vector[hash_val] += 1
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def search(self, query: str, k: int = 3, threshold: float = 0.5) -> List[Tuple[int, str, float]]:
        """Search for relevant documents using semantic similarity."""
        if not self.embeddings:
            return []
        
        # Generate embedding for query
        if self.use_openai:
            try:
                query_response = self.client.embeddings.create(
                    input=[query],
                    model=self.model
                )
                query_embedding = np.array(query_response.data[0].embedding)
            except Exception as e:
                logger.error(f"Error generating query embedding: {str(e)}")
                query_embedding = self._simple_embedding(query)
        else:
            query_embedding = self._fallback_query_embedding(query)
        
        # Calculate similarities
        similarities = []
        for idx, doc_embedding in self.embeddings.items():
            similarity = self.cosine_similarity(query_embedding, doc_embedding)
            if similarity >= threshold:
                similarities.append((idx, similarity))
        
        # Sort by similarity (descending) and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = []
        
        for idx, similarity in similarities[:k]:
            doc = self.documents[idx]
            results.append((idx, doc["content"], similarity))
        
        return results


class RAGPipeline:
    """Main RAG pipeline coordinating document processing and retrieval."""
    
    def __init__(self, docs_dir: str, chunk_size: int = 500, chunk_overlap: int = 50):
        self.processor = DocumentProcessor(chunk_size, chunk_overlap)
        self.embedding_manager = EmbeddingManager(use_openai=False)
        self.docs_dir = docs_dir
        self.is_initialized = False
    
    def initialize(self):
        """Load and process all documents."""
        logger.info("Initializing RAG pipeline...")
        
        documents = self.processor.load_documents(self.docs_dir)
        if not documents:
            logger.error("No documents loaded")
            return False
        
        logger.info(f"Loaded {len(documents)} document chunks")
        self.embedding_manager.generate_embeddings(documents)
        self.is_initialized = True
        logger.info("RAG pipeline initialized successfully")
        
        return True
    
    def search(self, query: str, k: int = 3, threshold: float = 0.5) -> List[Dict[str, any]]:
        """Search for relevant context given a user query."""
        if not self.is_initialized:
            return {"error": "RAG pipeline not initialized"}
        
        results = self.embedding_manager.search(query, k=k, threshold=threshold)
        
        return [
            {
                "content": content,
                "similarity_score": float(score),
                "rank": i + 1
            }
            for i, (_, content, score) in enumerate(results)
        ]
