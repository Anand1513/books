import os
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

class HybridRecommender:
    def __init__(self):
        # Load precomputed datasets and model scores
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.popular_pkl_path = os.path.join(base_dir, "popular.pkl")
        self.pt_pkl_path = os.path.join(base_dir, "pt.pkl")
        self.books_pkl_path = os.path.join(base_dir, "books.pkl")
        self.sim_scores_pkl_path = os.path.join(base_dir, "similarity_scores.pkl")
        
        self.popular_df = None
        self.pt = None
        self.books_df = None
        self.similarity_scores = None
        
        self.load_models()

    def load_models(self):
        try:
            if os.path.exists(self.popular_pkl_path):
                with open(self.popular_pkl_path, "rb") as f:
                    self.popular_df = pickle.load(f)
                    self.popular_lookup = dict(zip(self.popular_df["Book-Title"], self.popular_df["avg_rating"]))
            else:
                self.popular_lookup = {}
                
            if os.path.exists(self.pt_pkl_path):
                with open(self.pt_pkl_path, "rb") as f:
                    self.pt = pickle.load(f)
            if os.path.exists(self.books_pkl_path):
                with open(self.books_pkl_path, "rb") as f:
                    self.books_df = pickle.load(f)
                    # Pre-build fast title metadata dictionary for O(1) lookup
                    dedup = self.books_df.drop_duplicates("Book-Title")
                    self.books_lookup = {
                        str(row["Book-Title"]): {
                            "author": str(row["Book-Author"]),
                            "image_url": str(row["Image-URL-M"])
                        }
                        for _, row in dedup.iterrows()
                    }
                    self.title_list = list(self.books_lookup.keys())
            else:
                self.books_lookup = {}
                self.title_list = []

            if os.path.exists(self.sim_scores_pkl_path):
                with open(self.sim_scores_pkl_path, "rb") as f:
                    self.similarity_scores = pickle.load(f)
            print("ML Models loaded & indexed successfully in HybridRecommender pipeline.")
        except Exception as e:
            print(f"Error loading model pickle files: {e}")

    def get_recommendations(
        self,
        user_id: Optional[int] = None,
        db_session: Optional[Session] = None,
        session_books: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        if not user_id and not session_books:
            return self._compute_hybrid_recs(reference_books=[], limit=limit, is_cold_start=True)
            
        if session_books and not user_id:
            return self._compute_hybrid_recs(reference_books=session_books, limit=limit)
            
        if user_id and db_session:
            from backend.app.models.models import Rating, Book
            user_ratings = db_session.query(Rating).filter(Rating.user_id == user_id).all()
            user_books = []
            for r in user_ratings:
                b = db_session.query(Book).filter(Book.id == r.book_id).first()
                if b:
                    user_books.append(b.title)
            
            if not user_books:
                return self._compute_hybrid_recs(reference_books=[], limit=limit, is_cold_start=True)
            return self._compute_hybrid_recs(reference_books=user_books, limit=limit)
            
        return self._compute_hybrid_recs(reference_books=[], limit=limit, is_cold_start=True)

    def _compute_hybrid_recs(self, reference_books: List[str], limit: int, is_cold_start: bool = False) -> List[Dict]:
        recs = []
        if not self.books_lookup:
            return recs

        ref_titles = [t.lower() for t in reference_books]
        top_sim_titles = {}

        # 1. Direct Collaborative Filtering Lookup via similarity_scores & pt
        if not is_cold_start and reference_books and self.pt is not None and self.similarity_scores is not None:
            target_book = reference_books[-1]
            matches = [i for i, title in enumerate(self.pt.index) if target_book.lower() in str(title).lower()]
            if matches:
                idx = matches[0]
                similar_items = sorted(list(enumerate(self.similarity_scores[idx])), key=lambda x: x[1], reverse=True)[1:limit+10]
                for sim_idx, score in similar_items:
                    sim_title = str(self.pt.index[sim_idx])
                    if sim_title.lower() not in ref_titles:
                        top_sim_titles[sim_title] = float(score)

        # Build candidate list combining top similarity items + general candidates
        candidate_titles = list(top_sim_titles.keys())
        for t in self.title_list:
            if t not in candidate_titles:
                candidate_titles.append(t)
            if len(candidate_titles) >= 150:
                break

        # Precompute reference author ONCE to avoid O(N) scan inside loop
        ref_author = ""
        ref_words = set()
        if not is_cold_start and reference_books:
            target_ref = reference_books[-1].lower()
            ref_words = set(target_ref.split())
            if target_ref in self.books_lookup:
                ref_author = self.books_lookup[target_ref]["author"].lower()
            else:
                for k, v in self.books_lookup.items():
                    if k.lower() == target_ref:
                        ref_author = v["author"].lower()
                        break

        for title in candidate_titles:
            if title.lower() in ref_titles:
                continue

            meta = self.books_lookup.get(title)
            if not meta:
                continue

            author = meta["author"]
            image_url = meta["image_url"]

            # 1. Popularity Score (O(1) dictionary lookup)
            pop_score = 0.4
            if title in self.popular_lookup:
                pop_score = float(self.popular_lookup[title]) / 10.0

            # 2. Collaborative Filtering Score
            cf_score = top_sim_titles.get(title, 0.0)

            # 3. Content-Based Score (O(1) precomputed author match)
            cb_score = 1.0 if (ref_author and author.lower() == ref_author) else 0.0

            # 4. Semantic Similarity
            sem_score = 0.2
            if not is_cold_start and reference_books:
                t_words = set(title.lower().split())
                overlap = len(t_words.intersection(ref_words))
                sem_score = min(1.0, overlap / (max(len(t_words), len(ref_words)) + 1e-6))

            # 5. Hybrid Aggregation Formula
            if is_cold_start:
                final_score = pop_score
                pers_score = 0.0
                confidence = 0.5
            else:
                if cf_score > 0.0:
                    final_score = (0.6 * cf_score) + (0.2 * cb_score) + (0.1 * sem_score) + (0.1 * pop_score)
                    pers_score = (0.7 * cf_score) + (0.3 * cb_score)
                    confidence = min(0.99, cf_score + 0.5)
                else:
                    final_score = (0.3 * cf_score) + (0.3 * cb_score) + (0.2 * sem_score) + (0.2 * pop_score)
                    pers_score = (0.4 * cf_score) + (0.4 * cb_score) + (0.2 * sem_score)
                    confidence = min(1.0, final_score + 0.1)

            why_reason = "Recommended because it is trending globally with high reader ratings."
            if not is_cold_start and reference_books:
                why_reason = f"Recommended based on your interest in '{reference_books[-1]}'."
                if cf_score > 0.15:
                    why_reason = f"Recommended because readers of '{reference_books[-1]}' also highly enjoyed this book."
                elif cb_score > 0.8:
                    why_reason = f"Recommended because you enjoy books by {author}."

            recs.append({
                "title": title,
                "author": author,
                "image_url": image_url,
                "score": round(final_score, 4),
                "explain": {
                    "why": why_reason,
                    "genre_similarity": round(float(0.4 + 0.6 * cb_score), 2),
                    "reader_overlap": round(float(cf_score), 2),
                    "semantic_similarity": round(float(sem_score), 2),
                    "popularity_score": round(float(pop_score), 2),
                    "personalization_score": round(float(pers_score), 2),
                    "confidence_score": round(float(confidence), 2)
                }
            })

        # Sort recommendations by final score
        recs.sort(key=lambda x: x["score"], reverse=True)
        return recs[:limit]
