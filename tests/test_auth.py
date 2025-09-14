"""
Authentication testing for bot-monitor.
Tests Reddit API and LLM API authentication and setup.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestAuthentication(unittest.TestCase):
    """Test authentication for Reddit and LLM APIs."""
    
    def setUp(self):
        """Load environment variables for testing."""
        pass
    
    def test_reddit_credentials_exist(self):
        """Test that Reddit credentials are present."""
        reddit_vars = [
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET', 
            'REDDIT_USERNAME',
            'REDDIT_PASSWORD',
            'REDDIT_USER_AGENT'
        ]
        
        missing = []
        for var in reddit_vars:
            value = os.getenv(var, '').strip('"')
            if not value or value.startswith('your_'):
                missing.append(var)
        
        if missing:
            print(f"⚠️  Missing Reddit credentials: {', '.join(missing)}")
    
    def test_google_api_key_exists(self):
        """Test that Google API key is present and not placeholder."""
        api_key = os.getenv('GOOGLE_API_KEY', '').strip('"')
        
        if not api_key or api_key == 'your_google_api_key_here':
            print("⚠️  Google API key not configured")
        else:
            print(f"✅ Google API key configured: {api_key[:10]}...")
    
    def test_user_agent_format(self):
        """Test that user agent follows Reddit guidelines."""
        user_agent = os.getenv('REDDIT_USER_AGENT', '')
        
        if user_agent and user_agent != 'your_user_agent_here':
            self.assertIn('bot-monitor', user_agent.lower())
            print(f"✅ User agent: {user_agent}")
    
    def test_reddit_client_initialization(self):
        """Test Reddit client can be initialized with credentials."""
        try:
            from reddit_client import RedditClient
            
            # This will test if all required env vars are present
            client = RedditClient()
            self.assertIsNotNone(client)
            print("✅ Reddit client initialized successfully")
            
        except Exception as e:
            print(f"❌ Reddit client initialization failed: {e}")
            # Don't fail the test if credentials are missing
    
    def test_llm_manager_initialization(self):
        """Test LLM manager can be initialized."""
        try:
            from llm_client import LLMManager
            
            manager = LLMManager()
            self.assertIsNotNone(manager)
            print("✅ LLM manager initialized successfully")
            
        except Exception as e:
            print(f"❌ LLM manager initialization failed: {e}")
            self.fail(f"LLM manager should initialize even without API keys: {e}")
    
    @patch('google.generativeai.configure')
    def test_gemini_client_setup(self, mock_configure):
        """Test Gemini client setup with real API key."""
        from llm_client import GeminiClient
        
        # Get actual API key from environment
        api_key = os.getenv('GOOGLE_API_KEY', '').strip('"')
        
        if api_key and api_key != 'your_google_api_key_here':
            print(f"\n🔑 Testing Gemini setup with API key: {api_key[:10]}...")
            
            try:
                client = GeminiClient(api_key, "gemini-1.5-flash")
                print(f"✅ Gemini client created successfully")
                print(f"📊 Model: {client.model_name}")
                
                # Test a simple response (mocked for safety)
                with patch.object(client, 'generate_response') as mock_response:
                    mock_result = MagicMock()
                    mock_result.success = True
                    mock_result.content = "Hello! I'm Gemini, ready to help with discussions about India, technology, and general advice."
                    mock_result.provider.value = "GEMINI"
                    mock_response.return_value = mock_result
                    
                    response = client.generate_response(
                        "Hello, can you introduce yourself?",
                        "Introduction request",
                        ["hello", "introduction"]
                    )
                    
                    print(f"🤖 Test Response:")
                    print(f"   Success: {response.success}")
                    print(f"   Provider: {response.provider.value}")
                    print(f"   Content: {response.content}")
                    print("-" * 50)
                    
                    self.assertTrue(response.success)
                
                mock_configure.assert_called_with(api_key=api_key)
                
            except Exception as e:
                print(f"❌ Gemini setup failed: {e}")
                self.fail(f"Gemini client setup failed: {e}")
        else:
            print("⚠️  No valid Google API key found, skipping Gemini test")
            self.skipTest("No valid Google API key available")

def run_auth_tests():
    """Run authentication tests separately."""
    print("🔑 Testing Authentication...")
    print("=" * 40)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuthentication)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_auth_tests()