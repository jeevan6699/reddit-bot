"""
Comprehensive test suite for bot-monitor Reddit bot.

This module contains all tests for the bot components.
"""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import test modules
from test_auth import TestAuthentication
from test_llm import TestLLMIntegration
from test_keywords import TestKeywordMatcher
from test_database import TestDatabase
from test_utils import TestUtils

def run_all_tests():
    """Run all test suites."""
    
    print("🚀 Running bot-monitor Test Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTest(loader.loadTestsFromTestCase(TestAuthentication))
    suite.addTest(loader.loadTestsFromTestCase(TestLLMIntegration))
    suite.addTest(loader.loadTestsFromTestCase(TestKeywordMatcher))
    suite.addTest(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTest(loader.loadTestsFromTestCase(TestUtils))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🏁 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}")
    
    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}")
    
    if not result.failures and not result.errors:
        print("\n✅ All tests passed!")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)