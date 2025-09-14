"""Keyword matching system for filtering Reddit posts."""

import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MatchType(Enum):
    """Types of keyword matching."""
    EXACT = "exact"
    PARTIAL = "partial"
    REGEX = "regex"
    SEMANTIC = "semantic"


@dataclass
class KeywordRule:
    """A keyword matching rule."""
    keywords: List[str]
    match_type: MatchType
    match_location: str  # "title", "body", "both"
    priority: int = 1  # Higher priority = more important
    response_template: Optional[str] = None  # Optional specific response template


@dataclass
class MatchResult:
    """Result of keyword matching."""
    matched: bool
    matched_keywords: List[str]
    match_locations: List[str]  # Where matches were found
    priority: int
    rule: KeywordRule


class KeywordMatcher:
    """Keyword matching engine for Reddit posts."""
    
    def __init__(self):
        """Initialize the keyword matcher."""
        self.logger = logging.getLogger(__name__)
        self.rules: List[KeywordRule] = []
        self.blacklist_keywords: Set[str] = set()
        
    def add_rule(self, rule: KeywordRule):
        """Add a keyword matching rule."""
        self.rules.append(rule)
        self.logger.debug(f"Added keyword rule with {len(rule.keywords)} keywords")
    
    def add_blacklist_keywords(self, keywords: List[str]):
        """Add keywords to blacklist (posts containing these won't be processed)."""
        self.blacklist_keywords.update(keyword.lower() for keyword in keywords)
    
    def load_default_rules(self):
        """Load default keyword rules for Indian and general discussion topics."""
        
        # India-specific keywords with high priority
        india_keywords = KeywordRule(
            keywords=[
                "india", "indian", "delhi", "mumbai", "bangalore", "chennai", "kolkata",
                "modi", "bjp", "congress", "bollywood", "cricket", "ipl", "rupee",
                "diwali", "holi", "monsoon", "chai", "samosa", "biryani",
                "startup", "tech hub", "silicon valley of india", "it sector"
            ],
            match_type=MatchType.PARTIAL,
            match_location="both",
            priority=3,
            response_template="india_specific"
        )
        
        # General helpful discussion keywords
        advice_keywords = KeywordRule(
            keywords=[
                "advice", "help", "suggestion", "recommend", "opinion",
                "what should i", "how do i", "need help", "confused",
                "career", "job", "interview", "salary", "work",
                "relationship", "dating", "marriage", "family"
            ],
            match_type=MatchType.PARTIAL,
            match_location="both",
            priority=2,
            response_template="helpful_advice"
        )
        
        # Technology and programming keywords
        tech_keywords = KeywordRule(
            keywords=[
                "programming", "coding", "developer", "software", "python",
                "javascript", "react", "ai", "machine learning", "data science",
                "startup", "tech", "algorithm", "database", "api"
            ],
            match_type=MatchType.PARTIAL,
            match_location="both",
            priority=2,
            response_template="tech_discussion"
        )
        
        # Add rules
        self.add_rule(india_keywords)
        self.add_rule(advice_keywords)
        self.add_rule(tech_keywords)
        
        # Add blacklist keywords (controversial or inappropriate topics)
        self.add_blacklist_keywords([
            "suicide", "depression", "self harm", "drugs", "illegal",
            "porn", "nsfw", "hate", "violence", "terrorist"
        ])
    
    def check_blacklist(self, title: str, body: str) -> bool:
        """Check if post contains blacklisted keywords."""
        text = f"{title} {body}".lower()
        
        for keyword in self.blacklist_keywords:
            if keyword in text:
                self.logger.info(f"Post blocked due to blacklist keyword: {keyword}")
                return True
        
        return False
    
    def _match_exact(self, keywords: List[str], text: str) -> List[str]:
        """Exact keyword matching."""
        matches = []
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches.append(keyword)
        
        return matches
    
    def _match_partial(self, keywords: List[str], text: str) -> List[str]:
        """Partial keyword matching using word boundaries."""
        matches = []
        text_lower = text.lower()
        
        for keyword in keywords:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matches.append(keyword)
        
        return matches
    
    def _match_regex(self, keywords: List[str], text: str) -> List[str]:
        """Regex keyword matching."""
        matches = []
        
        for keyword in keywords:
            try:
                if re.search(keyword, text, re.IGNORECASE):
                    matches.append(keyword)
            except re.error:
                self.logger.warning(f"Invalid regex pattern: {keyword}")
        
        return matches
    
    def match_post(self, title: str, body: str) -> List[MatchResult]:
        """
        Match keywords against a Reddit post.
        
        Args:
            title: Post title
            body: Post body text
            
        Returns:
            List of MatchResult objects, sorted by priority
        """
        # Check blacklist first
        if self.check_blacklist(title, body):
            return []
        
        results = []
        
        for rule in self.rules:
            matched_keywords = []
            match_locations = []
            
            # Check title if required
            if rule.match_location in ["title", "both"]:
                if rule.match_type == MatchType.EXACT:
                    title_matches = self._match_exact(rule.keywords, title)
                elif rule.match_type == MatchType.PARTIAL:
                    title_matches = self._match_partial(rule.keywords, title)
                elif rule.match_type == MatchType.REGEX:
                    title_matches = self._match_regex(rule.keywords, title)
                else:
                    title_matches = []
                
                if title_matches:
                    matched_keywords.extend(title_matches)
                    match_locations.append("title")
            
            # Check body if required
            if rule.match_location in ["body", "both"] and body:
                if rule.match_type == MatchType.EXACT:
                    body_matches = self._match_exact(rule.keywords, body)
                elif rule.match_type == MatchType.PARTIAL:
                    body_matches = self._match_partial(rule.keywords, body)
                elif rule.match_type == MatchType.REGEX:
                    body_matches = self._match_regex(rule.keywords, body)
                else:
                    body_matches = []
                
                if body_matches:
                    matched_keywords.extend(body_matches)
                    match_locations.append("body")
            
            # Create match result if any keywords matched
            if matched_keywords:
                result = MatchResult(
                    matched=True,
                    matched_keywords=list(set(matched_keywords)),  # Remove duplicates
                    match_locations=match_locations,
                    priority=rule.priority,
                    rule=rule
                )
                results.append(result)
        
        # Sort by priority (highest first)
        results.sort(key=lambda x: x.priority, reverse=True)
        
        if results:
            self.logger.info(f"Found {len(results)} keyword matches")
        
        return results
    
    def should_respond(self, matches: List[MatchResult], 
                      min_priority: int = 1) -> Tuple[bool, Optional[MatchResult]]:
        """
        Determine if bot should respond based on matches.
        
        Args:
            matches: List of match results
            min_priority: Minimum priority required to respond
            
        Returns:
            Tuple of (should_respond, best_match)
        """
        if not matches:
            return False, None
        
        best_match = matches[0]  # Already sorted by priority
        
        if best_match.priority >= min_priority:
            return True, best_match
        
        return False, None