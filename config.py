import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
PDF_UPLOAD_DIR = DATA_DIR / "uploaded_pdfs"

DATA_DIR.mkdir(exist_ok=True)
VECTOR_STORE_DIR.mkdir(exist_ok=True)
PDF_UPLOAD_DIR.mkdir(exist_ok=True)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu" 

VECTOR_STORE_TYPE = "qdrant" 
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION_NAME = "rag_documents"
QDRANT_PATH =  DATA_DIR / "qdrant_db" 

TOP_K_RESULTS = 5
SEARCH_TYPE = "hybrid"  
HYBRID_WEIGHT_SEMANTIC = 0.6  
HYBRID_WEIGHT_KEYWORD = 0.4  

OLLAMA_MODEL = "Tuanpham/t-visstar-7b:latest"
LLM_TEMPERATURE = 0.3 
LLM_MAX_TOKENS = 1000

PAGE_TITLE = "RAG System - PDF Q&A"
PAGE_ICON = "📚"