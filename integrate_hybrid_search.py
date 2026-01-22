with open('rag_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_search_start = '    def search(self, query: str, search_type: str = "semantic"'
search_start_idx = content.find(old_search_start)

if search_start_idx != -1:
    get_stats_idx = content.find('\n    def get_stats(', search_start_idx)
    new_methods = '''    def search(self, query: str, search_type: str = "hybrid", k: int = config.TOP_K_RESULTS) -> List[Tuple[Document, float]]:
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

'''
    
    # Replace content
    new_content = content[:search_start_idx] + new_methods + content[get_stats_idx:]
    
    with open('rag_engine.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("SUCCESS: Hybrid search methods integrated successfully!")
else:
    print("ERROR: Could not find search method in rag_engine.py")
