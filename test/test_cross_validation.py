#!/usr/bin/env python3
"""
Cross-Validation Testing for Book Recommendation System
This script implements k-fold cross-validation to evaluate model robustness.
"""

import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import random
from collections import defaultdict
import time
import warnings
warnings.filterwarnings('ignore')

def load_data():
    """Load all necessary data files"""
    print("🔄 Loading data for cross-validation...")
    
    books_df = pd.read_csv('Books.csv')
    ratings_df = pd.read_csv('Ratings.csv')
    
    # Load original model files
    pt = pickle.load(open('pt.pkl', 'rb'))
    books_pkl = pickle.load(open('books.pkl', 'rb'))
    similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))
    
    print("✅ Data loaded successfully!")
    return books_df, ratings_df, pt, books_pkl, similarity_scores

def create_pivot_table(ratings_subset, books_df, min_ratings=50):
    """Create pivot table from ratings subset"""
    # Merge ratings with book titles
    ratings_with_books = ratings_subset.merge(books_df[['ISBN', 'Book-Title']], on='ISBN')
    
    # Count ratings per book
    book_rating_counts = ratings_with_books.groupby('Book-Title')['Book-Rating'].count()
    popular_books = book_rating_counts[book_rating_counts >= min_ratings].index
    
    # Filter to popular books only
    filtered_ratings = ratings_with_books[ratings_with_books['Book-Title'].isin(popular_books)]
    
    # Create pivot table
    pt = filtered_ratings.pivot_table(index='Book-Title', columns='User-ID', values='Book-Rating')
    pt.fillna(0, inplace=True)
    
    return pt

def calculate_similarity_matrix(pt):
    """Calculate cosine similarity matrix for books"""
    similarity_scores = cosine_similarity(pt)
    return similarity_scores

def get_recommendations_cv(book_title, pt, similarity_scores, num_recommendations=5):
    """Get recommendations using cross-validation model"""
    try:
        if book_title not in pt.index:
            return []
            
        index = list(pt.index).index(book_title)
        similar_items = sorted(list(enumerate(similarity_scores[index])), 
                             key=lambda x: x[1], reverse=True)[1:num_recommendations+1]
        
        recommendations = []
        for i in similar_items:
            if i[0] < len(pt.index):
                recommendations.append(pt.index[i[0]])
        
        return recommendations
        
    except (IndexError, ValueError, KeyError):
        return []

def evaluate_fold_performance(train_pt, test_ratings, books_df, similarity_scores):
    """Evaluate performance on a single fold"""
    metrics = {
        'hit_rate': 0,
        'precision': 0,
        'recall': 0,
        'coverage': 0,
        'diversity': 0,
        'response_time': 0
    }
    
    # Get test books that are also in training set
    test_books = set(test_ratings['Book-Title'].unique())
    available_test_books = test_books.intersection(set(train_pt.index))
    
    if len(available_test_books) == 0:
        return metrics
    
    # Sample test books for evaluation
    sample_books = random.sample(list(available_test_books), min(20, len(available_test_books)))
    
    hits = 0
    total_recommendations = 0
    all_recommendations = set()
    response_times = []
    
    for book in sample_books:
        start_time = time.time()
        recommendations = get_recommendations_cv(book, train_pt, similarity_scores, 5)
        end_time = time.time()
        
        response_times.append(end_time - start_time)
        
        if recommendations:
            total_recommendations += len(recommendations)
            all_recommendations.update(recommendations)
            
            # Check if any recommended book is in user's actual preferences
            # (simplified: assume books with high ratings are preferred)
            user_books = set(test_ratings[test_ratings['Book-Rating'] >= 7]['Book-Title'].unique())
            if any(rec in user_books for rec in recommendations):
                hits += 1
    
    # Calculate metrics
    if len(sample_books) > 0:
        metrics['hit_rate'] = hits / len(sample_books)
        metrics['response_time'] = np.mean(response_times)
    
    if total_recommendations > 0:
        metrics['precision'] = hits / len(sample_books)  # Simplified precision
    
    # Coverage: percentage of catalog covered by recommendations
    total_books = len(train_pt.index)
    metrics['coverage'] = len(all_recommendations) / total_books if total_books > 0 else 0
    
    # Diversity: average pairwise distance between recommendations
    if len(all_recommendations) > 1:
        rec_indices = [list(train_pt.index).index(book) for book in all_recommendations 
                      if book in train_pt.index]
        if len(rec_indices) > 1:
            diversities = []
            for i in range(len(rec_indices)):
                for j in range(i+1, len(rec_indices)):
                    similarity = similarity_scores[rec_indices[i]][rec_indices[j]]
                    diversity = 1 - similarity  # Diversity is inverse of similarity
                    diversities.append(diversity)
            metrics['diversity'] = np.mean(diversities) if diversities else 0
    
    return metrics

