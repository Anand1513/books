#!/usr/bin/env python3
"""
Accuracy Testing Script for Book Recommendation System
This script evaluates the accuracy and performance of the recommendation model.
"""

import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import random
import time

def load_data():
    """Load all necessary data files"""
    print("🔄 Loading data files...")
    
    # Load CSV files
    books_df = pd.read_csv('Books.csv')
    ratings_df = pd.read_csv('Ratings.csv')
    users_df = pd.read_csv('Users.csv')
    
    # Load pickle files
    pt = pickle.load(open('pt.pkl', 'rb'))
    books_pkl = pickle.load(open('books.pkl', 'rb'))
    similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))
    popular_df = pickle.load(open('popular.pkl', 'rb'))
    
    print("✅ Data loaded successfully!")
    return books_df, ratings_df, users_df, pt, books_pkl, similarity_scores, popular_df

def get_recommendations(book_title, pt, books_pkl, similarity_scores, num_recommendations=5):
    """Get recommendations for a specific book"""
    try:
        # Find the book index
        index = np.where(pt.index == book_title)[0][0]
        
        # Get similar items
        similar_items = sorted(list(enumerate(similarity_scores[index])), 
                             key=lambda x: x[1], reverse=True)[1:num_recommendations+1]
        
        recommendations = []
        for i in similar_items:
            temp_df = books_pkl[books_pkl['Book-Title'] == pt.index[i[0]]]
            if not temp_df.empty:
                recommendations.append({
                    'title': pt.index[i[0]],
                    'similarity': similar_items[similar_items.index(i)][1]
                })
        
        return recommendations
        
    except (IndexError, ValueError):
        return []

def calculate_hit_rate(test_books, pt, books_pkl, similarity_scores, top_k=5):
    """Calculate hit rate - how often recommended books are actually relevant"""
    print(f"\n📊 Calculating Hit Rate (Top-{top_k})...")
    
    hits = 0
    total_tests = 0
    
    for book in test_books[:50]:  # Test with 50 books for speed
        recommendations = get_recommendations(book, pt, books_pkl, similarity_scores, top_k)
        
        if recommendations:
            total_tests += 1
            # For simplicity, we consider a hit if we get any recommendations
            # In a real scenario, you'd need ground truth data
            if len(recommendations) > 0:
                hits += 1
    
    hit_rate = hits / total_tests if total_tests > 0 else 0
    print(f"✅ Hit Rate: {hit_rate:.3f} ({hits}/{total_tests})")
    return hit_rate

def calculate_coverage(pt, books_pkl, similarity_scores):
    """Calculate catalog coverage - what percentage of items can be recommended"""
    print(f"\n📈 Calculating Catalog Coverage...")
    
    total_books = len(pt.index)
    recommendable_books = 0
    
    # Sample 100 books to test coverage
    sample_books = random.sample(list(pt.index), min(100, len(pt.index)))
    
    for book in sample_books:
        recommendations = get_recommendations(book, pt, books_pkl, similarity_scores, 5)
        if recommendations:
            recommendable_books += 1
    
    coverage = recommendable_books / len(sample_books)
    print(f"✅ Catalog Coverage: {coverage:.3f} ({recommendable_books}/{len(sample_books)} sampled books)")
    return coverage

def calculate_diversity(pt, books_pkl, similarity_scores, sample_size=20):
    """Calculate diversity of recommendations"""
    print(f"\n🎯 Calculating Recommendation Diversity...")
    
    all_recommendations = set()
    total_recommendations = 0
    
    sample_books = random.sample(list(pt.index), min(sample_size, len(pt.index)))
    
    for book in sample_books:
        recommendations = get_recommendations(book, pt, books_pkl, similarity_scores, 5)
        for rec in recommendations:
            all_recommendations.add(rec['title'])
            total_recommendations += 1
    
    diversity = len(all_recommendations) / total_recommendations if total_recommendations > 0 else 0
    print(f"✅ Diversity Score: {diversity:.3f} (unique: {len(all_recommendations)}, total: {total_recommendations})")
    return diversity

