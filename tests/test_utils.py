"""
Utility functions testing for bot-monitor.
Tests various utility and helper functions.
"""

import unittest
import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def test_truncate_text(self):
        """Test text truncation functionality."""
        from utils import truncate_text
        
        # Test short text (no truncation needed)
        short_text = "This is a short text"
        self.assertEqual(truncate_text(short_text, 100), short_text)
        
        # Test long text (truncation needed)
        long_text = "This is a very long text that needs to be truncated because it exceeds the maximum length limit that we have set for this particular test case"
        truncated = truncate_text(long_text, 50)
        self.assertLessEqual(len(truncated), 53)  # 50 + "..."
        self.assertTrue(truncated.endswith("..."))
        
        # Test truncation at word boundary
        test_text = "This is a test message that should be truncated properly"
        truncated = truncate_text(test_text, 20)
        self.assertIn("...", truncated)
        # Should not cut in middle of word if possible
        self.assertNotIn("mes...", truncated)
    
    def test_clean_reddit_text(self):
        """Test Reddit text cleaning functionality."""
        from utils import clean_reddit_text
        
        # Test markdown removal
        markdown_text = "This is **bold** and *italic* text with ~~strikethrough~~"
        cleaned = clean_reddit_text(markdown_text)
        self.assertEqual(cleaned, "This is bold and italic text with strikethrough")
        
        # Test link removal
        link_text = "Check out [this link](https://example.com) for more info"
        cleaned = clean_reddit_text(link_text)
        self.assertEqual(cleaned, "Check out this link for more info")
        
        # Test code block removal
        code_text = "Here's some code: ```python\nprint('hello')\n``` and `inline code`"
        cleaned = clean_reddit_text(code_text)
        self.assertNotIn("```", cleaned)
        self.assertNotIn("print('hello')", cleaned)
        self.assertIn("inline code", cleaned)
        
        # Test newline and space cleanup
        messy_text = "This\n\nhas\n\n\nmany\nlines   and    spaces"
        cleaned = clean_reddit_text(messy_text)
        self.assertNotIn("\n", cleaned)
        self.assertNotIn("  ", cleaned)
    
    def test_is_spam_like(self):
        """Test spam detection functionality."""
        from utils import is_spam_like
        
        # Test normal text (not spam)
        normal_text = "This is a normal comment about technology and programming"
        self.assertFalse(is_spam_like(normal_text))
        
        # Test excessive caps (spam-like)
        caps_text = "THIS IS ALL CAPS AND LOOKS LIKE SPAM!!!"
        self.assertTrue(is_spam_like(caps_text))
        
        # Test excessive punctuation (spam-like)
        punct_text = "Amazing deal!!!! Click here now!!!!!!"
        self.assertTrue(is_spam_like(punct_text))
        
        # Test spam keywords
        spam_text = "Click here for free money and get rich quick"
        self.assertTrue(is_spam_like(spam_text))
        
        # Test empty text
        self.assertFalse(is_spam_like(""))
        self.assertFalse(is_spam_like(None))
    
    def test_validate_environment(self):
        """Test environment variable validation."""
        from utils import validate_environment
        
        # This test depends on current environment
        missing_vars = validate_environment()
        
        # Should return a list (empty if all vars present)
        self.assertIsInstance(missing_vars, list)
        
        # If Google API key is set, should not be in missing vars
        google_key = os.getenv('GOOGLE_API_KEY', '').strip('"')
        if google_key and google_key != 'your_google_api_key_here':
            llm_missing = [var for var in missing_vars if 'LLM API key' in var]
            self.assertEqual(len(llm_missing), 0)
    
    def test_get_safe_filename(self):
        """Test safe filename generation."""
        from utils import get_safe_filename
        
        # Test filename with invalid characters
        unsafe_filename = 'file<with>invalid:chars"and/slashes'
        safe_filename = get_safe_filename(unsafe_filename)
        
        # Should not contain invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            self.assertNotIn(char, safe_filename)
        
        # Test normal filename (should remain unchanged)
        normal_filename = 'normal_filename.txt'
        self.assertEqual(get_safe_filename(normal_filename), normal_filename)
        
        # Test empty filename
        self.assertEqual(get_safe_filename(''), '')
    
    def test_calculate_response_quality_score(self):
        """Test response quality scoring."""
        from utils import calculate_response_quality_score
        
        # Test good quality response
        good_response = "This is a thoughtful response about Indian technology trends that provides useful information and shows understanding of the topic."
        keywords = ["indian", "technology", "trends"]
        post_title = "What are the latest technology trends in India?"
        
        score = calculate_response_quality_score(good_response, post_title, keywords)
        self.assertGreater(score, 2.0)  # Should get a decent score
        
        # Test poor quality response (too short)
        poor_response = "Yes."
        score = calculate_response_quality_score(poor_response, post_title, keywords)
        self.assertLess(score, 1.0)
        
        # Test spam-like response
        spam_response = "CLICK HERE FOR AMAZING DEALS!!!"
        score = calculate_response_quality_score(spam_response, post_title, keywords)
        self.assertLess(score, 0.5)
        
        # Test empty response
        score = calculate_response_quality_score("", post_title, keywords)
        self.assertEqual(score, 0.0)
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        from utils import format_timestamp
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Test recent timestamp (minutes ago)
        recent = now - timedelta(minutes=30)
        formatted = format_timestamp(recent)
        self.assertIn("minutes ago", formatted)
        
        # Test older timestamp (hours ago)
        hours_ago = now - timedelta(hours=5)
        formatted = format_timestamp(hours_ago)
        self.assertIn("hours ago", formatted)
        
        # Test very recent (just now)
        very_recent = now - timedelta(seconds=10)
        formatted = format_timestamp(very_recent)
        self.assertEqual(formatted, "Just now")
        
        # Test days ago
        days_ago = now - timedelta(days=3)
        formatted = format_timestamp(days_ago)
        self.assertIn("days ago", formatted)
    
    def test_backup_database(self):
        """Test database backup functionality."""
        from utils import backup_database
        
        # Create a temporary database file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.write(b"test database content")
            temp_db_path = temp_db.name
        
        try:
            # Create temporary backup directory
            with tempfile.TemporaryDirectory() as backup_dir:
                backup_path = backup_database(temp_db_path, backup_dir)
                
                # Should return a path if successful
                if backup_path:
                    self.assertTrue(os.path.exists(backup_path))
                    self.assertTrue(backup_path.endswith('.db'))
                    
                    # Backup should contain the same data
                    with open(backup_path, 'rb') as backup_file:
                        backup_content = backup_file.read()
                    self.assertEqual(backup_content, b"test database content")
        
        finally:
            # Clean up
            try:
                os.unlink(temp_db_path)
            except:
                pass
    
    def test_load_config(self):
        """Test configuration loading functionality."""
        from utils import load_config, load_keywords_config
        
        # Test loading with non-existent file (should return empty dict)
        config = load_config("non_existent_file.yaml")
        self.assertEqual(config, {})
        
        keywords_config = load_keywords_config("non_existent_keywords.yaml")
        self.assertEqual(keywords_config, {})
    
    def test_setup_logging(self):
        """Test logging setup functionality."""
        from utils import setup_logging
        import logging
        
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            # Should not raise an exception
            setup_logging("INFO", log_file)
            
            # Log file directory should be created
            self.assertTrue(os.path.exists(os.path.dirname(log_file)))

def run_utils_tests():
    """Run utility function tests separately."""
    print("🔧 Testing Utility Functions...")
    print("=" * 40)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_utils_tests()