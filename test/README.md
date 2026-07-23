# Book Recommendation System - Test Suite

This test suite provides comprehensive testing for your book recommendation system, including model validation, Flask application testing, and performance benchmarks.

## 📁 Test Files

- **`test_model.py`** - Tests the machine learning model and data integrity
- **`test_flask_app.py`** - Tests the Flask web application endpoints
- **`run_all_tests.py`** - Master test runner that executes all tests
- **`README.md`** - This documentation file

## 🚀 How to Run Tests

### Option 1: Run All Tests (Recommended)
```bash
cd test
python run_all_tests.py
```

### Option 2: Run Individual Test Suites
```bash
# Test the ML model only
python test_model.py

# Test the Flask app only  
python test_flask_app.py
```

## 🧪 What Gets Tested

### Model Tests (`test_model.py`)
- ✅ Model file existence and loading
- ✅ Data structure validation
- ✅ Recommendation algorithm functionality
- ✅ Data consistency checks
- ✅ Sample recommendation generation

### Flask App Tests (`test_flask_app.py`)
- ✅ Home page loading and content
- ✅ Recommendation page functionality
- ✅ Form submission handling
- ✅ Error handling for invalid inputs
- ✅ Navigation and styling

### Performance Tests
- ✅ Model loading speed
- ✅ Recommendation generation speed
- ✅ Memory usage estimation

## 📊 Understanding Test Results

The test runner will show:
- **✅ PASSED** - Test completed successfully
- **❌ FAILED** - Test failed, needs attention
- **⚠️ WARNING** - Test passed but with warnings

### Sample Output
```
📚 BOOK RECOMMENDATION SYSTEM - COMPREHENSIVE TEST SUITE
================================================================================
🕐 Test started at: 2024-01-15 14:30:25
📁 Working directory: /path/to/your/project/test
================================================================================

==================== PREREQUISITES CHECK ====================
✅ ../popular.pkl
✅ ../pt.pkl
✅ ../books.pkl
✅ ../similarity_scores.pkl
✅ ../app2.py

🎉 All prerequisite files found!

==================== MODEL TESTS ====================
🧪 Starting Book Recommendation Model Tests...

✅ All model files loaded successfully!
✅ All required model files exist
✅ Popular books dataframe has 50 books with correct structure
✅ Pivot table has shape: (742, 888) (books x users)
✅ Similarity scores matrix has correct shape: (742, 742)
✅ Recommendation algorithm works for book: 'The Lovely Bones: A Novel'
✅ Data consistency check passed. Missing books: 15.23%

📊 Test Summary:
   Tests run: 6
   Failures: 0
   Errors: 0
🎉 All tests passed! Your model is working correctly.
```

## 🔧 Troubleshooting

### Common Issues

1. **"FileNotFoundError: No such file or directory"**
   - Make sure you're running tests from the `test/` directory
   - Ensure all `.pkl` files exist in the parent directory

2. **"ModuleNotFoundError: No module named 'app2'"**
   - Ensure `app2.py` exists in the parent directory
   - Check that you're running from the correct directory

3. **"Model files missing"**
   - Run your Jupyter notebook to generate the pickle files
   - Make sure all pickle files are in the main project directory

### Prerequisites
- Python 3.6+
- Flask
- NumPy
- Pandas
- All model pickle files (generated from Jupyter notebook)

## 📈 Performance Benchmarks

Typical performance on a modern machine:
- Model loading: < 1 second
- Single recommendation: < 0.1 seconds
- Memory usage: 50-200 MB (depending on dataset size)

## 🎯 Next Steps

After running tests:
1. Fix any failing tests
2. Run the Flask app: `python app2.py`
3. Test manually in browser at `http://127.0.0.1:8080/`
4. Deploy your application

## 📝 Adding More Tests

To add custom tests:
1. Create new test methods in existing files
2. Follow the naming convention: `test_your_feature_name`
3. Use assertions to validate expected behavior
4. Add print statements for user-friendly output

Happy testing! 🚀