#!/usr/bin/env python3
"""
Precision and Recall Testing for Book Recommendation System
This script implements advanced metrics to evaluate recommendation accuracy.
"""

import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score
import random
from collections import defaultdict
import matplotlib.pyplot as plt

def load_data():
    """Load all necessary data files"""
    print("🔄 Loading data for precision/recall testing...")
    
    # Load CSV files
    books_df = pd.read_csv('Books.csv')
    ratings_df = pd.read_csv('Ratings.csv')
    
    # Load pickle files
    pt = pickle.load(open('pt.pkl', 'rb'))
    books_pkl = pickle.load(open('books.pkl', 'rb'))
    similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))
    
    print("✅ Data loaded successfully!")
    return books_df, ratings_df, pt, books_pkl, similarity_scores

def get_recommendations(book_title, pt, books_pkl, similarity_scores, num_recommendations=5):
    """Get recommendations for a specific book"""
    try:
        index = np.where(pt.index == book_title)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index])), 
                             key=lambda x: x[1], reverse=True)[1:num_recommendations+1]
        
        recommendations = []
        for i in similar_items:
            recommendations.append(pt.index[i[0]])
        
        return recommendations
        
    except (IndexError, ValueError):
        return []

def create_test_set(ratings_df, pt, test_size=0.2):
    """Create a test set by hiding some user ratings"""
    print(f"\n📊 Creating test set for evaluation...")
    
    # Filter ratings to only include books in our recommendation system
    available_books = set(pt.index)
    
    # Get book titles from ratings (need to merge with books data)
    books_df = pd.read_csv('Books.csv')
    ratings_with_titles = ratings_df.merge(books_df[['ISBN', 'Book-Title']], on='ISBN')
    
    # Filter to only books in our system
    test_ratings = ratings_with_titles[
        ratings_with_titles['Book-Title'].isin(available_books)
    ]
    
    # Only consider ratings >= 7 as "relevant" (liked books)
    relevant_ratings = test_ratings[test_ratings['Book-Rating'] >= 7]
    
    print(f"✅ Found {len(relevant_ratings)} relevant ratings for testing")
    
    # Group by user to create user profiles
    user_profiles = defaultdict(list)
    for _, rating in relevant_ratings.iterrows():
        user_profiles[rating['User-ID']].append(rating['Book-Title'])
    
    # Filter users with at least 5 rated books
    valid_users = {user: books for user, books in user_profiles.items() if len(books) >= 5}
    
    print(f"✅ Found {len(valid_users)} users with sufficient ratings")
    
    # Create train/test split for each user
    test_data = []
    train_data = []
    
    for user_id, books in list(valid_users.items())[:100]:  # Limit to 100 users for speed
        if len(books) >= 5:
            train_books, test_books = train_test_split(books, test_size=test_size, random_state=42)
            
            test_data.append({
                'user_id': user_id,
                'train_books': train_books,
                'test_books': test_books
            })
    
    print(f"✅ Created test set with {len(test_data)} users")
    return test_data

def calculate_precision_recall_for_user(user_data, pt, books_pkl, similarity_scores, top_k=5):
    """Calculate precision and recall for a single user"""
    train_books = user_data['train_books']
    test_books = set(user_data['test_books'])
    
    # Get recommendations based on user's training books
    all_recommendations = set()
    
    for book in train_books:
        recommendations = get_recommendations(book, pt, books_pkl, similarity_scores, top_k)
        all_recommendations.update(recommendations)
    
    # Remove books the user already rated in training
    all_recommendations = all_recommendations - set(train_books)
    
    # Take top K recommendations
    recommended_books = list(all_recommendations)[:top_k]
    
    # Calculate metrics
    true_positives = len(set(recommended_books) & test_books)
    
    precision = true_positives / len(recommended_books) if recommended_books else 0
    recall = true_positives / len(test_books) if test_books else 0
    
    return precision, recall, true_positives, len(recommended_books), len(test_books)

