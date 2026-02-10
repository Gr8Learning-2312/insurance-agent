"""ChromaDB vector store with OpenAI embeddings"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import PyPDF2
from pathlib import Path
import os

from app.utils.config import config
from app.utils.logger import logger

class PolicyVectorStore:
    """Manages ChromaDB collection for insurance policy documents"""
    
    def __init__(self):
        logger.info("Initializing ChromaDB vector store")
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=config.chroma_persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # ✅ Use OpenAI embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=config.openai_api_key,
            model_name=config.embedding_model  # "text-embedding-3-small"
        )
        logger.info(f"Using OpenAI embedding model: {config.embedding_model}")
        
        # Get or create collection with embedding function
        self.collection = self.client.get_or_create_collection(
            name=config.chroma_collection_name,
            embedding_function=self.embedding_function,  # ✅ ChromaDB handles embeddings automatically
            metadata={"description": "Insurance policy documents"}
        )
        
        logger.info(f"ChromaDB collection '{config.chroma_collection_name}' ready")
        logger.info(f"Current document count: {self.collection.count()}")
    
    def load_pdf_policy(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text chunks from policy PDF"""
        logger.info(f"Loading policy PDF: {pdf_path}")
        
        if not Path(pdf_path).exists():
            logger.error(f"Policy PDF not found: {pdf_path}")
            return []
        
        chunks = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                logger.info(f"PDF has {len(pdf_reader.pages)} pages")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    # Split into smaller chunks (500 chars with 50 char overlap)
                    chunk_size = 500
                    overlap = 50
                    
                    for i in range(0, len(text), chunk_size - overlap):
                        chunk = text[i:i + chunk_size]
                        if len(chunk.strip()) > 50:
                            chunks.append({
                                "text": chunk.strip(),
                                "page": page_num,
                                "source": pdf_path
                            })
            
            logger.info(f"Extracted {len(chunks)} chunks from PDF")
            return chunks
        
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            return []
    
    def populate_from_pdf(self, pdf_path: Optional[str] = None):
        """Load policy PDF into vector store"""
        pdf_path = pdf_path or config.policy_pdf_path
        
        # Check if already populated
        if self.collection.count() > 0:
            logger.info("Collection already populated. Skipping.")
            return
        
        chunks = self.load_pdf_policy(pdf_path)
        if not chunks:
            logger.warning("No chunks extracted from PDF")
            return
        
        logger.info("Adding chunks to vector store (embeddings generated automatically)")
        
        # ✅ ChromaDB automatically generates embeddings when we add documents
        self.collection.add(
            documents=[chunk["text"] for chunk in chunks],  # No manual embeddings needed!
            metadatas=[{"page": c["page"], "source": c["source"]} for c in chunks],
            ids=[f"chunk_{i}" for i in range(len(chunks))]
        )
        
        logger.info(f"Successfully added {len(chunks)} chunks to vector store")
    
    def retrieve(self, query: str, top_k: int = 5) -> str:
        """Retrieve relevant policy text for a query"""
        logger.info(f"Retrieving policy text for query: {query[:100]}...")
        
        # ✅ ChromaDB automatically embeds the query using the same model
        results = self.collection.query(
            query_texts=[query],  # Just pass the text - no manual embedding!
            n_results=top_k
        )
        
        if not results['documents'] or not results['documents'][0]:
            logger.warning("No relevant policy documents found")
            return ""
        
        retrieved_text = "\n\n".join(results['documents'][0])
        logger.info(f"Retrieved {len(results['documents'][0])} relevant chunks")
        
        return retrieved_text

# Global vector store instance
policy_store = PolicyVectorStore()
