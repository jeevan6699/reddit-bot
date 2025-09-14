"""LLM client with support for multiple providers, focusing on Gemini."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None


class LLMProvider(Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    CLAUDE = "claude"
    OPENAI = "openai"


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    text: str
    provider: LLMProvider
    model: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    response_time: Optional[float] = None


class BaseLLMClient(ABC):
    """Base class for LLM clients."""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def generate_response(self, prompt: str, max_tokens: int = 500) -> Optional[LLMResponse]:
        """Generate a response using the LLM."""
        pass


class GeminiClient(BaseLLMClient):
    """Google Gemini client."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        super().__init__(api_key, model)
        
        if genai is None:
            raise ImportError("google-generativeai package not installed")
        
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
        
        # Safety settings to avoid overly restrictive filtering
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> Optional[LLMResponse]:
        """Generate response using Gemini."""
        start_time = time.time()
        
        try:
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
                top_p=0.8,
                top_k=40
            )
            
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            if response.text:
                response_time = time.time() - start_time
                
                return LLMResponse(
                    text=response.text.strip(),
                    provider=LLMProvider.GEMINI,
                    model=self.model,
                    response_time=response_time
                )
            else:
                self.logger.warning("Gemini returned empty response")
                return None
                
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            return None


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude client."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        super().__init__(api_key, model)
        
        if anthropic is None:
            raise ImportError("anthropic package not installed")
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> Optional[LLMResponse]:
        """Generate response using Claude."""
        start_time = time.time()
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response.content and response.content[0].text:
                response_time = time.time() - start_time
                
                return LLMResponse(
                    text=response.content[0].text.strip(),
                    provider=LLMProvider.CLAUDE,
                    model=self.model,
                    tokens_used=response.usage.output_tokens if hasattr(response, 'usage') else None,
                    response_time=response_time
                )
            else:
                self.logger.warning("Claude returned empty response")
                return None
                
        except Exception as e:
            self.logger.error(f"Claude API error: {e}")
            return None


class OpenAIClient(BaseLLMClient):
    """OpenAI client."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model)
        
        if openai is None:
            raise ImportError("openai package not installed")
        
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> Optional[LLMResponse]:
        """Generate response using OpenAI."""
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if response.choices and response.choices[0].message.content:
                response_time = time.time() - start_time
                
                return LLMResponse(
                    text=response.choices[0].message.content.strip(),
                    provider=LLMProvider.OPENAI,
                    model=self.model,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    response_time=response_time
                )
            else:
                self.logger.warning("OpenAI returned empty response")
                return None
                
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return None


class LLMManager:
    """Manager for multiple LLM providers with fallback support."""
    
    def __init__(self, primary_provider: LLMProvider = LLMProvider.GEMINI):
        self.logger = logging.getLogger(__name__)
        self.clients: Dict[LLMProvider, BaseLLMClient] = {}
        self.primary_provider = primary_provider
        self.fallback_order = [LLMProvider.GEMINI, LLMProvider.CLAUDE, LLMProvider.OPENAI]
        
        # Response templates for different contexts
        self.response_templates = {
            "india_specific": """You are a helpful assistant responding to a Reddit post about India or Indian topics. 
Provide a thoughtful, informative, and culturally aware response. Be respectful and avoid controversial topics.
Keep your response conversational and under 200 words.

Post Title: {title}
Post Content: {body}
Matched Keywords: {keywords}

Response:""",

            "helpful_advice": """You are a helpful assistant responding to someone seeking advice on Reddit.
Provide practical, supportive advice while being empathetic. Keep your response conversational and under 200 words.

Post Title: {title}
Post Content: {body}
Context: {keywords}

Response:""",

            "tech_discussion": """You are a knowledgeable assistant responding to a technology-related Reddit post.
Provide informative, accurate information while being approachable. Keep your response conversational and under 200 words.

Post Title: {title}
Post Content: {body}
Tech Topics: {keywords}

Response:""",

            "general": """You are a helpful assistant responding to a Reddit post.
Provide a thoughtful, relevant response that adds value to the discussion. Keep your response conversational and under 200 words.

Post Title: {title}
Post Content: {body}
Keywords: {keywords}

Response:"""
        }
    
    def add_client(self, provider: LLMProvider, client: BaseLLMClient):
        """Add an LLM client."""
        self.clients[provider] = client
        self.logger.info(f"Added {provider.value} client")
    
    def setup_gemini(self, api_key: str, model: str = "gemini-1.5-flash"):
        """Setup Gemini client."""
        try:
            client = GeminiClient(api_key, model)
            self.add_client(LLMProvider.GEMINI, client)
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Gemini: {e}")
            return False
    
    def setup_claude(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """Setup Claude client."""
        try:
            client = ClaudeClient(api_key, model)
            self.add_client(LLMProvider.CLAUDE, client)
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Claude: {e}")
            return False
    
    def setup_openai(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Setup OpenAI client."""
        try:
            client = OpenAIClient(api_key, model)
            self.add_client(LLMProvider.OPENAI, client)
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup OpenAI: {e}")
            return False
    
    def generate_reddit_response(self, title: str, body: str, keywords: List[str],
                                template_type: str = "general") -> Optional[LLMResponse]:
        """
        Generate a Reddit response using the available LLM providers.
        
        Args:
            title: Reddit post title
            body: Reddit post body
            keywords: Matched keywords
            template_type: Type of response template to use
            
        Returns:
            LLMResponse or None if all providers fail
        """
        # Get the appropriate template
        template = self.response_templates.get(template_type, self.response_templates["general"])
        
        # Format the prompt
        prompt = template.format(
            title=title,
            body=body or "No content provided",
            keywords=", ".join(keywords)
        )
        
        # Try providers in order (primary first, then fallbacks)
        providers_to_try = [self.primary_provider] + [
            p for p in self.fallback_order if p != self.primary_provider
        ]
        
        for provider in providers_to_try:
            if provider in self.clients:
                self.logger.info(f"Trying to generate response with {provider.value}")
                
                response = self.clients[provider].generate_response(prompt)
                if response:
                    self.logger.info(f"Successfully generated response with {provider.value}")
                    return response
                else:
                    self.logger.warning(f"Failed to generate response with {provider.value}")
        
        self.logger.error("All LLM providers failed to generate a response")
        return None
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers."""
        return list(self.clients.keys())
    
    def is_healthy(self) -> bool:
        """Check if at least one provider is available."""
        return len(self.clients) > 0