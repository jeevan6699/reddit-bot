"""Main Reddit bot implementation."""

import logging
import time
import schedule
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

from reddit_client import RedditClient, PostData
from llm_client import LLMManager, LLMProvider, LLMResponse
from keyword_matcher import KeywordMatcher, MatchResult
from database import DatabaseManager, InteractionType, log_post_checked, log_keyword_match, log_response_generated, log_reply_posted, log_reply_failed, log_error
from web_ui import monitor


class RedditBot:
    """Main Reddit bot class."""
    
    def __init__(self, config_path: str = "config/.env"):
        """Initialize the Reddit bot."""
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.is_paused = False
        
        # Load environment variables
        load_dotenv(config_path)
        
        # Initialize components
        self.reddit_client: Optional[RedditClient] = None
        self.llm_manager = LLMManager(primary_provider=LLMProvider.GEMINI)
        self.keyword_matcher = KeywordMatcher()
        self.database = DatabaseManager()
        
        # Configuration from environment variables
        self.subreddits = os.getenv('SUBREDDITS', 'india,AskReddit').split(',')
        self.subreddits = [s.strip() for s in self.subreddits]  # Remove whitespace
        self.check_interval_minutes = int(os.getenv('CHECK_INTERVAL_MINUTES', '60'))
        self.max_replies_per_hour = int(os.getenv('MAX_REPLIES_PER_HOUR', '3'))
        self.min_score_threshold = 0  # Minimum post score to consider
        
        # Rate limiting
        self.hourly_reply_count = 0
        self.last_hour_reset = datetime.now().hour
        
        # Initialize components
        self._setup_components()
        
        # Update monitor
        monitor.current_subreddits = self.subreddits
        
    def _setup_components(self):
        """Setup Reddit client, LLM providers, and keyword matching."""
        try:
            # Setup Reddit client
            reddit_creds = {
                'client_id': os.getenv('REDDIT_CLIENT_ID'),
                'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
                'user_agent': os.getenv('REDDIT_USER_AGENT', 'RedditBot/1.0'),
                'username': os.getenv('REDDIT_USERNAME'),
                'password': os.getenv('REDDIT_PASSWORD')
            }
            
            if all(reddit_creds.values()):
                self.reddit_client = RedditClient(**reddit_creds)
                self.logger.info("Reddit client initialized successfully")
            else:
                self.logger.error("Missing Reddit credentials")
                return False
            
            # Setup LLM providers
            providers_setup = []
            
            # Gemini (primary)
            gemini_key = os.getenv('GOOGLE_API_KEY')
            if gemini_key:
                if self.llm_manager.setup_gemini(gemini_key):
                    providers_setup.append("gemini")
                    self.logger.info("Gemini client initialized successfully")
            
            # Claude (fallback)
            claude_key = os.getenv('ANTHROPIC_API_KEY')
            if claude_key:
                if self.llm_manager.setup_claude(claude_key):
                    providers_setup.append("claude")
                    self.logger.info("Claude client initialized successfully")
            
            # OpenAI (fallback)
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                if self.llm_manager.setup_openai(openai_key):
                    providers_setup.append("openai")
                    self.logger.info("OpenAI client initialized successfully")
            
            if not providers_setup:
                self.logger.error("No LLM providers configured")
                return False
            
            monitor.active_providers = providers_setup
            
            # Setup keyword matching
            self.keyword_matcher.load_default_rules()
            self.logger.info("Keyword matcher initialized with default rules")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up components: {e}")
            log_error(self.database, f"Setup error: {e}")
            return False
    
    def _reset_hourly_limits(self):
        """Reset hourly rate limits if necessary."""
        current_hour = datetime.now().hour
        if current_hour != self.last_hour_reset:
            self.hourly_reply_count = 0
            self.last_hour_reset = current_hour
            self.logger.info("Hourly rate limits reset")
    
    def _can_reply(self) -> bool:
        """Check if bot can reply based on rate limits."""
        self._reset_hourly_limits()
        
        # Check hourly limit
        if self.hourly_reply_count >= self.max_replies_per_hour:
            self.logger.info(f"Hourly reply limit reached ({self.max_replies_per_hour})")
            return False
        
        # Check Reddit client rate limit
        if not self.reddit_client.can_reply():
            self.logger.info("Reddit client rate limit not reached")
            return False
        
        return True
    
    def check_subreddit(self, subreddit_name: str):
        """Check a subreddit for new posts and potentially respond."""
        self.logger.info(f"Checking r/{subreddit_name} for new posts")
        
        try:
            # Get new posts
            posts = self.reddit_client.get_new_posts(subreddit_name, limit=25)
            
            if not posts:
                self.logger.info(f"No new posts found in r/{subreddit_name}")
                return
            
            self.logger.info(f"Found {len(posts)} posts in r/{subreddit_name}")
            
            for post in posts:
                if self.is_paused:
                    self.logger.info("Bot is paused, stopping post processing")
                    break
                
                self._process_post(post)
                
                # Small delay between processing posts
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error checking r/{subreddit_name}: {e}")
            log_error(self.database, f"Error checking r/{subreddit_name}: {e}")
            monitor.log_error(f"Error checking r/{subreddit_name}: {e}")
    
    def _process_post(self, post: PostData):
        """Process a single Reddit post."""
        try:
            # Log that we checked this post
            log_post_checked(self.database, post.id, post.subreddit, post.title)
            monitor.increment_stat('posts_checked')
            
            # Check if already processed
            if self.database.is_post_processed(post.id):
                self.logger.debug(f"Post {post.id} already processed")
                return
            
            # Check if post is valid for responding
            if not self.reddit_client.is_valid_post(post):
                self.logger.debug(f"Post {post.id} not valid for responding")
                self.database.mark_post_processed(
                    post.id, post.subreddit, post.title, post.author, post.created_utc
                )
                return
            
            # Check keyword matches
            matches = self.keyword_matcher.match_post(post.title, post.body)
            
            if not matches:
                self.logger.debug(f"No keyword matches for post {post.id}")
                self.database.mark_post_processed(
                    post.id, post.subreddit, post.title, post.author, post.created_utc
                )
                return
            
            # Log keyword match
            all_keywords = []
            for match in matches:
                all_keywords.extend(match.matched_keywords)
            
            log_keyword_match(self.database, post.id, post.subreddit, post.title, all_keywords)
            monitor.increment_stat('keywords_matched')
            monitor.log_activity('keyword_match', {
                'post_id': post.id,
                'subreddit': post.subreddit,
                'keywords': all_keywords[:5]  # Limit for display
            })
            
            # Check if we should respond
            should_respond, best_match = self.keyword_matcher.should_respond(matches, min_priority=2)
            
            if not should_respond:
                self.logger.info(f"Post {post.id} matches keywords but priority too low")
                self.database.mark_post_processed(
                    post.id, post.subreddit, post.title, post.author, post.created_utc
                )
                return
            
            # Check if already replied to this post
            if self.database.has_replied_to_post(post.id):
                self.logger.info(f"Already replied to post {post.id}")
                return
            
            # Check rate limits
            if not self._can_reply():
                self.logger.info(f"Rate limit reached, skipping reply to post {post.id}")
                return
            
            # Generate response
            response = self._generate_response(post, best_match)
            
            if not response:
                self.logger.warning(f"Failed to generate response for post {post.id}")
                return
            
            # Post reply
            if self._post_reply(post, response):
                self.hourly_reply_count += 1
                self.database.mark_post_processed(
                    post.id, post.subreddit, post.title, post.author, post.created_utc, replied=True
                )
            else:
                self.database.mark_post_processed(
                    post.id, post.subreddit, post.title, post.author, post.created_utc
                )
                
        except Exception as e:
            self.logger.error(f"Error processing post {post.id}: {e}")
            log_error(self.database, f"Error processing post {post.id}: {e}")
            monitor.log_error(f"Error processing post {post.id}: {e}")
    
    def _generate_response(self, post: PostData, match: MatchResult) -> Optional[LLMResponse]:
        """Generate a response for a post."""
        try:
            # Determine template type
            template_type = "general"
            if match.rule.response_template:
                template_type = match.rule.response_template
            
            # Generate response
            response = self.llm_manager.generate_reddit_response(
                title=post.title,
                body=post.body,
                keywords=match.matched_keywords,
                template_type=template_type
            )
            
            if response:
                log_response_generated(
                    self.database, post.id, post.subreddit, 
                    response.text, response.provider.value
                )
                monitor.increment_stat('responses_generated')
                monitor.log_activity('response_generated', {
                    'post_id': post.id,
                    'provider': response.provider.value,
                    'length': len(response.text)
                })
                
                self.logger.info(f"Generated response for post {post.id} using {response.provider.value}")
                return response
            else:
                self.logger.warning(f"Failed to generate response for post {post.id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating response for post {post.id}: {e}")
            log_error(self.database, f"Error generating response: {e}")
            return None
    
    def _post_reply(self, post: PostData, response: LLMResponse) -> bool:
        """Post a reply to Reddit."""
        try:
            success = self.reddit_client.reply_to_post(post.id, response.text)
            
            if success:
                log_reply_posted(
                    self.database, post.id, post.subreddit,
                    response.text, response.provider.value
                )
                monitor.increment_stat('successful_replies')
                monitor.log_activity('reply_posted', {
                    'post_id': post.id,
                    'subreddit': post.subreddit,
                    'provider': response.provider.value
                })
                
                self.logger.info(f"Successfully replied to post {post.id}")
                return True
            else:
                log_reply_failed(self.database, post.id, post.subreddit, "Reddit API error")
                monitor.increment_stat('failed_replies')
                monitor.log_activity('reply_failed', {
                    'post_id': post.id,
                    'subreddit': post.subreddit,
                    'reason': 'reddit_api_error'
                })
                
                self.logger.warning(f"Failed to reply to post {post.id}")
                return False
                
        except Exception as e:
            error_msg = f"Error posting reply: {e}"
            log_reply_failed(self.database, post.id, post.subreddit, error_msg)
            monitor.increment_stat('failed_replies')
            monitor.log_error(error_msg)
            
            self.logger.error(f"Error posting reply to {post.id}: {e}")
            return False
    
    def run_check_cycle(self):
        """Run a single check cycle for all subreddits."""
        if self.is_paused:
            self.logger.info("Bot is paused, skipping check cycle")
            return
        
        self.logger.info("Starting check cycle")
        monitor.log_activity('check_cycle', {'subreddits': self.subreddits})
        
        for subreddit in self.subreddits:
            if self.is_paused or not self.is_running:
                break
            
            self.check_subreddit(subreddit)
            
            # Delay between subreddits
            time.sleep(5)
        
        self.logger.info("Check cycle completed")
    
    def start(self):
        """Start the Reddit bot."""
        if not self.reddit_client or not self.llm_manager.is_healthy():
            self.logger.error("Cannot start bot: missing required components")
            monitor.update_status("error")
            return False
        
        self.is_running = True
        self.is_paused = False
        monitor.update_status("running")
        
        self.logger.info("Reddit bot started")
        monitor.log_activity('bot_control', {'action': 'started'})
        
        # Schedule periodic checks
        schedule.clear()  # Clear any existing schedules
        schedule.every(self.check_interval_minutes).minutes.do(self.run_check_cycle)
        
        # Run initial check
        self.run_check_cycle()
        
        return True
    
    def stop(self):
        """Stop the Reddit bot."""
        self.is_running = False
        self.is_paused = False
        monitor.update_status("stopped")
        
        schedule.clear()
        
        self.logger.info("Reddit bot stopped")
        monitor.log_activity('bot_control', {'action': 'stopped'})
    
    def pause(self):
        """Pause the Reddit bot."""
        self.is_paused = True
        monitor.update_status("paused")
        
        self.logger.info("Reddit bot paused")
        monitor.log_activity('bot_control', {'action': 'paused'})
    
    def resume(self):
        """Resume the Reddit bot."""
        if self.is_running:
            self.is_paused = False
            monitor.update_status("running")
            
            self.logger.info("Reddit bot resumed")
            monitor.log_activity('bot_control', {'action': 'resumed'})
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        stats = self.database.get_total_stats()
        
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'subreddits': self.subreddits,
            'llm_providers': [p.value for p in self.llm_manager.get_available_providers()],
            'hourly_reply_count': self.hourly_reply_count,
            'max_replies_per_hour': self.max_replies_per_hour,
            'stats': stats
        }


def run_bot_scheduler():
    """Run the bot's scheduled tasks in a separate thread."""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/reddit_bot.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create bot instance
    bot = RedditBot()
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_bot_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Start web UI in a separate thread
    from web_ui import run_ui
    ui_thread = threading.Thread(
        target=lambda: run_ui(host='localhost', port=5000, debug=False),
        daemon=True
    )
    ui_thread.start()
    
    try:
        # Start the bot
        if bot.start():
            print("Reddit bot started successfully!")
            print("Web UI available at: http://localhost:5000")
            
            # Keep the main thread alive
            while bot.is_running:
                time.sleep(10)
                
                # Update monitor stats
                stats = bot.database.get_total_stats()
                monitor.stats.update(stats)
        else:
            print("Failed to start Reddit bot")
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        bot.stop()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        bot.stop()