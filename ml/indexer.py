import os
import pickle
import numpy as np
from typing import List, Dict

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_SEMANTIC_LIBS = True
except ImportError:
    HAS_SEMANTIC_LIBS = False

class SemanticIndexer:
    def __init__(self):
        self.model = None
        self.index = None
        self.titles = []
        
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.books_pkl_path = os.path.join(base_dir, "books.pkl")
        self.popular_pkl_path = os.path.join(base_dir, "popular.pkl")
        
        self.initialize_search()

    def initialize_search(self):
        # Retrieve unique list of book titles
        unique_titles = set()
        
        if os.path.exists(self.popular_pkl_path):
            with open(self.popular_pkl_path, "rb") as f:
                pop_df = pickle.load(f)
                unique_titles.update(pop_df["Book-Title"].astype(str).tolist())
                
        if os.path.exists(self.books_pkl_path):
            with open(self.books_pkl_path, "rb") as f:
                books_df = pickle.load(f)
                # Seed first 300 books to save memory during local validation
                unique_titles.update(books_df["Book-Title"].astype(str).head(300).tolist())
                
        self.titles = list(unique_titles)
        
        if HAS_SEMANTIC_LIBS:
            try:
                # Load lightweight model
                print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                embeddings = self.model.encode(self.titles, show_progress_bar=False)
                
                # Build FAISS index
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(np.array(embeddings).astype("float32"))
                print(f"Successfully built FAISS vector search index with {len(self.titles)} book titles.")
            except Exception as e:
                print(f"Error compiling FAISS index: {e}. Falling back to keyword distance search.")
                self.model = None
                self.index = None

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        results = []
        if not self.titles:
            return results

        # Scenario 1: FAISS Semantic Search
        if HAS_SEMANTIC_LIBS and self.model and self.index:
            try:
                query_vector = self.model.encode([query])
                distances, indices = self.index.search(np.array(query_vector).astype("float32"), limit)
                
                for dist, idx in zip(distances[0], indices[0]):
                    if idx < len(self.titles):
                        # Convert L2 distance to simulated similarity score [0 to 1]
                        score = 1.0 / (1.0 + float(dist))
                        results.append({
                            "title": self.titles[idx],
                            "score": round(score, 4)
                        })
                return results
            except Exception as e:
                print(f"FAISS search failed: {e}. Falling back to standard string checks.")
        
        # Scenario 2: Keyword Similarity Fallback (if vector libraries are missing/failed)
        query_words = set(query.lower().split())
        matched = []
        
        for title in self.titles:
            title_lower = title.lower()
            overlap = 0
            for word in query_words:
                if word in title_lower:
                    overlap += 1
            if overlap > 0:
                # Basic similarity ratio based on overlapping keywords
                score = overlap / (len(query_words) + 0.1 * len(title_lower.split()))
                matched.append((title, score))
                
        # Sort matches by score
        matched.sort(key=lambda x: x[1], reverse=True)
        for title, score in matched[:limit]:
            results.append({
                "title": title,
                "score": round(0.5 + 0.5 * score, 4) # bound between 0.5 and 1.0
            })
            
        return results