def perform_cross_validation(ratings_df, books_df, k_folds=5, min_ratings=30):
    """Perform k-fold cross-validation"""
    print(f"\n🔄 Performing {k_folds}-fold cross-validation...")
    
    # Filter ratings to have enough data
    book_counts = ratings_df.groupby('ISBN').size()
    popular_isbns = book_counts[book_counts >= min_ratings].index
    filtered_ratings = ratings_df[ratings_df['ISBN'].isin(popular_isbns)]
    
    print(f"✅ Using {len(filtered_ratings)} ratings for cross-validation")
    
    # Create k-fold splits
    kf = KFold(n_splits=k_folds, shuffle=True, random_state=42)
    
    fold_results = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(filtered_ratings)):
        print(f"\n📊 Processing Fold {fold_idx + 1}/{k_folds}...")
        
        # Split data
        train_ratings = filtered_ratings.iloc[train_idx]
        test_ratings = filtered_ratings.iloc[test_idx]
        
        # Create training model
        try:
            train_pt = create_pivot_table(train_ratings, books_df, min_ratings=min_ratings//2)
            
            if len(train_pt) < 10:  # Need minimum books for meaningful evaluation
                print(f"   ⚠️  Fold {fold_idx + 1}: Insufficient books ({len(train_pt)}), skipping...")
                continue
            
            # Calculate similarity matrix
            similarity_scores = calculate_similarity_matrix(train_pt)
            
            # Evaluate fold performance
            metrics = evaluate_fold_performance(train_pt, test_ratings, books_df, similarity_scores)
            
            metrics['fold'] = fold_idx + 1
            metrics['train_books'] = len(train_pt)
            metrics['test_ratings'] = len(test_ratings)
            
            fold_results.append(metrics)
            
            print(f"   ✅ Fold {fold_idx + 1} completed:")
            print(f"      Books in model: {len(train_pt)}")
            print(f"      Hit Rate: {metrics['hit_rate']:.3f}")
            print(f"      Coverage: {metrics['coverage']:.3f}")
            print(f"      Diversity: {metrics['diversity']:.3f}")
            
        except Exception as e:
            print(f"   ❌ Fold {fold_idx + 1} failed: {str(e)}")
            continue
    
    return fold_results

def analyze_cross_validation_results(fold_results):
    """Analyze and report cross-validation results"""
    if not fold_results:
        print("❌ No valid folds completed!")
        return
    
    print(f"\n📈 CROSS-VALIDATION RESULTS ANALYSIS")
    print("=" * 80)
    
    # Calculate statistics for each metric
    metrics = ['hit_rate', 'precision', 'recall', 'coverage', 'diversity', 'response_time']
    
    print(f"\n📊 PERFORMANCE ACROSS {len(fold_results)} FOLDS:")
    print("-" * 60)
    
    results_summary = {}
    
    for metric in metrics:
        values = [fold[metric] for fold in fold_results if metric in fold]
        if values:
            mean_val = np.mean(values)
            std_val = np.std(values)
            min_val = np.min(values)
            max_val = np.max(values)
            
            results_summary[metric] = {
                'mean': mean_val,
                'std': std_val,
                'min': min_val,
                'max': max_val
            }
            
            print(f"{metric.replace('_', ' ').title():15}: {mean_val:.4f} (±{std_val:.4f}) [{min_val:.4f}, {max_val:.4f}]")
    
    # Model stability analysis
    print(f"\n🔍 MODEL STABILITY ANALYSIS:")
    print("-" * 40)
    
    hit_rates = [fold['hit_rate'] for fold in fold_results]
    hit_rate_cv = np.std(hit_rates) / np.mean(hit_rates) if np.mean(hit_rates) > 0 else float('inf')
    
    if hit_rate_cv < 0.2:
        stability = "🎯 EXCELLENT - Very stable across folds"
    elif hit_rate_cv < 0.5:
        stability = "👍 GOOD - Reasonably stable"
    elif hit_rate_cv < 1.0:
        stability = "⚠️  FAIR - Some variability between folds"
    else:
        stability = "❌ POOR - High variability, model unstable"
    
    print(f"Coefficient of Variation: {hit_rate_cv:.3f}")
    print(f"Stability Assessment: {stability}")
    
    # Performance consistency
    print(f"\n📋 DETAILED FOLD BREAKDOWN:")
    print("-" * 50)
    for i, fold in enumerate(fold_results):
        print(f"Fold {fold['fold']:2d}: Hit Rate={fold['hit_rate']:.3f}, "
              f"Coverage={fold['coverage']:.3f}, Books={fold['train_books']:3d}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 30)
    
    avg_hit_rate = results_summary.get('hit_rate', {}).get('mean', 0)
    avg_coverage = results_summary.get('coverage', {}).get('mean', 0)
    avg_diversity = results_summary.get('diversity', {}).get('mean', 0)
    
    if avg_hit_rate > 0.3:
        print("✅ Good recommendation accuracy across folds")
    else:
        print("⚠️  Consider improving recommendation algorithm")
    
    if avg_coverage > 0.1:
        print("✅ Good catalog coverage")
    else:
        print("⚠️  Low catalog coverage - consider expanding recommendations")
    
    if avg_diversity > 0.5:
        print("✅ Good recommendation diversity")
    else:
        print("⚠️  Low diversity - recommendations may be too similar")
    
    if hit_rate_cv < 0.3:
        print("✅ Model is stable and reliable")
    else:
        print("⚠️  Model shows instability - consider more robust algorithms")
    
    return results_summary

def compare_with_baseline(fold_results, original_pt):
    """Compare cross-validation results with original model"""
    print(f"\n🔄 Comparing with baseline model...")
    
    # Test original model on sample books
    sample_books = random.sample(list(original_pt.index), min(20, len(original_pt.index)))
    
    original_similarity = pickle.load(open('similarity_scores.pkl', 'rb'))
    
    baseline_metrics = {
        'coverage': 0,
        'diversity': 0,
        'response_time': 0
    }
    
    all_recommendations = set()
    response_times = []
    
    for book in sample_books:
        start_time = time.time()
        recommendations = get_recommendations_cv(book, original_pt, original_similarity, 5)
        end_time = time.time()
        
        response_times.append(end_time - start_time)
        all_recommendations.update(recommendations)
    
    baseline_metrics['coverage'] = len(all_recommendations) / len(original_pt.index)
    baseline_metrics['response_time'] = np.mean(response_times)
    
    # Calculate diversity
    if len(all_recommendations) > 1:
        rec_indices = [list(original_pt.index).index(book) for book in all_recommendations 
                      if book in original_pt.index]
        if len(rec_indices) > 1:
            diversities = []
            for i in range(len(rec_indices)):
                for j in range(i+1, len(rec_indices)):
                    similarity = original_similarity[rec_indices[i]][rec_indices[j]]
                    diversity = 1 - similarity
                    diversities.append(diversity)
            baseline_metrics['diversity'] = np.mean(diversities) if diversities else 0
    
    print(f"\n📊 BASELINE vs CROSS-VALIDATION COMPARISON:")
    print("-" * 60)
    
    if fold_results:
        cv_coverage = np.mean([fold['coverage'] for fold in fold_results])
        cv_diversity = np.mean([fold['diversity'] for fold in fold_results])
        cv_response_time = np.mean([fold['response_time'] for fold in fold_results])
        
        print(f"Coverage    - Baseline: {baseline_metrics['coverage']:.4f}, CV: {cv_coverage:.4f}")
        print(f"Diversity   - Baseline: {baseline_metrics['diversity']:.4f}, CV: {cv_diversity:.4f}")
        print(f"Response    - Baseline: {baseline_metrics['response_time']:.4f}s, CV: {cv_response_time:.4f}s")
        
        # Determine if CV results are consistent with baseline
        coverage_diff = abs(baseline_metrics['coverage'] - cv_coverage)
        diversity_diff = abs(baseline_metrics['diversity'] - cv_diversity)
        
        if coverage_diff < 0.05 and diversity_diff < 0.1:
            print("✅ Cross-validation results are consistent with baseline model")
        else:
            print("⚠️  Some differences detected between baseline and CV results")

def main():
    """Main function to run cross-validation analysis"""
    print("🔄 CROSS-VALIDATION ANALYSIS")
    print("=" * 80)
    
    # Load data
    books_df, ratings_df, original_pt, books_pkl, original_similarity = load_data()
    
    # Perform cross-validation
    fold_results = perform_cross_validation(ratings_df, books_df, k_folds=5)
    
    if not fold_results:
        print("❌ Cross-validation failed. Need more rating data.")
        return None
    
    # Analyze results
    results_summary = analyze_cross_validation_results(fold_results)
    
    # Compare with baseline
    compare_with_baseline(fold_results, original_pt)
    
    print(f"\n🎉 Cross-validation analysis completed!")
    print(f"📊 Evaluated {len(fold_results)} folds successfully")
    
    return results_summary, fold_results

if __name__ == "__main__":
    results_summary, fold_results = main()