import os
import hashlib
import time
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import json

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

import config
from utils import clean_text, reciprocal_rank_fusion

class RAGEngine:
    def __init__(self):
        print("Initializing RAGEngine...")
        self.embeddings = None
        self.vector_store = None
        self.client = None
        self.bm25_index = None
        self.bm25_documents = [] 
        print(f"Initializing Text Splitter (Size: {config.CHUNK_SIZE}, Overlap: {config.CHUNK_OVERLAP})")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self._initialize_embeddings()
        self._initialize_qdrant()
        if self.client:
            try:
                info = self.client.get_collection(config.QDRANT_COLLECTION_NAME)
                print(f"Connected to Qdrant collection '{config.QDRANT_COLLECTION_NAME}'. Points: {info.points_count}")
            except Exception as e:
                print(f"Warning: Could not get collection info: {e}")
        self.scan_and_process_pdfs()
        self._build_bm25_index() 
    def _initialize_embeddings(self):
        """Initialize the embedding model."""
        try:
            print(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL_NAME,
                model_kwargs={'device': config.EMBEDDING_DEVICE},
                encode_kwargs={'normalize_embeddings': True}
            )
            print("Embedding model loaded successfully!")
        except Exception as e:
            print(f"CRITICAL ERROR loading embeddings: {e}")
            raise

    def _initialize_qdrant(self):
        """Initialize Qdrant connection with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Connecting to Qdrant at {config.QDRANT_URL} (Attempt {attempt+1}/{max_retries})...")
                self.client = QdrantClient(
                    url=config.QDRANT_URL, 
                    api_key=config.QDRANT_API_KEY if config.QDRANT_API_KEY else None
                )
                try:
                    self.client.get_collection(config.QDRANT_COLLECTION_NAME)
                    print(f"Collection '{config.QDRANT_COLLECTION_NAME}' exists.")
                except Exception:
                    print(f"Collection '{config.QDRANT_COLLECTION_NAME}' not found. Creating...")
                    self.client.create_collection(
                        collection_name=config.QDRANT_COLLECTION_NAME,
                        vectors_config=models.VectorParams(
                            size=384,
                            distance=models.Distance.COSINE
                        )
                    )
                    print("Collection created.")
                self.vector_store = QdrantVectorStore(
                    client=self.client,
                    embedding=self.embeddings,
                    collection_name=config.QDRANT_COLLECTION_NAME
                )
                print("Qdrant Vector Store initialized successfully!")
                return
                
            except Exception as e:
                print(f"Error connecting to Qdrant: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        print("FAILED to initialize Qdrant after retries.")
        self.vector_store = None

    def scan_and_process_pdfs(self) -> int:
        """Scan upload directory and process new PDFs."""
        if not config.PDF_UPLOAD_DIR.exists():
            config.PDF_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            return 0
            
        print(f"Scanning {config.PDF_UPLOAD_DIR} for new PDFs...")
        pdf_files = list(config.PDF_UPLOAD_DIR.glob("*.pdf"))
        processed_count = 0
        
        for pdf_path in pdf_files:
            try:
                chunks = self.process_pdf(str(pdf_path))
                if chunks > 0:
                    processed_count += 1
            except Exception as e:
                print(f"Error auto-processing {pdf_path.name}: {e}")
                
        return processed_count
    
    def process_pdf(self, pdf_path: str) -> int:
        """
        Process a PDF file and add it to the Qdrant knowledge base.
        """
        print(f"Processing PDF: {os.path.basename(pdf_path)}")
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            print(f"Loaded {len(pages)} pages.")
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return 0
        for page in pages:
            page.page_content = clean_text(page.page_content)
        chunks = self.text_splitter.split_documents(pages)
        print(f"Split into {len(chunks)} chunks.")
        
        if not chunks:
            print("No chunks created.")
            return 0
        ids = []
        new_chunks = []
        pdf_name = os.path.basename(pdf_path)
        
        for i, chunk in enumerate(chunks):
            content_hash = hashlib.md5(f"{chunk.page_content}".encode()).hexdigest()
            ids.append(content_hash)
            
            chunk.metadata['source'] = pdf_name
            chunk.metadata['chunk_index'] = i
            new_chunks.append(chunk)

        if self.vector_store:
            try:
                print(f"Upserting {len(new_chunks)} chunks to Qdrant...")
                self.vector_store.add_documents(new_chunks, ids=ids)
                print(f"Successfully saved to Qdrant collection '{config.QDRANT_COLLECTION_NAME}'.")
            except Exception as e:
                print(f"ERROR saving to Qdrant: {e}")
                return 0
        else:
            print("Vector Store is not available inside process_pdf!")
            return 0

        self._export_chunks_debug(pdf_name, new_chunks)

        self._build_bm25_index()
        
        return len(new_chunks)

    def _export_chunks_debug(self, filename: str, chunks: List[Document]):
        """Export chunks to a readable format for inspection."""
        try:
            debug_dir = config.DATA_DIR / "vector_database_debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            output_file = debug_dir / f"{filename}_chunks.json"
            
            export_data = []
            for i, chunk in enumerate(chunks, 1):
                export_data.append({
                    "chunk_id": i,
                    "content": chunk.page_content,
                    "metadata": chunk.metadata
                })
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"Debug exported to {output_file}")
        except Exception as e:
            print(f"Error exporting debug: {e}")
    
    def _build_bm25_index(self):
        """Build BM25 index from existing documents in Qdrant."""
        if not self.client or not self.vector_store:
            print("Cannot build BM25 index: Qdrant not initialized")
            return
        
        try:
            print("Building BM25 index from Qdrant documents...")
            collection_info = self.client.get_collection(config.QDRANT_COLLECTION_NAME)
            
            if collection_info.points_count == 0:
                print("No documents in Qdrant, BM25 index empty")
                self.bm25_index = None
                self.bm25_documents = []
                return
            
            scroll_result = self.client.scroll(
                collection_name=config.QDRANT_COLLECTION_NAME,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            points = scroll_result[0]
            self.bm25_documents = []
            
            for point in points:
                content = point.payload.get('page_content', '')
                metadata = point.payload.get('metadata', {})
                doc = Document(page_content=content, metadata=metadata)
                self.bm25_documents.append(doc)
            tokenized_docs = [doc.page_content.lower().split() for doc in self.bm25_documents]
            self.bm25_index = BM25Okapi(tokenized_docs)
            
            print(f"BM25 index built with {len(self.bm25_documents)} documents")
        except Exception as e:
            print(f"Error building BM25 index: {e}")
            self.bm25_index = None
            self.bm25_documents = []
    
    
    def search(self, query: str, search_type: str = "hybrid", k: int = config.TOP_K_RESULTS) -> List[Tuple[Document, float]]:
        """Search for relevant documents using hybrid approach."""
        if self.vector_store is None:
            print("Search failed: Vector Store is None")
            return []
        
        print(f"Searching for: '{query}' (type: {search_type}, limit {k})")
        
        if search_type == "hybrid":
            return self._hybrid_search(query, k)
        elif search_type == "semantic":
            return self._semantic_search(query, k)
        elif search_type == "keyword":
            return self._keyword_search(query, k)
        else:
            return self._hybrid_search(query, k)
    
    def _semantic_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Perform semantic vector search."""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            print(f"Semantic search found {len(results)} results.")
            return results
        except Exception as e:
            print(f"Semantic search error: {e}")
            return []
    
    def _keyword_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Perform BM25 keyword search."""
        if not self.bm25_index or not self.bm25_documents:
            print("BM25 index not available, falling back to semantic search")
            return self._semantic_search(query, k)
        
        try:
            tokenized_query = query.lower().split()
            scores = self.bm25_index.get_scores(tokenized_query)
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
            results = [(self.bm25_documents[i], float(scores[i])) for i in top_indices]
            print(f"Keyword search found {len(results)} results.")
            return results
        except Exception as e:
            print(f"Keyword search error: {e}")
            return []
    
    def _hybrid_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Perform hybrid search combining semantic and keyword results."""
        semantic_results = self._semantic_search(query, k=k*2)
        keyword_results = self._keyword_search(query, k=k*2)
        
        if not semantic_results and not keyword_results:
            return []
        
        fused_results = reciprocal_rank_fusion(semantic_results, keyword_results, k=60)
        final_results = fused_results[:k]
        print(f"Hybrid search returned {len(final_results)} results after fusion.")
        return final_results


    def get_stats(self) -> Dict[str, any]:
        """Get statistics from Qdrant."""
        if not self.client:
             return {'total_chunks': 0, 'total_documents': 0, 'document_names': [], 'has_data': False}

        try:
            count_result = self.client.count(collection_name=config.QDRANT_COLLECTION_NAME)
            count = count_result.count
            
            files = [f.name for f in config.PDF_UPLOAD_DIR.glob("*.pdf")] if config.PDF_UPLOAD_DIR.exists() else []
            
            return {
                'total_chunks': count,
                'total_documents': len(files),
                'document_names': files,
                'has_data': count > 0
            }
        except Exception as e:
            print(f"Stats error: {e}")
            return {'total_chunks': 0, 'total_documents': 0, 'document_names': [], 'has_data': False}

    def clear_all(self):
        """Clear Qdrant collection."""
        if self.client:
            try:
                self.client.delete_collection(config.QDRANT_COLLECTION_NAME)
                self._initialize_qdrant()

                import shutil
                debug_dir = config.DATA_DIR / "vector_database_debug"
                if debug_dir.exists():
                    shutil.rmtree(debug_dir)
                    debug_dir.mkdir()
                print("All data cleared.")
            except Exception as e:
                print(f"Error clearing data: {e}")