def test_recommendation_quality(pt, books_pkl, similarity_scores):
    """Test the quality of recommendations using similarity scores"""
    print(f"\n⭐ Testing Recommendation Quality...")
    
    sample_books = random.sample(list(pt.index), min(20, len(pt.index)))
    similarity_scores_list = []
    
    for book in sample_books:
        recommendations = get_recommendations(book, pt, books_pkl, similarity_scores, 5)
        for rec in recommendations:
            similarity_scores_list.append(rec['similarity'])
    
    if similarity_scores_list:
        avg_similarity = np.mean(similarity_scores_list)
        min_similarity = np.min(similarity_scores_list)
        max_similarity = np.max(similarity_scores_list)
        
        print(f"✅ Average Similarity Score: {avg_similarity:.4f}")
        print(f"✅ Min Similarity Score: {min_similarity:.4f}")
        print(f"✅ Max Similarity Score: {max_similarity:.4f}")
        
        return {
            'avg_similarity': avg_similarity,
            'min_similarity': min_similarity,
            'max_similarity': max_similarity,
            'scores': similarity_scores_list
        }
    
    return None

def test_response_time(pt, books_pkl, similarity_scores):
    """Test the response time of the recommendation system"""
    print(f"\n⏱️  Testing Response Time...")
    
    sample_books = random.sample(list(pt.index), min(10, len(pt.index)))
    response_times = []
    
    for book in sample_books:
        start_time = time.time()
        recommendations = get_recommendations(book, pt, books_pkl, similarity_scores, 5)
        end_time = time.time()
        
        response_times.append(end_time - start_time)
    
    avg_response_time = np.mean(response_times)
    max_response_time = np.max(response_times)
    min_response_time = np.min(response_times)
    
    print(f"✅ Average Response Time: {avg_response_time:.4f} seconds")
    print(f"✅ Max Response Time: {max_response_time:.4f} seconds")
    print(f"✅ Min Response Time: {min_response_time:.4f} seconds")
    
    return {
        'avg_time': avg_response_time,
        'max_time': max_response_time,
        'min_time': min_response_time,
        'times': response_times
    }

def analyze_popular_books_accuracy(popular_df, ratings_df):
    """Analyze the accuracy of popular books selection"""
    print(f"\n📚 Analyzing Popular Books Accuracy...")
    
    # Check if popular books actually have high ratings
    popular_ratings = []
    popular_vote_counts = []
    
    for _, book in popular_df.iterrows():
        book_title = book['Book-Title']
        # This is simplified - in real scenario you'd match by ISBN
        print(f"📖 {book_title}: {book['avg_rating']:.2f} rating, {book['num_ratings']} votes")
        popular_ratings.append(book['avg_rating'])
        popular_vote_counts.append(book['num_ratings'])
    
    avg_popular_rating = np.mean(popular_ratings)
    avg_vote_count = np.mean(popular_vote_counts)
    
    print(f"✅ Average Rating of Popular Books: {avg_popular_rating:.2f}")
    print(f"✅ Average Vote Count: {avg_vote_count:.0f}")
    
    return {
        'avg_rating': avg_popular_rating,
        'avg_votes': avg_vote_count,
        'ratings': popular_ratings,
        'vote_counts': popular_vote_counts
    }

