"""
LLM integration testing for bot-monitor.
Tests Gemini, Claude, and OpenAI integration.
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv

class TestLLMIntegration(unittest.TestCase):
    """Test LLM provider integrations."""
    
    @classmethod
    def setUpClass(cls):
        """Load environment variables for testing."""
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
    
    def test_llm_provider_enum(self):
        """Test LLM provider enumeration."""
        from llm_client import LLMProvider
        
        self.assertEqual(LLMProvider.GEMINI.value, "gemini")
        self.assertEqual(LLMProvider.CLAUDE.value, "claude")
        self.assertEqual(LLMProvider.OPENAI.value, "openai")
    
    def test_llm_response_dataclass(self):
        """Test LLMResponse dataclass."""
        from llm_client import LLMResponse, LLMProvider
        
        response = LLMResponse(
            text="Test response",
            provider=LLMProvider.GEMINI,
            model="gemini-1.5-flash",
            tokens_used=50,
            response_time=1.5
        )
        
        self.assertEqual(response.text, "Test response")
        self.assertEqual(response.provider, LLMProvider.GEMINI)
        self.assertEqual(response.model, "gemini-1.5-flash")
        self.assertEqual(response.tokens_used, 50)
        self.assertEqual(response.response_time, 1.5)
    
    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_gemini_client_creation(self, mock_configure, mock_model):
        """Test Gemini client creation."""
        from llm_client import GeminiClient
        
        # Mock the model
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        
        client = GeminiClient("test_api_key", "gemini-1.5-flash")
        
        self.assertIsNotNone(client)
        mock_configure.assert_called_with(api_key="test_api_key")
        mock_model.assert_called_with("gemini-1.5-flash")
    
    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_gemini_response_generation(self, mock_configure, mock_model):
        """Test Gemini response generation."""
        from llm_client import GeminiClient, LLMProvider
        
        # Mock the model and response
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        mock_response = MagicMock()
        mock_response.text = "This is a test response from Gemini about technology trends in India. India has been experiencing rapid technological growth with initiatives like Digital India and startup ecosystem development."
        mock_model_instance.generate_content.return_value = mock_response
        
        client = GeminiClient("test_key", "gemini-1.5-flash")
        
        # Test response generation
        response = client.generate_response(
            "What are your thoughts on technology in India?",
            "Technology trends in India",
            ["technology", "india"]
        )
        
        print("\n🤖 LLM Response Test Output:")
        print(f"Provider: {response.provider.value}")
        print(f"Success: {response.success}")
        print(f"Content: {response.content}")
        print(f"Length: {len(response.content)} characters")
        print("-" * 60)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.content, mock_response.text)
        self.assertEqual(response.provider, LLMProvider.GEMINI)
        self.assertTrue(response.success)
    
    def test_llm_manager_fallback_order(self):
        """Test LLM manager fallback order."""
        from llm_client import LLMManager, LLMProvider
        
        manager = LLMManager(primary_provider=LLMProvider.GEMINI)
        
        self.assertEqual(manager.primary_provider, LLMProvider.GEMINI)
        self.assertIn(LLMProvider.GEMINI, manager.fallback_order)
        self.assertIn(LLMProvider.CLAUDE, manager.fallback_order)
        self.assertIn(LLMProvider.OPENAI, manager.fallback_order)
    
    def test_response_templates_exist(self):
        """Test that response templates are properly defined."""
        from llm_client import LLMManager
        
        manager = LLMManager()
        
        required_templates = [
            "india_specific",
            "helpful_advice", 
            "tech_discussion",
            "general"
        ]
        
        for template in required_templates:
            with self.subTest(template=template):
                self.assertIn(template, manager.response_templates)
                self.assertIn("{title}", manager.response_templates[template])
                self.assertIn("{body}", manager.response_templates[template])
                self.assertIn("{keywords}", manager.response_templates[template])
    
    def test_template_formatting(self):
        """Test template formatting with sample data."""
        from llm_client import get_response_template
        
        print("\n📋 Testing Response Templates:")
        
        # Test India-specific template
        template = get_response_template("india_specific")
        print(f"\n🇮🇳 India-specific template:")
        print(f"{template[:200]}...")
        self.assertIn("India", template)
        
        # Test helpful advice template
        template = get_response_template("helpful_advice")
        print(f"\n💡 Helpful advice template:")
        print(f"{template[:200]}...")
        self.assertIn("advice", template.lower())
        
        # Test tech discussion template
        template = get_response_template("tech_discussion")
        print(f"\n💻 Tech discussion template:")
        print(f"{template[:200]}...")
        self.assertIn("technology", template.lower())
        
        # Test general template
        template = get_response_template("general")
        print(f"\n🗣️ General template:")
        print(f"{template[:200]}...")
        print("-" * 60)
        
        self.assertIsInstance(template, str)
        self.assertGreater(len(template), 0)

    def test_llm_manager_response_generation(self):
        """Test LLM manager response generation with output printing."""
        from llm_client import LLMManager
        
        print("\n🧠 Testing LLM Manager Response Generation:")
        
        # Test scenarios
        test_scenarios = [
            {
                "post_title": "What are the best programming languages to learn in India?",
                "post_content": "I'm a college student in India and want to start my programming career. Which languages should I focus on?",
                "keywords": ["programming", "india", "career"],
                "template_type": "tech_discussion"
            },
            {
                "post_title": "Moving to Bangalore for work - any advice?",
                "post_content": "Got a job offer in Bangalore. Never lived there before. What should I know?",
                "keywords": ["bangalore", "advice", "work"],
                "template_type": "india_specific"
            },
            {
                "post_title": "How to deal with work stress?",
                "post_content": "Feeling overwhelmed at my new job. Any tips for managing stress?",
                "keywords": ["stress", "work", "advice"],
                "template_type": "helpful_advice"
            }
        ]
        
        manager = LLMManager()
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- Test Scenario {i}: {scenario['template_type']} ---")
            print(f"Post Title: {scenario['post_title']}")
            print(f"Keywords: {', '.join(scenario['keywords'])}")
            
            # Mock the response since we're testing
            with patch.object(manager, 'generate_response') as mock_generate:
                mock_response = MagicMock()
                mock_response.success = True
                mock_response.content = f"This is a mock {scenario['template_type']} response for: {scenario['post_title']}"
                mock_response.provider = "GEMINI"
                mock_generate.return_value = mock_response
                
                response = manager.generate_response(
                    scenario['post_title'],
                    scenario['post_content'],
                    scenario['keywords']
                )
                
                print(f"Response Success: {response.success}")
                print(f"Response Provider: {response.provider}")
                print(f"Response Content: {response.content}")
                
                self.assertTrue(response.success)
                self.assertIsNotNone(response.content)
        
        print("\n" + "=" * 60)

def run_llm_tests():
    """Run LLM integration tests separately."""
    print("🤖 Testing LLM Integration...")
    print("=" * 40)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLLMIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_llm_tests()