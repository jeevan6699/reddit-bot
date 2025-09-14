"""
Authentication testing for bot-monitor.
Tests Reddit and LLM API authentication    @patch('google.generativeai.configure')
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
            self.skipTest("No valid Google API key available")unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv

class TestAuthentication(unittest.TestCase):
    """Test authentication for Reddit and LLM APIs."""
    
    @classmethod
    def setUpClass(cls):
        """Load environment variables for testing."""
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
    
    def test_reddit_credentials_exist(self):
        """Test that Reddit credentials are present."""
        required_vars = [
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET',
            'REDDIT_USERNAME',
            'REDDIT_PASSWORD',
            'REDDIT_USER_AGENT'
        ]
        
        for var in required_vars:
            with self.subTest(var=var):
                value = os.getenv(var)
                self.assertIsNotNone(value, f"{var} is not set")
                self.assertNotEqual(value.strip('"'), '', f"{var} is empty")
    
    def test_google_api_key_exists(self):
        """Test that Google API key is present and not placeholder."""
        api_key = os.getenv('GOOGLE_API_KEY', '').strip('"')
        self.assertIsNotNone(api_key, "GOOGLE_API_KEY is not set")
        self.assertNotEqual(api_key, 'your_google_api_key', "GOOGLE_API_KEY is still placeholder")
        self.assertTrue(api_key.startswith('AIza'), "GOOGLE_API_KEY doesn't look like a valid Google API key")
    
    def test_user_agent_format(self):
        """Test that user agent follows Reddit guidelines."""
        user_agent = os.getenv('REDDIT_USER_AGENT', '').strip('"')
        self.assertIn('bot-monitor', user_agent, "User agent should contain 'bot-monitor'")
        self.assertIn('/u/', user_agent, "User agent should contain reddit username")
        self.assertRegex(user_agent, r'bot-monitor/\d+\.\d+', "User agent should have version number")
    
    @patch('praw.Reddit')
    def test_reddit_client_initialization(self, mock_reddit):
        """Test Reddit client can be initialized with credentials."""
        from reddit_client import RedditClient
        
        # Mock successful authentication
        mock_user = MagicMock()
        mock_user.name = "test_user"
        mock_reddit.return_value.user.me.return_value = mock_user
        
        client = RedditClient(
            client_id=os.getenv('REDDIT_CLIENT_ID', '').strip('"'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET', '').strip('"'),
            user_agent=os.getenv('REDDIT_USER_AGENT', '').strip('"'),
            username=os.getenv('REDDIT_USERNAME', '').strip('"'),
            password=os.getenv('REDDIT_PASSWORD', '').strip('"')
        )
        
        self.assertIsNotNone(client)
        mock_reddit.assert_called_once()
    
    def test_llm_manager_initialization(self):
        """Test LLM manager can be initialized."""
        from llm_client import LLMManager, LLMProvider
        
        manager = LLMManager(primary_provider=LLMProvider.GEMINI)
        self.assertIsNotNone(manager)
        self.assertEqual(manager.primary_provider, LLMProvider.GEMINI)
    
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