def evaluate_precision_recall(test_data, pt, books_pkl, similarity_scores, top_k_values=[5, 10, 20]):
    """Evaluate precision and recall across all test users"""
    print(f"\n📈 Evaluating Precision and Recall...")
    
    results = {}
    
    for top_k in top_k_values:
        print(f"\n🎯 Evaluating for Top-{top_k} recommendations...")
        
        precisions = []
        recalls = []
        f1_scores = []
        
        for i, user_data in enumerate(test_data):
            precision, recall, tp, rec_count, test_count = calculate_precision_recall_for_user(
                user_data, pt, books_pkl, similarity_scores, top_k
            )
            
            precisions.append(precision)
            recalls.append(recall)
            
            # Calculate F1 score
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            f1_scores.append(f1)
            
            if i < 5:  # Show details for first 5 users
                print(f"   User {user_data['user_id']}: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}")
        
        avg_precision = np.mean(precisions)
        avg_recall = np.mean(recalls)
        avg_f1 = np.mean(f1_scores)
        
        results[top_k] = {
            'precision': avg_precision,
            'recall': avg_recall,
            'f1_score': avg_f1,
            'precision_std': np.std(precisions),
            'recall_std': np.std(recalls),
            'f1_std': np.std(f1_scores)
        }
        
        print(f"✅ Top-{top_k} Results:")
        print(f"   Average Precision: {avg_precision:.4f} (±{np.std(precisions):.4f})")
        print(f"   Average Recall: {avg_recall:.4f} (±{np.std(recalls):.4f})")
        print(f"   Average F1-Score: {avg_f1:.4f} (±{np.std(f1_scores):.4f})")
    
    return results

def calculate_map_at_k(test_data, pt, books_pkl, similarity_scores, k=10):
    """Calculate Mean Average Precision at K"""
    print(f"\n🎯 Calculating Mean Average Precision at {k}...")
    
    average_precisions = []
    
    for user_data in test_data[:20]:  # Limit for speed
        train_books = user_data['train_books']
        test_books = set(user_data['test_books'])
        
        # Get recommendations
        all_recommendations = []
        for book in train_books:
            recommendations = get_recommendations(book, pt, books_pkl, similarity_scores, k)
            all_recommendations.extend(recommendations)
        
        # Remove duplicates and training books
        seen = set(train_books)
        unique_recommendations = []
        for book in all_recommendations:
            if book not in seen:
                unique_recommendations.append(book)
                seen.add(book)
        
        # Take top K
        top_k_recommendations = unique_recommendations[:k]
        
        # Calculate average precision
        relevant_found = 0
        precision_sum = 0
        
        for i, book in enumerate(top_k_recommendations):
            if book in test_books:
                relevant_found += 1
                precision_at_i = relevant_found / (i + 1)
                precision_sum += precision_at_i
        
        avg_precision = precision_sum / len(test_books) if test_books else 0
        average_precisions.append(avg_precision)
    
    map_score = np.mean(average_precisions)
    print(f"✅ Mean Average Precision at {k}: {map_score:.4f}")
    
    return map_score

def calculate_ndcg_at_k(test_data, pt, books_pkl, similarity_scores, k=10):
    """Calculate Normalized Discounted Cumulative Gain at K"""
    print(f"\n📊 Calculating NDCG at {k}...")
    
    ndcg_scores = []
    
    for user_data in test_data[:20]:  # Limit for speed
        train_books = user_data['train_books']
        test_books = set(user_data['test_books'])
        
        # Get recommendations with scores
        all_recommendations = []
        for book in train_books:
            try:
                index = np.where(pt.index == book)[0][0]
                similar_items = sorted(list(enumerate(similarity_scores[index])), 
                                     key=lambda x: x[1], reverse=True)[1:k+1]
                
                for i in similar_items:
                    book_title = pt.index[i[0]]
                    if book_title not in train_books:
                        all_recommendations.append((book_title, similar_items[similar_items.index(i)][1]))
            except:
                continue
        
        # Sort by similarity score and take top K
        all_recommendations.sort(key=lambda x: x[1], reverse=True)
        top_k_recommendations = all_recommendations[:k]
        
        # Calculate DCG
        dcg = 0
        for i, (book, score) in enumerate(top_k_recommendations):
            relevance = 1 if book in test_books else 0
            dcg += relevance / np.log2(i + 2)  # i+2 because log2(1) = 0
        
        # Calculate IDCG (ideal DCG)
        ideal_relevances = [1] * min(len(test_books), k) + [0] * max(0, k - len(test_books))
        idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_relevances))
        
        # Calculate NDCG
        ndcg = dcg / idcg if idcg > 0 else 0
        ndcg_scores.append(ndcg)
    
    avg_ndcg = np.mean(ndcg_scores)
    print(f"✅ Average NDCG at {k}: {avg_ndcg:.4f}")
    
    return avg_ndcg

