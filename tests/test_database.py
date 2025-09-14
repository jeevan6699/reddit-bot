"""
Database testing for bot-monitor.
Tests database operations and logging functionality.
"""

import unittest
import os
import sys
import tempfile
import sqlite3

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestDatabase(unittest.TestCase):
    """Test database functionality."""
    
    def setUp(self):
        """Set up test database."""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        from database import DatabaseManager, InteractionType
        self.db = DatabaseManager(self.temp_db.name)
        self.InteractionType = InteractionType
    
    def tearDown(self):
        """Clean up test database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_database_initialization(self):
        """Test database tables are created correctly."""
        # Check that tables exist
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['interactions', 'processed_posts', 'daily_stats']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    def test_interaction_logging(self):
        """Test logging interactions to database."""
        from database import InteractionLog
        
        interaction = InteractionLog(
            interaction_type=self.InteractionType.POST_CHECKED,
            post_id="test123",
            subreddit="test",
            post_title="Test Post",
            matched_keywords=["test", "keyword"],
            success=True
        )
        
        interaction_id = self.db.log_interaction(interaction)
        self.assertGreater(interaction_id, 0)
        
        # Verify it was stored
        interactions = self.db.get_recent_interactions(limit=1)
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0].post_id, "test123")
        self.assertEqual(interactions[0].subreddit, "test")
    
    def test_post_processing_tracking(self):
        """Test tracking processed posts."""
        post_id = "test_post_123"
        subreddit = "test"
        title = "Test Post Title"
        author = "test_author"
        created_utc = 1234567890.0
        
        # Mark post as processed
        self.db.mark_post_processed(post_id, subreddit, title, author, created_utc)
        
        # Check if post is marked as processed
        self.assertTrue(self.db.is_post_processed(post_id))
        self.assertFalse(self.db.has_replied_to_post(post_id))
        
        # Mark as replied
        self.db.mark_post_processed(post_id, subreddit, title, author, created_utc, replied=True)
        self.assertTrue(self.db.has_replied_to_post(post_id))
    
    def test_daily_stats_tracking(self):
        """Test daily statistics tracking."""
        from database import InteractionLog
        
        # Log different types of interactions
        interactions = [
            InteractionLog(interaction_type=self.InteractionType.POST_CHECKED),
            InteractionLog(interaction_type=self.InteractionType.KEYWORD_MATCHED),
            InteractionLog(interaction_type=self.InteractionType.RESPONSE_GENERATED),
            InteractionLog(interaction_type=self.InteractionType.REPLY_POSTED),
        ]
        
        for interaction in interactions:
            self.db.log_interaction(interaction)
        
        # Check daily stats
        stats = self.db.get_total_stats()
        self.assertEqual(stats['posts_checked'], 1)
        self.assertEqual(stats['keywords_matched'], 1)
        self.assertEqual(stats['responses_generated'], 1)
        self.assertEqual(stats['successful_replies'], 1)
    
    def test_recent_interactions_filtering(self):
        """Test filtering recent interactions by type."""
        from database import InteractionLog
        
        # Log different types
        self.db.log_interaction(InteractionLog(interaction_type=self.InteractionType.POST_CHECKED))
        self.db.log_interaction(InteractionLog(interaction_type=self.InteractionType.KEYWORD_MATCHED))
        self.db.log_interaction(InteractionLog(interaction_type=self.InteractionType.ERROR))
        
        # Get all interactions
        all_interactions = self.db.get_recent_interactions()
        self.assertEqual(len(all_interactions), 3)
        
        # Get only errors
        error_interactions = self.db.get_recent_interactions(interaction_type=self.InteractionType.ERROR)
        self.assertEqual(len(error_interactions), 1)
        self.assertEqual(error_interactions[0].interaction_type, self.InteractionType.ERROR)
    
    def test_convenience_functions(self):
        """Test convenience logging functions."""
        from database import (
            log_post_checked, log_keyword_match, log_response_generated,
            log_reply_posted, log_reply_failed, log_error
        )
        
        # Test each convenience function
        log_post_checked(self.db, "post1", "test", "Test Title")
        log_keyword_match(self.db, "post2", "test", "Test Title", ["keyword1", "keyword2"])
        log_response_generated(self.db, "post3", "test", "Generated response", "gemini")
        log_reply_posted(self.db, "post4", "test", "Posted response", "gemini")
        log_reply_failed(self.db, "post5", "test", "Error message")
        log_error(self.db, "Test error message")
        
        # Verify all were logged
        interactions = self.db.get_recent_interactions()
        self.assertEqual(len(interactions), 6)
        
        # Check types
        types = [i.interaction_type for i in interactions]
        self.assertIn(self.InteractionType.POST_CHECKED, types)
        self.assertIn(self.InteractionType.KEYWORD_MATCHED, types)
        self.assertIn(self.InteractionType.RESPONSE_GENERATED, types)
        self.assertIn(self.InteractionType.REPLY_POSTED, types)
        self.assertIn(self.InteractionType.REPLY_FAILED, types)
        self.assertIn(self.InteractionType.ERROR, types)
    
    def test_database_indexes(self):
        """Test that database indexes are created for performance."""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Check for expected indexes
        expected_indexes = [
            'idx_interactions_timestamp',
            'idx_interactions_type',
            'idx_interactions_post_id',
            'idx_processed_posts_subreddit'
        ]
        
        for index in expected_indexes:
            self.assertIn(index, indexes)
        
        conn.close()

def run_database_tests():
    """Run database tests separately."""
    print("🗄️  Testing Database Operations...")
    print("=" * 40)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDatabase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_database_tests()