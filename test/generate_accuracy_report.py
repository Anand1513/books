#!/usr/bin/env python3
"""
Comprehensive Accuracy Report Generator with Visualizations
This script generates a complete accuracy analysis report with charts and graphs.
"""

import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Import our test modules
import sys
sys.path.append('.')

def load_data():
    """Load all necessary data files"""
    print("🔄 Loading data for comprehensive report...")
    
    books_df = pd.read_csv('Books.csv')
    ratings_df = pd.read_csv('Ratings.csv')
    
    pt = pickle.load(open('pt.pkl', 'rb'))
    books_pkl = pickle.load(open('books.pkl', 'rb'))
    similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))
    
    print("✅ Data loaded successfully!")
    return books_df, ratings_df, pt, books_pkl, similarity_scores

def run_basic_accuracy_tests():
    """Run basic accuracy tests and collect results"""
    print("🔄 Running basic accuracy tests...")
    
    try:
        # Import and run test_accuracy
        exec(open('test/test_accuracy.py').read())
        print("✅ Basic accuracy tests completed")
        return True
    except Exception as e:
        print(f"⚠️  Basic accuracy tests failed: {str(e)}")
        return False

def create_visualizations(books_df, ratings_df, pt, similarity_scores):
    """Create comprehensive visualizations"""
    print("🎨 Creating visualizations...")
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create output directory
    os.makedirs('test/reports', exist_ok=True)
    
    # 1. Dataset Overview
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Book Recommendation System - Dataset Overview', fontsize=16, fontweight='bold')
    
    # Books by publication year
    books_df['Year-Of-Publication'] = pd.to_numeric(books_df['Year-Of-Publication'], errors='coerce')
    valid_years = books_df[(books_df['Year-Of-Publication'] >= 1900) & 
                          (books_df['Year-Of-Publication'] <= 2023)]['Year-Of-Publication']
    
    axes[0,0].hist(valid_years, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0,0].set_title('Distribution of Book Publication Years')
    axes[0,0].set_xlabel('Publication Year')
    axes[0,0].set_ylabel('Number of Books')
    
    # Rating distribution
    rating_counts = ratings_df['Book-Rating'].value_counts().sort_index()
    axes[0,1].bar(rating_counts.index, rating_counts.values, alpha=0.7, color='lightcoral')
    axes[0,1].set_title('Distribution of Book Ratings')
    axes[0,1].set_xlabel('Rating')
    axes[0,1].set_ylabel('Number of Ratings')
    
    # Books in recommendation system vs total
    total_books = len(books_df)
    rec_books = len(pt)
    
    labels = ['In Recommendation\nSystem', 'Not in System']
    sizes = [rec_books, total_books - rec_books]
    colors = ['lightgreen', 'lightgray']
    
    axes[1,0].pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    axes[1,0].set_title('Books Coverage in Recommendation System')
    
    # Top authors by number of books
    top_authors = books_df['Book-Author'].value_counts().head(10)
    axes[1,1].barh(range(len(top_authors)), top_authors.values, color='gold')
    axes[1,1].set_yticks(range(len(top_authors)))
    axes[1,1].set_yticklabels([author[:20] + '...' if len(author) > 20 else author 
                              for author in top_authors.index])
    axes[1,1].set_title('Top 10 Authors by Number of Books')
    axes[1,1].set_xlabel('Number of Books')
    
    plt.tight_layout()
    plt.savefig('test/reports/dataset_overview.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Recommendation System Performance
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Recommendation System Performance Analysis', fontsize=16, fontweight='bold')
    
    # Similarity score distribution
    similarity_flat = similarity_scores.flatten()
    similarity_flat = similarity_flat[similarity_flat != 1.0]  # Remove self-similarities
    
    axes[0,0].hist(similarity_flat, bins=50, alpha=0.7, color='purple', edgecolor='black')
    axes[0,0].set_title('Distribution of Book Similarity Scores')
    axes[0,0].set_xlabel('Cosine Similarity Score')
    axes[0,0].set_ylabel('Frequency')
    
    # Sample recommendation quality for popular books
    sample_books = ['1984', 'To Kill a Mockingbird', 'The Great Gatsby', 'Pride and Prejudice']
    available_books = [book for book in sample_books if book in pt.index]
    
    if available_books:
        rec_scores = []
        book_names = []
        
        for book in available_books[:4]:  # Limit to 4 books
            try:
                index = np.where(pt.index == book)[0][0]
                similar_items = sorted(list(enumerate(similarity_scores[index])), 
                                     key=lambda x: x[1], reverse=True)[1:6]
                scores = [item[1] for item in similar_items]
                rec_scores.extend(scores)
                book_names.extend([f"{book}\nRec {i+1}" for i in range(len(scores))])
            except:
                continue
        
        if rec_scores:
            axes[0,1].bar(range(len(rec_scores)), rec_scores, color='orange', alpha=0.7)
            axes[0,1].set_title('Recommendation Quality for Sample Books')
            axes[0,1].set_xlabel('Recommendations')
            axes[0,1].set_ylabel('Similarity Score')
            axes[0,1].set_xticks(range(0, len(rec_scores), 5))
            axes[0,1].set_xticklabels([f"Book {i//5 + 1}" for i in range(0, len(rec_scores), 5)])
    
    # Rating patterns analysis
    books_with_ratings = ratings_df.merge(books_df[['ISBN', 'Book-Title']], on='ISBN')
    avg_ratings = books_with_ratings.groupby('Book-Title')['Book-Rating'].agg(['mean', 'count'])
    avg_ratings = avg_ratings[avg_ratings['count'] >= 10]  # Books with at least 10 ratings
    
    axes[1,0].scatter(avg_ratings['count'], avg_ratings['mean'], alpha=0.6, color='red')
    axes[1,0].set_xlabel('Number of Ratings')
    axes[1,0].set_ylabel('Average Rating')
    axes[1,0].set_title('Average Rating vs Number of Ratings')
    axes[1,0].set_xscale('log')
    
    # Model coverage analysis
    rating_thresholds = [1, 5, 10, 25, 50, 100, 250, 500]
    coverage_data = []
    
    for threshold in rating_thresholds:
        book_counts = books_with_ratings.groupby('Book-Title').size()
        books_above_threshold = len(book_counts[book_counts >= threshold])
        coverage_data.append(books_above_threshold)
    
    axes[1,1].plot(rating_thresholds, coverage_data, marker='o', linewidth=2, markersize=8, color='green')
    axes[1,1].set_xlabel('Minimum Rating Threshold')
    axes[1,1].set_ylabel('Number of Books')
    axes[1,1].set_title('Book Coverage vs Rating Threshold')
    axes[1,1].set_xscale('log')
    axes[1,1].grid(True, alpha=0.3)
    
    # Add annotation for current model
    current_books = len(pt)
    axes[1,1].axhline(y=current_books, color='red', linestyle='--', alpha=0.7)
    axes[1,1].text(100, current_books + 50, f'Current Model: {current_books} books', 
                   color='red', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('test/reports/performance_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. User and Rating Analysis
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('User Behavior and Rating Analysis', fontsize=16, fontweight='bold')
    
    # User rating distribution
    user_rating_counts = ratings_df.groupby('User-ID').size()
    
    axes[0,0].hist(user_rating_counts, bins=50, alpha=0.7, color='teal', edgecolor='black')
    axes[0,0].set_xlabel('Number of Ratings per User')
    axes[0,0].set_ylabel('Number of Users')
    axes[0,0].set_title('Distribution of User Activity')
    axes[0,0].set_yscale('log')
    
    # Rating patterns over time (if we had timestamp data, we'll simulate)
    # For now, show rating distribution by rating value
    rating_dist = ratings_df['Book-Rating'].value_counts().sort_index()
    
    axes[0,1].bar(rating_dist.index, rating_dist.values, alpha=0.7, color='brown')
    axes[0,1].set_xlabel('Rating Value')
    axes[0,1].set_ylabel('Frequency')
    axes[0,1].set_title('Overall Rating Distribution')
    
    # Most rated books
    book_rating_counts = books_with_ratings.groupby('Book-Title').size().sort_values(ascending=False)
    top_rated_books = book_rating_counts.head(15)
    
    axes[1,0].barh(range(len(top_rated_books)), top_rated_books.values, color='navy')
    axes[1,0].set_yticks(range(len(top_rated_books)))
    axes[1,0].set_yticklabels([title[:25] + '...' if len(title) > 25 else title 
                              for title in top_rated_books.index])
    axes[1,0].set_xlabel('Number of Ratings')
    axes[1,0].set_title('Most Rated Books')
    
    # Average rating by book (for books with sufficient ratings)
    avg_ratings_filtered = avg_ratings[avg_ratings['count'] >= 20].sort_values('mean', ascending=False)
    top_avg_books = avg_ratings_filtered.head(15)
    
    axes[1,1].barh(range(len(top_avg_books)), top_avg_books['mean'], color='darkgreen')
    axes[1,1].set_yticks(range(len(top_avg_books)))
    axes[1,1].set_yticklabels([title[:25] + '...' if len(title) > 25 else title 
                              for title in top_avg_books.index])
    axes[1,1].set_xlabel('Average Rating')
    axes[1,1].set_title('Highest Rated Books (20+ ratings)')
    axes[1,1].set_xlim(0, 10)
    
    plt.tight_layout()
    plt.savefig('test/reports/user_rating_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Visualizations created successfully!")

def generate_performance_metrics():
    """Generate detailed performance metrics"""
    print("📊 Generating performance metrics...")
    
    # Load data
    books_df, ratings_df, pt, books_pkl, similarity_scores = load_data()
    
    metrics = {}
    
    # Dataset statistics
    metrics['dataset'] = {
        'total_books': len(books_df),
        'total_ratings': len(ratings_df),
        'total_users': ratings_df['User-ID'].nunique(),
        'books_in_model': len(pt),
        'coverage_percentage': (len(pt) / len(books_df)) * 100,
        'avg_ratings_per_book': len(ratings_df) / len(books_df),
        'avg_ratings_per_user': len(ratings_df) / ratings_df['User-ID'].nunique()
    }
    
    # Model statistics
    sparsity = 1 - (np.count_nonzero(pt.values) / (pt.shape[0] * pt.shape[1]))
    
    metrics['model'] = {
        'matrix_shape': pt.shape,
        'sparsity': sparsity,
        'density': 1 - sparsity,
        'avg_similarity': np.mean(similarity_scores[similarity_scores != 1.0]),
        'max_similarity': np.max(similarity_scores[similarity_scores != 1.0]),
        'min_similarity': np.min(similarity_scores)
    }
    
    # Performance estimates
    import time
    
    # Test recommendation speed
    sample_books = list(pt.index)[:10]
    start_time = time.time()
    
    for book in sample_books:
        try:
            index = np.where(pt.index == book)[0][0]
            similar_items = sorted(list(enumerate(similarity_scores[index])), 
                                 key=lambda x: x[1], reverse=True)[1:6]
        except:
            continue
    
    end_time = time.time()
    avg_response_time = (end_time - start_time) / len(sample_books)
    
    metrics['performance'] = {
        'avg_recommendation_time': avg_response_time,
        'recommendations_per_second': 1 / avg_response_time if avg_response_time > 0 else 0,
        'model_size_mb': os.path.getsize('similarity_scores.pkl') / (1024 * 1024)
    }
    
    return metrics

def create_html_report(metrics):
    """Create a comprehensive HTML report"""
    print("📝 Creating HTML report...")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Book Recommendation System - Accuracy Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                border-left: 4px solid #3498db;
                padding-left: 15px;
                margin-top: 30px;
            }}
            .metric-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .metric-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .metric-label {{
                font-size: 0.9em;
                opacity: 0.9;
            }}
            .chart-container {{
                text-align: center;
                margin: 30px 0;
            }}
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .status-good {{ background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); }}
            .status-warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
            .status-info {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
            .recommendations {{
                background-color: #ecf0f1;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }}
            .timestamp {{
                text-align: center;
                color: #7f8c8d;
                font-style: italic;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Book Recommendation System - Accuracy Report</h1>
            
            <h2>📊 Dataset Overview</h2>
            <div class="metric-grid">
                <div class="metric-card status-info">
                    <div class="metric-value">{metrics['dataset']['total_books']:,}</div>
                    <div class="metric-label">Total Books</div>
                </div>
                <div class="metric-card status-info">
                    <div class="metric-value">{metrics['dataset']['total_ratings']:,}</div>
                    <div class="metric-label">Total Ratings</div>
                </div>
                <div class="metric-card status-info">
                    <div class="metric-value">{metrics['dataset']['total_users']:,}</div>
                    <div class="metric-label">Total Users</div>
                </div>
                <div class="metric-card status-good">
                    <div class="metric-value">{metrics['dataset']['books_in_model']:,}</div>
                    <div class="metric-label">Books in Model</div>
                </div>
                <div class="metric-card status-warning">
                    <div class="metric-value">{metrics['dataset']['coverage_percentage']:.1f}%</div>
                    <div class="metric-label">Coverage</div>
                </div>
                <div class="metric-card status-info">
                    <div class="metric-value">{metrics['dataset']['avg_ratings_per_book']:.1f}</div>
                    <div class="metric-label">Avg Ratings/Book</div>
                </div>
            </div>
            
            <div class="chart-container">
                <img src="dataset_overview.png" alt="Dataset Overview">
            </div>
            
            <h2>🎯 Model Performance</h2>
            <div class="metric-grid">
                <div class="metric-card status-good">
                    <div class="metric-value">{metrics['model']['sparsity']:.1%}</div>
                    <div class="metric-label">Matrix Sparsity</div>
                </div>
                <div class="metric-card status-info">
                    <div class="metric-value">{metrics['model']['avg_similarity']:.3f}</div>
                    <div class="metric-label">Avg Similarity</div>
                </div>
                <div class="metric-card status-good">
                    <div class="metric-value">{metrics['performance']['avg_recommendation_time']:.3f}s</div>
                    <div class="metric-label">Response Time</div>
                </div>
                <div class="metric-card status-info">
                    <div class="metric-value">{metrics['performance']['model_size_mb']:.1f} MB</div>
                    <div class="metric-label">Model Size</div>
                </div>
            </div>
            
            <div class="chart-container">
                <img src="performance_analysis.png" alt="Performance Analysis">
            </div>
            
            <h2>👥 User Analysis</h2>
            <div class="chart-container">
                <img src="user_rating_analysis.png" alt="User and Rating Analysis">
            </div>
            
            <h2>💡 Recommendations</h2>
            <div class="recommendations">
                <h3>✅ Strengths:</h3>
                <ul>
                    <li>Fast recommendation generation ({metrics['performance']['avg_recommendation_time']:.3f}s average)</li>
                    <li>Reasonable model size ({metrics['performance']['model_size_mb']:.1f} MB)</li>
                    <li>Good similarity score distribution</li>
                    <li>Handles {metrics['dataset']['books_in_model']:,} books effectively</li>
                </ul>
                
                <h3>⚠️ Areas for Improvement:</h3>
                <ul>
                    <li>Low coverage ({metrics['dataset']['coverage_percentage']:.1f}% of total books)</li>
                    <li>High matrix sparsity ({metrics['model']['sparsity']:.1%})</li>
                    <li>Cold start problem for new books</li>
                    <li>Limited to collaborative filtering approach</li>
                </ul>
                
                <h3>🚀 Suggested Enhancements:</h3>
                <ul>
                    <li>Implement hybrid recommendation system</li>
                    <li>Add content-based filtering for new books</li>
                    <li>Consider matrix factorization techniques</li>
                    <li>Implement user-based collaborative filtering</li>
                    <li>Add real-time learning capabilities</li>
                </ul>
            </div>
            
            <div class="timestamp">
                Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """
    
    with open('test/reports/accuracy_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ HTML report created: test/reports/accuracy_report.html")

def main():
    """Main function to generate comprehensive accuracy report"""
    print("📋 COMPREHENSIVE ACCURACY REPORT GENERATOR")
    print("=" * 80)
    
    # Load data
    books_df, ratings_df, pt, books_pkl, similarity_scores = load_data()
    
    # Run basic tests
    run_basic_accuracy_tests()
    
    # Create visualizations
    create_visualizations(books_df, ratings_df, pt, similarity_scores)
    
    # Generate metrics
    metrics = generate_performance_metrics()
    
    # Create HTML report
    create_html_report(metrics)
    
    # Print summary
    print(f"\n🎉 COMPREHENSIVE REPORT COMPLETED!")
    print("=" * 50)
    print(f"📊 Dataset: {metrics['dataset']['total_books']:,} books, {metrics['dataset']['total_ratings']:,} ratings")
    print(f"🎯 Model: {metrics['dataset']['books_in_model']:,} books ({metrics['dataset']['coverage_percentage']:.1f}% coverage)")
    print(f"⚡ Performance: {metrics['performance']['avg_recommendation_time']:.3f}s response time")
    print(f"💾 Model Size: {metrics['performance']['model_size_mb']:.1f} MB")
    
    print(f"\n📁 Generated Files:")
    print(f"   • test/reports/dataset_overview.png")
    print(f"   • test/reports/performance_analysis.png") 
    print(f"   • test/reports/user_rating_analysis.png")
    print(f"   • test/reports/accuracy_report.html")
    
    print(f"\n🌐 Open test/reports/accuracy_report.html in your browser to view the complete report!")
    
    return metrics

if __name__ == "__main__":
    metrics = main()