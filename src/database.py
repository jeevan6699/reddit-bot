"""Database models and operations for Reddit bot logging."""

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
import os


class InteractionType(Enum):
    """Types of bot interactions."""
    POST_CHECKED = "post_checked"
    KEYWORD_MATCHED = "keyword_matched" 
    RESPONSE_GENERATED = "response_generated"
    REPLY_POSTED = "reply_posted"
    REPLY_FAILED = "reply_failed"
    ERROR = "error"


@dataclass
class InteractionLog:
    """Log entry for bot interactions."""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    interaction_type: Optional[InteractionType] = None
    post_id: Optional[str] = None
    subreddit: Optional[str] = None
    post_title: Optional[str] = None
    matched_keywords: Optional[List[str]] = None
    llm_provider: Optional[str] = None
    response_text: Optional[str] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DatabaseManager:
    """SQLite database manager for Reddit bot."""
    
    def __init__(self, db_path: str = "database/reddit_bot.db"):
        """Initialize database manager."""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            # Create interactions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    interaction_type TEXT NOT NULL,
                    post_id TEXT,
                    subreddit TEXT,
                    post_title TEXT,
                    matched_keywords TEXT,  -- JSON array
                    llm_provider TEXT,
                    response_text TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    metadata TEXT  -- JSON object
                )
            ''')
            
            # Create posts table for tracking processed posts
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_posts (
                    post_id TEXT PRIMARY KEY,
                    subreddit TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT,
                    created_utc REAL,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
                    replied BOOLEAN DEFAULT FALSE,
                    reply_count INTEGER DEFAULT 0
                )
            ''')
            
            # Create statistics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date DATE PRIMARY KEY,
                    posts_checked INTEGER DEFAULT 0,
                    keywords_matched INTEGER DEFAULT 0,
                    responses_generated INTEGER DEFAULT 0,
                    successful_replies INTEGER DEFAULT 0,
                    failed_replies INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(interaction_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_interactions_post_id ON interactions(post_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_processed_posts_subreddit ON processed_posts(subreddit)')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def log_interaction(self, interaction: InteractionLog) -> int:
        """Log an interaction to the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute('''
                    INSERT INTO interactions (
                        interaction_type, post_id, subreddit, post_title,
                        matched_keywords, llm_provider, response_text,
                        success, error_message, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    interaction.interaction_type.value if interaction.interaction_type else None,
                    interaction.post_id,
                    interaction.subreddit,
                    interaction.post_title,
                    json.dumps(interaction.matched_keywords) if interaction.matched_keywords else None,
                    interaction.llm_provider,
                    interaction.response_text,
                    interaction.success,
                    interaction.error_message,
                    json.dumps(interaction.metadata) if interaction.metadata else None
                ))
                
                interaction_id = cursor.lastrowid
                conn.commit()
                
                # Update daily stats
                self._update_daily_stats(interaction.interaction_type)
                
                return interaction_id
                
        except Exception as e:
            self.logger.error(f"Error logging interaction: {e}")
            return -1
    
    def _update_daily_stats(self, interaction_type: InteractionType):
        """Update daily statistics."""
        try:
            today = datetime.now().date()
            
            with self._get_connection() as conn:
                # Insert or update daily stats
                conn.execute('''
                    INSERT OR IGNORE INTO daily_stats (date) VALUES (?)
                ''', (today,))
                
                # Update appropriate counter
                if interaction_type == InteractionType.POST_CHECKED:
                    column = "posts_checked"
                elif interaction_type == InteractionType.KEYWORD_MATCHED:
                    column = "keywords_matched"
                elif interaction_type == InteractionType.RESPONSE_GENERATED:
                    column = "responses_generated"
                elif interaction_type == InteractionType.REPLY_POSTED:
                    column = "successful_replies"
                elif interaction_type == InteractionType.REPLY_FAILED:
                    column = "failed_replies"
                elif interaction_type == InteractionType.ERROR:
                    column = "errors"
                else:
                    return
                
                conn.execute(f'''
                    UPDATE daily_stats 
                    SET {column} = {column} + 1
                    WHERE date = ?
                ''', (today,))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating daily stats: {e}")
    
    def mark_post_processed(self, post_id: str, subreddit: str, title: str, 
                           author: str, created_utc: float, replied: bool = False):
        """Mark a post as processed."""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO processed_posts (
                        post_id, subreddit, title, author, created_utc, 
                        last_checked, replied, reply_count
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 
                              COALESCE((SELECT reply_count FROM processed_posts WHERE post_id = ?), 0) + ?)
                ''', (post_id, subreddit, title, author, created_utc, replied, post_id, 1 if replied else 0))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error marking post as processed: {e}")
    
    def is_post_processed(self, post_id: str) -> bool:
        """Check if a post has been processed."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'SELECT 1 FROM processed_posts WHERE post_id = ?',
                    (post_id,)
                )
                return cursor.fetchone() is not None
                
        except Exception as e:
            self.logger.error(f"Error checking if post processed: {e}")
            return False
    
    def has_replied_to_post(self, post_id: str) -> bool:
        """Check if bot has already replied to a post."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'SELECT replied FROM processed_posts WHERE post_id = ? AND replied = TRUE',
                    (post_id,)
                )
                return cursor.fetchone() is not None
                
        except Exception as e:
            self.logger.error(f"Error checking if replied to post: {e}")
            return False
    
    def get_recent_interactions(self, limit: int = 50, 
                              interaction_type: Optional[InteractionType] = None) -> List[InteractionLog]:
        """Get recent interactions."""
        try:
            with self._get_connection() as conn:
                query = '''
                    SELECT * FROM interactions 
                    {} 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                '''
                
                if interaction_type:
                    query = query.format("WHERE interaction_type = ?")
                    params = (interaction_type.value, limit)
                else:
                    query = query.format("")
                    params = (limit,)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                interactions = []
                for row in rows:
                    interaction = InteractionLog(
                        id=row['id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        interaction_type=InteractionType(row['interaction_type']),
                        post_id=row['post_id'],
                        subreddit=row['subreddit'],
                        post_title=row['post_title'],
                        matched_keywords=json.loads(row['matched_keywords']) if row['matched_keywords'] else None,
                        llm_provider=row['llm_provider'],
                        response_text=row['response_text'],
                        success=bool(row['success']) if row['success'] is not None else None,
                        error_message=row['error_message'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else None
                    )
                    interactions.append(interaction)
                
                return interactions
                
        except Exception as e:
            self.logger.error(f"Error getting recent interactions: {e}")
            return []
    
    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily statistics for the last N days."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM daily_stats 
                    ORDER BY date DESC 
                    LIMIT ?
                ''', (days,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting daily stats: {e}")
            return []
    
    def get_total_stats(self) -> Dict[str, int]:
        """Get total statistics."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        SUM(posts_checked) as total_posts_checked,
                        SUM(keywords_matched) as total_keywords_matched,
                        SUM(responses_generated) as total_responses_generated,
                        SUM(successful_replies) as total_successful_replies,
                        SUM(failed_replies) as total_failed_replies,
                        SUM(errors) as total_errors
                    FROM daily_stats
                ''')
                
                row = cursor.fetchone()
                return {
                    'posts_checked': row['total_posts_checked'] or 0,
                    'keywords_matched': row['total_keywords_matched'] or 0,
                    'responses_generated': row['total_responses_generated'] or 0,
                    'successful_replies': row['total_successful_replies'] or 0,
                    'failed_replies': row['total_failed_replies'] or 0,
                    'errors': row['total_errors'] or 0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting total stats: {e}")
            return {
                'posts_checked': 0,
                'keywords_matched': 0,
                'responses_generated': 0,
                'successful_replies': 0,
                'failed_replies': 0,
                'errors': 0
            }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old interaction data."""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
            
            with self._get_connection() as conn:
                # Delete old interactions
                conn.execute(
                    'DELETE FROM interactions WHERE timestamp < ?',
                    (cutoff_date,)
                )
                
                # Delete old processed posts (keep for longer)
                old_cutoff = cutoff_date.replace(day=cutoff_date.day - 60)
                conn.execute(
                    'DELETE FROM processed_posts WHERE first_seen < ?',
                    (old_cutoff,)
                )
                
                conn.commit()
                self.logger.info(f"Cleaned up data older than {days_to_keep} days")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")


# Convenience functions for common operations
def create_database_manager(db_path: str = "database/reddit_bot.db") -> DatabaseManager:
    """Create and return a database manager instance."""
    return DatabaseManager(db_path)


def log_post_checked(db: DatabaseManager, post_id: str, subreddit: str, title: str):
    """Log that a post was checked."""
    interaction = InteractionLog(
        interaction_type=InteractionType.POST_CHECKED,
        post_id=post_id,
        subreddit=subreddit,
        post_title=title
    )
    return db.log_interaction(interaction)


def log_keyword_match(db: DatabaseManager, post_id: str, subreddit: str, 
                     title: str, keywords: List[str]):
    """Log that keywords were matched in a post."""
    interaction = InteractionLog(
        interaction_type=InteractionType.KEYWORD_MATCHED,
        post_id=post_id,
        subreddit=subreddit,
        post_title=title,
        matched_keywords=keywords
    )
    return db.log_interaction(interaction)


def log_response_generated(db: DatabaseManager, post_id: str, subreddit: str,
                          response_text: str, llm_provider: str):
    """Log that a response was generated."""
    interaction = InteractionLog(
        interaction_type=InteractionType.RESPONSE_GENERATED,
        post_id=post_id,
        subreddit=subreddit,
        response_text=response_text,
        llm_provider=llm_provider,
        success=True
    )
    return db.log_interaction(interaction)


def log_reply_posted(db: DatabaseManager, post_id: str, subreddit: str,
                    response_text: str, llm_provider: str):
    """Log that a reply was successfully posted."""
    interaction = InteractionLog(
        interaction_type=InteractionType.REPLY_POSTED,
        post_id=post_id,
        subreddit=subreddit,
        response_text=response_text,
        llm_provider=llm_provider,
        success=True
    )
    return db.log_interaction(interaction)


def log_reply_failed(db: DatabaseManager, post_id: str, subreddit: str,
                    error_message: str):
    """Log that a reply failed to post."""
    interaction = InteractionLog(
        interaction_type=InteractionType.REPLY_FAILED,
        post_id=post_id,
        subreddit=subreddit,
        error_message=error_message,
        success=False
    )
    return db.log_interaction(interaction)


def log_error(db: DatabaseManager, error_message: str, metadata: Optional[Dict[str, Any]] = None):
    """Log an error."""
    interaction = InteractionLog(
        interaction_type=InteractionType.ERROR,
        error_message=error_message,
        metadata=metadata,
        success=False
    )
    return db.log_interaction(interaction)