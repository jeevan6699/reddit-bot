"""Utility functions for the Reddit bot."""

import logging
import yaml
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


def load_config(config_path: str = "config/settings.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading config from {config_path}: {e}")
        return {}


def load_keywords_config(keywords_path: str = "config/keywords.yaml") -> Dict[str, Any]:
    """Load keywords configuration from YAML file."""
    try:
        with open(keywords_path, 'r') as f:
            keywords_config = yaml.safe_load(f)
        return keywords_config
    except Exception as e:
        logging.error(f"Error loading keywords config from {keywords_path}: {e}")
        return {}


def setup_logging(log_level: str = "INFO", log_file: str = "logs/reddit_bot.log"):
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to specified length while preserving word boundaries."""
    if len(text) <= max_length:
        return text
    
    # Find the last space before max_length
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If space is reasonably close to end
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."


def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display."""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "Just now"


def clean_reddit_text(text: str) -> str:
    """Clean Reddit text by removing markdown and formatting."""
    if not text:
        return ""
    
    # Remove Reddit markdown
    import re
    
    # Remove links
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove bold/italic
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    
    # Remove strikethrough
    text = re.sub(r'~~([^~]+)~~', r'\1', text)
    
    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove multiple newlines
    text = re.sub(r'\n+', ' ', text)
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def is_spam_like(text: str) -> bool:
    """Check if text appears spam-like."""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for excessive caps
    caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
    if caps_ratio > 0.5 and len(text) > 10:
        return True
    
    # Check for excessive punctuation
    punct_ratio = sum(1 for c in text if c in '!?.,;:') / len(text)
    if punct_ratio > 0.3:
        return True
    
    # Check for spam keywords
    spam_keywords = [
        'click here', 'buy now', 'limited time', 'act now',
        'free money', 'get rich', 'make money fast',
        'telegram', 'whatsapp group', 'dm me'
    ]
    
    for keyword in spam_keywords:
        if keyword in text_lower:
            return True
    
    return False


def validate_environment() -> List[str]:
    """Validate required environment variables."""
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET', 
        'REDDIT_USERNAME',
        'REDDIT_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    # Check for at least one LLM provider
    llm_providers = [
        'GOOGLE_API_KEY',
        'ANTHROPIC_API_KEY', 
        'OPENAI_API_KEY'
    ]
    
    if not any(os.getenv(var) for var in llm_providers):
        missing_vars.append('At least one LLM API key (GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY)')
    
    return missing_vars


def get_safe_filename(filename: str) -> str:
    """Get a safe filename by removing/replacing invalid characters."""
    import re
    # Remove invalid characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    safe_filename = re.sub(r'_+', '_', safe_filename)
    return safe_filename.strip('_')


def calculate_response_quality_score(response: str, post_title: str, keywords: List[str]) -> float:
    """Calculate a quality score for generated responses."""
    score = 0.0
    
    if not response or len(response.strip()) < 10:
        return 0.0
    
    # Length check (prefer 50-200 characters)
    length = len(response)
    if 50 <= length <= 200:
        score += 1.0
    elif 30 <= length < 50 or 200 < length <= 300:
        score += 0.7
    else:
        score += 0.3
    
    # Keyword relevance
    response_lower = response.lower()
    post_title_lower = post_title.lower()
    
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in response_lower)
    if keyword_matches > 0:
        score += min(keyword_matches * 0.3, 1.0)
    
    # Title relevance
    title_words = post_title_lower.split()
    title_word_matches = sum(1 for word in title_words if len(word) > 3 and word in response_lower)
    if title_word_matches > 0:
        score += min(title_word_matches * 0.2, 0.8)
    
    # Check for conversational elements
    conversational_indicators = [
        'i think', 'in my opinion', 'you might', 'have you considered',
        'what about', 'perhaps', 'maybe', 'could', 'would', 'should'
    ]
    
    conv_matches = sum(1 for indicator in conversational_indicators if indicator in response_lower)
    if conv_matches > 0:
        score += 0.5
    
    # Penalize generic responses
    generic_phrases = [
        'that\'s interesting', 'thanks for sharing', 'great question',
        'i agree', 'good point', 'well said'
    ]
    
    generic_matches = sum(1 for phrase in generic_phrases if phrase in response_lower)
    if generic_matches > 0:
        score -= generic_matches * 0.3
    
    # Penalize spam-like content
    if is_spam_like(response):
        score -= 1.0
    
    return max(0.0, min(5.0, score))


def backup_database(db_path: str, backup_dir: str = "database/backups"):
    """Create a backup of the database."""
    try:
        import shutil
        from datetime import datetime
        
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"reddit_bot_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(db_path, backup_path)
        
        # Keep only last 5 backups
        backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("reddit_bot_backup_")])
        while len(backups) > 5:
            oldest_backup = backups.pop(0)
            os.remove(os.path.join(backup_dir, oldest_backup))
        
        logging.info(f"Database backed up to {backup_path}")
        return backup_path
        
    except Exception as e:
        logging.error(f"Error backing up database: {e}")
        return None


def parse_subreddit_list(subreddit_string: str) -> List[str]:
    """Parse comma-separated subreddit list."""
    if not subreddit_string:
        return []
    
    subreddits = []
    for sub in subreddit_string.split(','):
        sub = sub.strip().lower()
        if sub:
            # Remove r/ prefix if present
            if sub.startswith('r/'):
                sub = sub[2:]
            subreddits.append(sub)
    
    return subreddits


def log_error(error: Exception, context: str = "") -> None:
    """Log error with context to file."""
    try:
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'error.log')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {context}: {type(error).__name__}: {error}\n")
            
    except Exception:
        pass  # Don't fail if logging fails