def generate_precision_recall_report(results, map_score, ndcg_score):
    """Generate a comprehensive precision/recall report"""
    print(f"\n📋 PRECISION & RECALL ANALYSIS REPORT")
    print("=" * 80)
    
    print(f"\n📊 DETAILED METRICS BY TOP-K:")
    for k, metrics in results.items():
        print(f"\n🎯 Top-{k} Recommendations:")
        print(f"   Precision: {metrics['precision']:.4f} (±{metrics['precision_std']:.4f})")
        print(f"   Recall:    {metrics['recall']:.4f} (±{metrics['recall_std']:.4f})")
        print(f"   F1-Score:  {metrics['f1_score']:.4f} (±{metrics['f1_std']:.4f})")
    
    print(f"\n🏆 ADVANCED METRICS:")
    print(f"   Mean Average Precision (MAP@10): {map_score:.4f}")
    print(f"   Normalized DCG (NDCG@10): {ndcg_score:.4f}")
    
    print(f"\n💡 INTERPRETATION:")
    
    # Get best performing K
    best_k = max(results.keys(), key=lambda k: results[k]['f1_score'])
    best_f1 = results[best_k]['f1_score']
    
    print(f"   • Best performing configuration: Top-{best_k} (F1: {best_f1:.4f})")
    
    if best_f1 > 0.3:
        print("   • 🎉 EXCELLENT: High precision and recall scores!")
    elif best_f1 > 0.2:
        print("   • 👍 GOOD: Decent recommendation accuracy")
    elif best_f1 > 0.1:
        print("   • ⚠️  FAIR: Room for improvement in accuracy")
    else:
        print("   • ❌ POOR: Significant accuracy improvements needed")
    
    if map_score > 0.2:
        print("   • 📈 Good ranking quality (high MAP score)")
    else:
        print("   • 📉 Consider improving recommendation ranking")
    
    print(f"\n🔧 RECOMMENDATIONS:")
    if results[5]['precision'] < 0.1:
        print("   • Increase similarity threshold for better precision")
    if results[20]['recall'] < 0.2:
        print("   • Consider hybrid approaches to improve recall")
    if ndcg_score < 0.3:
        print("   • Improve ranking algorithm for better NDCG")

def main():
    """Main function to run precision/recall analysis"""
    print("🎯 PRECISION & RECALL ANALYSIS")
    print("=" * 80)
    
    # Load data
    books_df, ratings_df, pt, books_pkl, similarity_scores = load_data()
    
    # Create test set
    test_data = create_test_set(ratings_df, pt)
    
    if not test_data:
        print("❌ Could not create test set. Need more user rating data.")
        return
    
    # Evaluate precision and recall
    results = evaluate_precision_recall(test_data, pt, books_pkl, similarity_scores)
    
    # Calculate advanced metrics
    map_score = calculate_map_at_k(test_data, pt, books_pkl, similarity_scores)
    ndcg_score = calculate_ndcg_at_k(test_data, pt, books_pkl, similarity_scores)
    
    # Generate report
    generate_precision_recall_report(results, map_score, ndcg_score)
    
    return results, map_score, ndcg_score

if __name__ == "__main__":
    results, map_score, ndcg_score = main()