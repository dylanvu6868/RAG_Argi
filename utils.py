import re
from typing import List, Dict, Tuple
import hashlib


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s,.!?;:()\-\'\"]+', '', text)
    text = text.strip()
    
    return text


def extract_page_number(metadata: Dict) -> int:
    return metadata.get('page', 0) + 1


def format_source_reference(doc_name: str, page: int) -> str:
    return f"{doc_name} (page {page})"


def calculate_file_hash(file_path: str) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def highlight_text(text: str, query: str, max_length: int = 300) -> str:
    query_terms = query.lower().split()
    if len(text) > max_length:
        text_lower = text.lower()
        first_pos = len(text)
        
        for term in query_terms:
            pos = text_lower.find(term)
            if pos != -1 and pos < first_pos:
                first_pos = pos
        
        if first_pos < len(text):
            start = max(0, first_pos - max_length // 2)
            end = min(len(text), start + max_length)
            text = "..." + text[start:end] + "..."
        else:
            text = text[:max_length] + "..."
    
    return text


def reciprocal_rank_fusion(
    semantic_results: List[Tuple[any, float]], 
    keyword_results: List[Tuple[any, float]], 
    k: int = 60
) -> List[Tuple[any, float]]:
    doc_scores = {}
    for rank, (doc, score) in enumerate(semantic_results, 1):
        doc_id = id(doc)
        if doc_id not in doc_scores:
            doc_scores[doc_id] = {'doc': doc, 'score': 0}
        doc_scores[doc_id]['score'] += 1 / (k + rank)
    for rank, (doc, score) in enumerate(keyword_results, 1):
        doc_id = id(doc)
        if doc_id not in doc_scores:
            doc_scores[doc_id] = {'doc': doc, 'score': 0}
        doc_scores[doc_id]['score'] += 1 / (k + rank)
    ranked_results = sorted(
        [(item['doc'], item['score']) for item in doc_scores.values()],
        key=lambda x: x[1],
        reverse=True
    )
    
    return ranked_results
    
def format_chat_history(history: List[Dict[str, str]]) -> str:
    formatted = []
    for msg in history:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        prefix = "🧑 User:" if role == 'user' else "🤖 Assistant:"
        formatted.append(f"{prefix}\n{content}\n")
    
    return "\n".join(formatted)