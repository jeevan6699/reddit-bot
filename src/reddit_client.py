"""Reddit client wrapper using PRAW for interacting with Reddit API."""

import time
import logging
from typing import List, Optional, Dict, Any, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta

import praw
from praw.models import Submission, Comment
from prawcore.exceptions import ResponseException, RequestException


@dataclass
class PostData:
    """Data structure for Reddit post information."""
    id: str
    title: str
    body: str
    author: str
    subreddit: str
    url: str
    created_utc: float
    score: int
    num_comments: int
    is_self: bool


class RedditClient:
    """Reddit API client with rate limiting and error handling."""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str, 
                 username: str, password: str):
        """Initialize Reddit client with credentials."""
        self.logger = logging.getLogger(__name__)
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                username=username,
                password=password
            )
            
            # Test authentication
            user = self.reddit.user.me()
            if user is None:
                raise Exception("Authentication failed - user is None")
            
            self.logger.info(f"Successfully authenticated as {username}")
            
        except Exception as e:
            error_msg = str(e)
            if "invalid_grant" in error_msg:
                self.logger.error("Reddit authentication failed - possible causes:")
                self.logger.error("1. Incorrect username/password")
                self.logger.error("2. Two-factor authentication enabled (disable for bot account)")
                self.logger.error("3. Account might be suspended or restricted")
                self.logger.error("4. Password contains special characters that need escaping")
            elif "invalid_client" in error_msg:
                self.logger.error("Reddit client credentials invalid - check CLIENT_ID and CLIENT_SECRET")
            else:
                self.logger.error(f"Reddit authentication error: {error_msg}")
            raise
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2  # Minimum seconds between requests
        self.last_reply_time = 0
        self.min_reply_interval = 600  # Minimum 10 minutes between replies
        
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def can_reply(self) -> bool:
        """Check if enough time has passed since last reply."""
        current_time = time.time()
        return (current_time - self.last_reply_time) >= self.min_reply_interval
    
    def get_new_posts(self, subreddit_name: str, limit: int = 25, 
                     time_filter: str = "hour") -> List[PostData]:
        """
        Get new posts from a subreddit.
        
        Args:
            subreddit_name: Name of the subreddit
            limit: Maximum number of posts to retrieve
            time_filter: Time filter ("hour", "day", "week", "month", "year", "all")
        
        Returns:
            List of PostData objects
        """
        self._rate_limit()
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            if time_filter == "hour":
                posts = subreddit.new(limit=limit)
            else:
                posts = subreddit.top(time_filter=time_filter, limit=limit)
            
            post_data = []
            for post in posts:
                try:
                    # Filter out posts older than specified time
                    if time_filter == "hour":
                        post_age = datetime.utcnow() - datetime.utcfromtimestamp(post.created_utc)
                        if post_age > timedelta(hours=1):
                            continue
                    
                    post_info = PostData(
                        id=post.id,
                        title=post.title,
                        body=post.selftext if post.is_self else "",
                        author=str(post.author) if post.author else "[deleted]",
                        subreddit=str(post.subreddit),
                        url=post.url,
                        created_utc=post.created_utc,
                        score=post.score,
                        num_comments=post.num_comments,
                        is_self=post.is_self
                    )
                    post_data.append(post_info)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing post {post.id}: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(post_data)} posts from r/{subreddit_name}")
            return post_data
            
        except Exception as e:
            self.logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            return []
    
    def reply_to_post(self, post_id: str, reply_text: str) -> bool:
        """
        Reply to a Reddit post.
        
        Args:
            post_id: Reddit post ID
            reply_text: Text to reply with
        
        Returns:
            True if successful, False otherwise
        """
        if not self.can_reply():
            self.logger.warning("Cannot reply yet - rate limit not reached")
            return False
        
        self._rate_limit()
        
        try:
            submission = self.reddit.submission(id=post_id)
            comment = submission.reply(reply_text)
            
            self.last_reply_time = time.time()
            self.logger.info(f"Successfully replied to post {post_id} with comment {comment.id}")
            return True
            
        except ResponseException as e:
            if "THREAD_LOCKED" in str(e):
                self.logger.warning(f"Cannot reply to post {post_id}: thread is locked")
            elif "RATELIMIT" in str(e):
                self.logger.warning(f"Rate limited when replying to post {post_id}")
            else:
                self.logger.error(f"Reddit API error replying to post {post_id}: {e}")
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error replying to post {post_id}: {e}")
            return False
    
    def get_post_details(self, post_id: str) -> Optional[PostData]:
        """Get detailed information about a specific post."""
        self._rate_limit()
        
        try:
            submission = self.reddit.submission(id=post_id)
            
            return PostData(
                id=submission.id,
                title=submission.title,
                body=submission.selftext if submission.is_self else "",
                author=str(submission.author) if submission.author else "[deleted]",
                subreddit=str(submission.subreddit),
                url=submission.url,
                created_utc=submission.created_utc,
                score=submission.score,
                num_comments=submission.num_comments,
                is_self=submission.is_self
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching post details for {post_id}: {e}")
            return None
    
    def is_valid_post(self, post: PostData) -> bool:
        """Check if a post is valid for responding to."""
        # Don't reply to deleted or removed posts
        if post.author == "[deleted]" or not post.title:
            return False
        
        # Don't reply to very downvoted posts
        if post.score < -5:
            return False
        
        # Don't reply to very old posts (more than 24 hours)
        post_age = datetime.utcnow() - datetime.utcfromtimestamp(post.created_utc)
        if post_age > timedelta(hours=24):
            return False
        
        return True