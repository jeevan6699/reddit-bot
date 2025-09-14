"""
Main test runner for bot-monitor.
Runs all test suites and provides comprehensive reporting.
"""

import os
import sys
import unittest
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import all test modules
from test_auth import run_auth_tests
from test_llm import run_llm_tests
from test_keywords import run_keyword_tests
from test_database import run_database_tests
from test_utils import run_utils_tests

def check_environment():
    """Check if all required environment variables are set."""
    print("🔍 Checking Environment Configuration...")
    print("=" * 40)
    
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'REDDIT_USERNAME',
        'REDDIT_PASSWORD',
        'REDDIT_USER_AGENT'
    ]
    
    optional_vars = [
        'GOOGLE_API_KEY',
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'MONITORED_SUBREDDITS',
        'FLASK_PORT'
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        value = os.getenv(var, '').strip('"')
        if not value or value in ['your_reddit_client_id', 'your_reddit_client_secret', 
                                  'your_reddit_username', 'your_reddit_password']:
            missing_required.append(var)
        else:
            print(f"✅ {var}: {'*' * min(len(value), 8)}...")
    
    for var in optional_vars:
        value = os.getenv(var, '').strip('"')
        if not value or value.startswith('your_'):
            missing_optional.append(var)
        else:
            print(f"✅ {var}: {'*' * min(len(value), 8)}...")
    
    if missing_required:
        print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
        print("⚠️  Some tests may fail due to missing authentication credentials")
    
    if missing_optional:
        print(f"\n⚠️  Missing optional variables: {', '.join(missing_optional)}")
        print("💡 Some features may not be available during testing")
    
    print("\n" + "=" * 40)
    return len(missing_required) == 0

def run_all_tests():
    """Run all test suites and provide comprehensive reporting."""
    start_time = time.time()
    
    print(f"🤖 Starting bot-monitor Test Suite")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check environment first
    env_ok = check_environment()
    
    # Test results tracking
    test_results = {}
    
    # Test suites to run
    test_suites = [
        ("Authentication", run_auth_tests),
        ("Keywords", run_keyword_tests),
        ("Database", run_database_tests),
        ("Utilities", run_utils_tests),
        ("LLM Integration", run_llm_tests)
    ]
    
    # Run each test suite
    for suite_name, test_function in test_suites:
        print(f"\n{'=' * 60}")
        print(f"🧪 Running {suite_name} Tests")
        print(f"{'=' * 60}")
        
        try:
            suite_start = time.time()
            success = test_function()
            suite_time = time.time() - suite_start
            
            test_results[suite_name] = {
                'success': success,
                'time': suite_time
            }
            
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status} - {suite_name} tests completed in {suite_time:.2f}s")
            
        except Exception as e:
            suite_time = time.time() - suite_start
            test_results[suite_name] = {
                'success': False,
                'time': suite_time,
                'error': str(e)
            }
            print(f"\n❌ FAILED - {suite_name} tests failed with error: {e}")
    
    # Generate final report
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("📊 TEST SUITE SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for result in test_results.values() if result['success'])
    total_count = len(test_results)
    
    for suite_name, result in test_results.items():
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        time_str = f"{result['time']:.2f}s"
        
        if 'error' in result:
            print(f"{status} - {suite_name:<20} ({time_str}) - Error: {result['error']}")
        else:
            print(f"{status} - {suite_name:<20} ({time_str})")
    
    print("-" * 60)
    print(f"📈 Results: {passed_count}/{total_count} test suites passed")
    print(f"⏱️  Total execution time: {total_time:.2f} seconds")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Your bot is ready for deployment.")
        
        if env_ok:
            print("✅ Environment configuration looks good")
            print("💡 You can start the bot with: python src/main.py")
        else:
            print("⚠️  Please check environment configuration before deployment")
    else:
        print(f"\n⚠️  {total_count - passed_count} test suite(s) failed")
        print("🔧 Please fix failing tests before deployment")
    
    print("\n" + "=" * 60)
    
    return passed_count == total_count

def run_specific_test(test_name):
    """Run a specific test suite."""
    test_map = {
        'auth': ('Authentication', run_auth_tests),
        'llm': ('LLM Integration', run_llm_tests),
        'keywords': ('Keywords', run_keyword_tests),
        'database': ('Database', run_database_tests),
        'utils': ('Utilities', run_utils_tests)
    }
    
    if test_name.lower() not in test_map:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_map.keys())}")
        return False
    
    suite_name, test_function = test_map[test_name.lower()]
    
    print(f"🧪 Running {suite_name} Tests Only")
    print("=" * 40)
    
    try:
        start_time = time.time()
        success = test_function()
        end_time = time.time()
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {suite_name} tests completed in {end_time - start_time:.2f}s")
        
        return success
        
    except Exception as e:
        print(f"\n❌ FAILED - {suite_name} tests failed with error: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        run_specific_test(test_name)
    else:
        # Run all tests
        run_all_tests()