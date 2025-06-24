import logging
import re
from typing import Dict, List, Optional
from datetime import datetime
from functools import lru_cache

from ..models.email_models import Email

class EmailCategorizationService:
    """Service for categorizing emails using rule-based and ML approaches."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define categorization rules (can be extended with ML models)
        self.category_rules = {
            'billing': {
                'keywords': ['invoice', 'payment', 'bill', 'billing', 'receipt', 'charge', 'subscription'],
                'sender_patterns': ['billing@', 'invoice@', 'payments@', 'noreply@paypal', 'stripe'],
                'priority': 1,
                'weight': 1.5  # Higher weight for billing category
            },
            'support': {
                'keywords': ['support', 'help', 'assistance', 'ticket', 'issue', 'problem', 'question'],
                'sender_patterns': ['support@', 'help@', 'customer@', 'service@'],
                'priority': 2,
                'weight': 1.2
            },
            'marketing': {
                'keywords': ['newsletter', 'promotion', 'offer', 'sale', 'discount', 'marketing', 'unsubscribe'],
                'sender_patterns': ['marketing@', 'newsletter@', 'promo@', 'offers@'],
                'priority': 3,
                'weight': 1.0
            },
            'notification': {
                'keywords': ['notification', 'alert', 'reminder', 'update', 'status', 'confirm'],
                'sender_patterns': ['no-reply@', 'noreply@', 'notification@', 'alerts@'],
                'priority': 4,
                'weight': 1.3
            },
            'security': {
                'keywords': ['security', 'password', 'login', 'verification', 'authentication', 'suspicious'],
                'sender_patterns': ['security@', 'auth@', 'verification@'],
                'priority': 0,  # Highest priority
                'weight': 2.0  # Highest weight for security
            }
        }
        
        self.default_category = 'general'
        
        # Statistics tracking
        self.categorization_stats = {
            'total_categorized': 0,
            'category_counts': {},
            'last_reset': datetime.now()
        }
        
        # Pre-compile regex patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance."""
        self.compiled_patterns = {}
        for category, rules in self.category_rules.items():
            self.compiled_patterns[category] = {
                'keywords': [re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE) for k in rules['keywords']],
                'sender_patterns': [re.compile(p, re.IGNORECASE) for p in rules['sender_patterns']]
            }
    
    # @lru_cache(maxsize=1000)
    def categorize_email(self, email: Email) -> str:
        """
        Categorize an email based on subject, sender, and content.
        Uses LRU cache to improve performance for similar emails.
        
        Args:
            email: Email object to categorize
            
        Returns:
            Category string
        """
        try:
            # Combine text for analysis
            text_to_analyze = f"{email.subject} {email.sender} {email.body}".lower()
            
            # Find matching categories with scores
            category_scores = {}
            
            for category, rules in self.category_rules.items():
                score = self._calculate_category_score(text_to_analyze, email.sender.lower(), rules)
                if score > 0:
                    category_scores[category] = score
            
            # Select category with highest score
            if category_scores:
                best_category = max(category_scores.items(), key=lambda x: x[1])[0]
                category = best_category
            else:
                category = self.default_category
            
            # Update statistics
            self._update_stats(category)
            
            self.logger.debug(f"Email categorized as '{category}': {email.subject[:50]}...")
            
            return category
            
        except Exception as e:
            self.logger.error(f"Error categorizing email: {str(e)}")
            return self.default_category
    
    def _calculate_category_score(self, text: str, sender: str, rules: Dict) -> float:
        """
        Calculate category score based on rules.
        Optimized version using pre-compiled patterns.
        
        Args:
            text: Combined email text (subject + body)
            sender: Email sender
            rules: Category rules dictionary
            
        Returns:
            Score float (higher = better match)
        """
        score = 0.0
        patterns = self.compiled_patterns.get(rules.get('category', ''), {})
        
        # Check keywords in text using pre-compiled patterns
        keyword_matches = sum(1 for pattern in patterns.get('keywords', []) if pattern.search(text))
        score += keyword_matches * 2.0 * rules.get('weight', 1.0)
        
        # Check sender patterns using pre-compiled patterns
        sender_matches = sum(1 for pattern in patterns.get('sender_patterns', []) if pattern.search(sender))
        score += sender_matches * 3.0 * rules.get('weight', 1.0)
        
        # Apply priority bonus (lower priority number = higher bonus)
        priority_bonus = (5 - rules['priority']) * 0.5
        score += priority_bonus
        
        return score
    
    def _update_stats(self, category: str):
        """Update categorization statistics."""
        self.categorization_stats['total_categorized'] += 1
        
        if category not in self.categorization_stats['category_counts']:
            self.categorization_stats['category_counts'][category] = 0
        
        self.categorization_stats['category_counts'][category] += 1
    
    def get_categorization_stats(self) -> Dict:
        """Get categorization statistics."""
        return {
            'total_categorized': self.categorization_stats['total_categorized'],
            'category_distribution': self.categorization_stats['category_counts'].copy(),
            'available_categories': list(self.category_rules.keys()) + [self.default_category],
            'last_reset': self.categorization_stats['last_reset'].isoformat()
        }
    
    def reset_stats(self):
        """Reset categorization statistics."""
        self.categorization_stats = {
            'total_categorized': 0,
            'category_counts': {},
            'last_reset': datetime.now()
        }
        self.logger.info("Categorization statistics reset")
    
    def update_category_rules(self, category: str, rules: Dict) -> bool:
        """
        Update or add category rules.
        
        Args:
            category: Category name
            rules: Rules dictionary with keywords, sender_patterns, priority
            
        Returns:
            True if successful, False otherwise
        """
        try:
            required_fields = ['keywords', 'sender_patterns', 'priority']
            
            if not all(field in rules for field in required_fields):
                self.logger.error(f"Invalid rules format for category {category}")
                return False
            
            if not isinstance(rules['keywords'], list) or not isinstance(rules['sender_patterns'], list):
                self.logger.error(f"Keywords and sender_patterns must be lists for category {category}")
                return False
            
            if not isinstance(rules['priority'], int) or rules['priority'] < 0:
                self.logger.error(f"Priority must be a non-negative integer for category {category}")
                return False
            
            # Add weight if not present
            if 'weight' not in rules:
                rules['weight'] = 1.0
            
            self.category_rules[category] = rules
            self._compile_patterns()  # Recompile patterns after update
            self.logger.info(f"Category rules updated for: {category}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating category rules: {str(e)}")
            return False
    
    def get_category_rules(self) -> Dict:
        """Get all category rules."""
        return self.category_rules.copy()
    
    def delete_category(self, category: str) -> bool:
        """
        Delete a custom category.
        
        Args:
            category: Category name to delete
            
        Returns:
            True if successful, False otherwise
        """
        if category == self.default_category:
            self.logger.error(f"Cannot delete default category: {category}")
            return False
        
        if category in self.category_rules:
            del self.category_rules[category]
            self._compile_patterns()  # Recompile patterns after deletion
            self.logger.info(f"Category deleted: {category}")
            return True
        
        return False
    
    def suggest_category_improvements(self, emails: List[Email]) -> Dict:
        """
        Analyze emails to suggest category rule improvements.
        This is a placeholder for ML-based improvements.
        
        Args:
            emails: List of emails to analyze
            
        Returns:
            Dictionary with improvement suggestions
        """
        suggestions = {
            'common_uncategorized_keywords': [],
            'potential_new_categories': [],
            'sender_pattern_suggestions': {}
        }
        
        try:
            uncategorized_emails = [e for e in emails if e.category == self.default_category]
            
            if len(uncategorized_emails) > 10:  # Only analyze if we have enough data
                # Find common keywords in uncategorized emails
                word_counts = {}
                sender_domains = {}
                
                for email in uncategorized_emails:
                    words = re.findall(r'\b\w+\b', email.subject.lower())
                    for word in words:
                        if len(word) > 3:  # Ignore short words
                            word_counts[word] = word_counts.get(word, 0) + 1
                    
                    # Extract sender domain
                    if '@' in email.sender:
                        domain = email.sender.split('@')[-1].split('>')[0]
                        sender_domains[domain] = sender_domains.get(domain, 0) + 1
                
                # Top uncategorized keywords
                top_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                suggestions['common_uncategorized_keywords'] = [kw[0] for kw in top_keywords if kw[1] > 2]
                
                # Top sender domains
                top_domains = sorted(sender_domains.items(), key=lambda x: x[1], reverse=True)[:5]
                suggestions['sender_pattern_suggestions'] = {domain: count for domain, count in top_domains if count > 2}
        
        except Exception as e:
            self.logger.error(f"Error generating category suggestions: {str(e)}")
        
        return suggestions
