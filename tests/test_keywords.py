"""
Keyword matching testing for bot-monitor.
Tests the keyword detection and matching system.
"""

import unittest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestKeywordMatcher(unittest.TestCase):
    """Test keyword matching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        from keyword_matcher import KeywordMatcher, KeywordRule, MatchType
        
        self.matcher = KeywordMatcher()
        self.MatchType = MatchType
        self.KeywordRule = KeywordRule
    
    def test_keyword_rule_creation(self):
        """Test KeywordRule creation."""
        rule = self.KeywordRule(
            keywords=["india", "delhi"],
            match_type=self.MatchType.PARTIAL,
            match_location="both",
            priority=3
        )
        
        self.assertEqual(rule.keywords, ["india", "delhi"])
        self.assertEqual(rule.match_type, self.MatchType.PARTIAL)
        self.assertEqual(rule.match_location, "both")
        self.assertEqual(rule.priority, 3)
    
    def test_add_rule(self):
        """Test adding keyword rules."""
        rule = self.KeywordRule(
            keywords=["test"],
            match_type=self.MatchType.EXACT,
            match_location="title",
            priority=1
        )
        
        initial_count = len(self.matcher.rules)
        self.matcher.add_rule(rule)
        
        self.assertEqual(len(self.matcher.rules), initial_count + 1)
        self.assertIn(rule, self.matcher.rules)
    
    def test_blacklist_keywords(self):
        """Test blacklist functionality."""
        blacklist = ["spam", "scam", "illegal"]
        self.matcher.add_blacklist_keywords(blacklist)
        
        # Test that blacklisted content is detected
        self.assertTrue(self.matcher.check_blacklist("This is spam content", ""))
        self.assertTrue(self.matcher.check_blacklist("", "This is a scam post"))
        self.assertFalse(self.matcher.check_blacklist("This is clean content", ""))
    
    def test_exact_matching(self):
        """Test exact keyword matching."""
        keywords = ["india", "delhi"]
        text = "I love India and Delhi is amazing"
        
        matches = self.matcher._match_exact(keywords, text)
        
        self.assertIn("india", matches)
        self.assertIn("delhi", matches)
    
    def test_partial_matching(self):
        """Test partial keyword matching with word boundaries."""
        keywords = ["indian", "food"]
        text = "I love Indian food and cuisine"
        
        matches = self.matcher._match_partial(keywords, text)
        
        self.assertIn("indian", matches)
        self.assertIn("food", matches)
    
    def test_regex_matching(self):
        """Test regex keyword matching."""
        keywords = [r"\bIndia\b", r"Delhi|Mumbai"]
        text = "India is great and Delhi is the capital"
        
        matches = self.matcher._match_regex(keywords, text)
        
        self.assertEqual(len(matches), 2)
    
    def test_default_rules_loading(self):
        """Test loading of default keyword rules."""
        initial_count = len(self.matcher.rules)
        self.matcher.load_default_rules()
        
        # Should have added rules
        self.assertGreater(len(self.matcher.rules), initial_count)
        
        # Check for expected rule types
        rule_types = [rule.response_template for rule in self.matcher.rules if rule.response_template]
        self.assertIn("india_specific", rule_types)
        self.assertIn("helpful_advice", rule_types)
        self.assertIn("tech_discussion", rule_types)
    
    def test_post_matching(self):
        """Test matching against a sample post."""
        self.matcher.load_default_rules()
        
        # Sample posts to test
        test_posts = [
            {
                "title": "Best places to visit in India",
                "body": "I'm planning a trip to India and looking for suggestions about Delhi and Mumbai",
                "expected_template": "india_specific"
            },
            {
                "title": "Python vs Java for beginners",
                "body": "I'm new to programming. Should I start with Python or Java for my career?",
                "expected_template": "tech_discussion"
            },
            {
                "title": "How to deal with work stress?",
                "body": "Feeling overwhelmed at my new job. Any advice for managing workplace stress?",
                "expected_template": "helpful_advice"
            }
        ]
        
        print("\n🎯 Testing Keyword Matching on Sample Posts:")
        
        for i, post in enumerate(test_posts, 1):
            print(f"\n--- Post {i} ---")
            print(f"Title: {post['title']}")
            print(f"Body: {post['body'][:80]}...")
            
            matches = self.matcher.match_post(post['title'], post['body'])
            
            print(f"Total Matches: {len(matches)}")
            
            if matches:
                for match in matches[:3]:  # Show top 3 matches
                    print(f"  • Keyword: '{match.keyword}' (Priority: {match.rule.priority}, Template: {match.rule.response_template})")
                
                # Check for expected template
                templates = [m.rule.response_template for m in matches if m.rule.response_template]
                print(f"Response Templates: {list(set(templates))}")
                
                if post['expected_template'] in templates:
                    print(f"✅ Found expected template: {post['expected_template']}")
                else:
                    print(f"⚠️  Expected template '{post['expected_template']}' not found")
            
            self.assertGreater(len(matches), 0, f"No matches found for post {i}")
        
        print("\n" + "-" * 60)
        
        # Original test logic
        title = "Best places to visit in India"
        body = "I'm planning a trip to India and looking for suggestions about Delhi and Mumbai"
        
        matches = self.matcher.match_post(title, body)
        
        self.assertGreater(len(matches), 0)
        
        # Should have high-priority India match
        india_matches = [m for m in matches if m.rule.response_template == "india_specific"]
        self.assertGreater(len(india_matches), 0)
        self.assertEqual(india_matches[0].priority, 3)
    
    def test_should_respond_logic(self):
        """Test should_respond decision logic."""
        from keyword_matcher import MatchResult
        
        # Create mock match results
        high_priority_match = MatchResult(
            matched=True,
            matched_keywords=["india"],
            match_locations=["title"],
            priority=3,
            rule=self.KeywordRule(["india"], self.MatchType.PARTIAL, "title", 3)
        )
        
        low_priority_match = MatchResult(
            matched=True,
            matched_keywords=["general"],
            match_locations=["body"],
            priority=1,
            rule=self.KeywordRule(["general"], self.MatchType.PARTIAL, "body", 1)
        )
        
        # Test with high priority - should respond
        should_respond, best_match = self.matcher.should_respond([high_priority_match], min_priority=2)
        self.assertTrue(should_respond)
        self.assertEqual(best_match, high_priority_match)
        
        # Test with low priority - should not respond
        should_respond, best_match = self.matcher.should_respond([low_priority_match], min_priority=2)
        self.assertFalse(should_respond)
        self.assertIsNone(best_match)
    
    def test_match_result_sorting(self):
        """Test that match results are sorted by priority."""
        self.matcher.load_default_rules()
        
        # Create a post that should match multiple rules
        title = "Need advice about programming in India"
        body = "I'm looking for career advice about software development in Indian tech companies"
        
        matches = self.matcher.match_post(title, body)
        
        # Should have multiple matches
        self.assertGreater(len(matches), 1)
        
        # Should be sorted by priority (highest first)
        for i in range(len(matches) - 1):
            self.assertGreaterEqual(matches[i].priority, matches[i + 1].priority)
    
    def test_case_insensitive_matching(self):
        """Test that matching is case insensitive."""
        keywords = ["India", "Delhi"]
        text_lower = "i love india and delhi"
        text_upper = "I LOVE INDIA AND DELHI"
        text_mixed = "I love India and DELHI"
        
        matches_lower = self.matcher._match_partial(keywords, text_lower)
        matches_upper = self.matcher._match_partial(keywords, text_upper)
        matches_mixed = self.matcher._match_partial(keywords, text_mixed)
        
        self.assertEqual(len(matches_lower), 2)
        self.assertEqual(len(matches_upper), 2)
        self.assertEqual(len(matches_mixed), 2)

def run_keyword_tests():
    """Run keyword matcher tests separately."""
    print("🔍 Testing Keyword Matching...")
    print("=" * 40)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKeywordMatcher)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_keyword_tests()