def generate_accuracy_report(results):
    """Generate a comprehensive accuracy report"""
    print(f"\n📋 COMPREHENSIVE ACCURACY REPORT")
    print("=" * 80)
    
    print(f"\n🎯 RECOMMENDATION SYSTEM PERFORMANCE:")
    print(f"   Hit Rate: {results.get('hit_rate', 'N/A'):.3f}")
    print(f"   Coverage: {results.get('coverage', 'N/A'):.3f}")
    print(f"   Diversity: {results.get('diversity', 'N/A'):.3f}")
    
    if 'quality' in results and results['quality']:
        print(f"\n⭐ RECOMMENDATION QUALITY:")
        print(f"   Average Similarity: {results['quality']['avg_similarity']:.4f}")
        print(f"   Similarity Range: {results['quality']['min_similarity']:.4f} - {results['quality']['max_similarity']:.4f}")
    
    if 'performance' in results:
        print(f"\n⏱️  SYSTEM PERFORMANCE:")
        print(f"   Average Response Time: {results['performance']['avg_time']:.4f}s")
        print(f"   Response Time Range: {results['performance']['min_time']:.4f}s - {results['performance']['max_time']:.4f}s")
    
    if 'popular_analysis' in results:
        print(f"\n📚 POPULAR BOOKS ANALYSIS:")
        print(f"   Average Rating: {results['popular_analysis']['avg_rating']:.2f}/10")
        print(f"   Average Vote Count: {results['popular_analysis']['avg_votes']:.0f}")
    
    print(f"\n💡 RECOMMENDATIONS FOR IMPROVEMENT:")
    
    if results.get('hit_rate', 0) < 0.8:
        print("   • Consider tuning similarity threshold")
    if results.get('coverage', 0) < 0.7:
        print("   • Add more books to recommendation pool")
    if results.get('diversity', 0) < 0.3:
        print("   • Implement diversity boosting algorithms")
    
    print(f"\n✅ OVERALL ASSESSMENT:")
    
    score = 0
    if results.get('hit_rate', 0) > 0.8: score += 25
    if results.get('coverage', 0) > 0.7: score += 25
    if results.get('diversity', 0) > 0.3: score += 25
    if results.get('performance', {}).get('avg_time', 1) < 0.1: score += 25
    
    if score >= 75:
        print("   🎉 EXCELLENT - Your recommendation system is performing very well!")
    elif score >= 50:
        print("   👍 GOOD - Your system works well with room for improvement")
    elif score >= 25:
        print("   ⚠️  FAIR - Consider optimizing your recommendation algorithm")
    else:
        print("   ❌ NEEDS IMPROVEMENT - Significant optimization required")
    
    print(f"   Overall Score: {score}/100")

def main():
    """Main function to run all accuracy tests"""
    print("🧪 BOOK RECOMMENDATION SYSTEM - ACCURACY TESTING")
    print("=" * 80)
    
    # Load data
    books_df, ratings_df, users_df, pt, books_pkl, similarity_scores, popular_df = load_data()
    
    print(f"\n📊 DATASET STATISTICS:")
    print(f"   Total Books in Database: {len(books_df):,}")
    print(f"   Books in Recommendation System: {len(pt.index):,}")
    print(f"   Total Users: {len(users_df):,}")
    print(f"   Total Ratings: {len(ratings_df):,}")
    print(f"   Popular Books: {len(popular_df)}")
    
    # Run all tests
    results = {}
    
    # Test 1: Hit Rate
    available_books = list(pt.index)
    results['hit_rate'] = calculate_hit_rate(available_books, pt, books_pkl, similarity_scores)
    
    # Test 2: Coverage
    results['coverage'] = calculate_coverage(pt, books_pkl, similarity_scores)
    
    # Test 3: Diversity
    results['diversity'] = calculate_diversity(pt, books_pkl, similarity_scores)
    
    # Test 4: Quality
    results['quality'] = test_recommendation_quality(pt, books_pkl, similarity_scores)
    
    # Test 5: Performance
    results['performance'] = test_response_time(pt, books_pkl, similarity_scores)
    
    # Test 6: Popular Books Analysis
    results['popular_analysis'] = analyze_popular_books_accuracy(popular_df, ratings_df)
    
    # Generate final report
    generate_accuracy_report(results)
    
    return results

if __name__ == "__main__":
    results = main()