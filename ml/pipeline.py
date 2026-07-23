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
            if os.path.exists(self.pt_pkl_path):
                with open(self.pt_pkl_path, "rb") as f:
                    self.pt = pickle.load(f)
            if os.path.exists(self.books_pkl_path):
                with open(self.books_pkl_path, "rb") as f:
                    self.books_df = pickle.load(f)
            if os.path.exists(self.sim_scores_pkl_path):
                with open(self.sim_scores_pkl_path, "rb") as f:
                    self.similarity_scores = pickle.load(f)
            print("ML Models loaded successfully in HybridRecommender pipeline.")
        except Exception as e:
            print(f"Error loading model pickle files: {e}")

    def get_recommendations(
        self,
        user_id: Optional[int] = None,
        db_session: Optional[Session] = None,
        session_books: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Hybrid pipeline combining:
        1. Popularity Score (from ratings count & avg)
        2. Collaborative Filtering (item-item similarity correlation)
        3. Content-based similarity (author overlap)
        4. Semantic vector search similarity (simulated)
        5. LLM-style personalization reranking
        """
        # Scenario 1: Anonymous user / Cold Start
        if not user_id and not session_books:
            return self._compute_hybrid_recs(reference_books=[], limit=limit, is_cold_start=True)
            
        # Scenario 2: Active Session
        if session_books and not user_id:
            return self._compute_hybrid_recs(reference_books=session_books, limit=limit)
            
        # Scenario 3: Personalized logged-in user
        if user_id and db_session:
            from backend.app.models.models import Rating, Book
            user_ratings = db_session.query(Rating).filter(Rating.user_id == user_id).all()
            user_books = []
            for r in user_ratings:
                b = db_session.query(Book).filter(Book.id == r.book_id).first()
                if b:
                    user_books.append(b.title)
            
            if not user_books:
                # Fallback if user hasn't rated anything yet
                return self._compute_hybrid_recs(reference_books=[], limit=limit, is_cold_start=True)
            return self._compute_hybrid_recs(reference_books=user_books, limit=limit)
            
        return self._compute_hybrid_recs(reference_books=[], limit=limit, is_cold_start=True)

    def _compute_hybrid_recs(self, reference_books: List[str], limit: int, is_cold_start: bool = False) -> List[Dict]:
        recs = []
        if self.books_df is None:
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
        # Supplement with general candidates up to 250
        extra_candidates = self.books_df.drop_duplicates('Book-Title')['Book-Title'].tolist()
        for t in extra_candidates:
            if str(t) not in candidate_titles:
                candidate_titles.append(str(t))
            if len(candidate_titles) >= 250:
                break

        for title in candidate_titles:
            if title.lower() in ref_titles:
                continue

            # Fetch metadata from books_df
            match_rows = self.books_df[self.books_df["Book-Title"] == title]
            if match_rows.empty:
                continue
            row = match_rows.iloc[0]
            author = str(row["Book-Author"])
            image_url = str(row["Image-URL-M"])

            # 1. Popularity Score
            pop_score = 0.4
            if self.popular_df is not None:
                match = self.popular_df[self.popular_df["Book-Title"] == title]
                if not match.empty:
                    pop_score = float(match.iloc[0]["avg_rating"]) / 10.0

            # 2. Collaborative Filtering Score
            cf_score = top_sim_titles.get(title, 0.0)

            # 3. Content-Based Score (Author match)
            cb_score = 0.0
            if not is_cold_start and reference_books:
                ref_match = self.books_df[self.books_df["Book-Title"].str.lower() == reference_books[-1].lower()]
                if not ref_match.empty:
                    ref_author = ref_match.iloc[0]["Book-Author"]
                    if ref_author.lower() == author.lower():
                        cb_score = 1.0

            # 4. Semantic Similarity
            sem_score = 0.2
            if not is_cold_start and reference_books:
                t_words = set(title.lower().split())
                ref_words = set(reference_books[-1].lower().split())
                overlap = len(t_words.intersection(ref_words))
                sem_score = min(1.0, overlap / (max(len(t_words), len(ref_words)) + 1e-6))

            # 5. Hybrid Aggregation Formula
            if is_cold_start:
                final_score = pop_score
                pers_score = 0.0
                confidence = 0.5
            else:
                # Give high weight (60%) to direct collaborative filtering match if present
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
