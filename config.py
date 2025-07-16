"""
Configuration management for Reddit Persona Analyzer
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for managing API keys and settings"""
    
    # Reddit API Configuration
    REDDIT_CLIENT_ID: Optional[str] = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET: Optional[str] = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT: str = os.getenv('REDDIT_USER_AGENT', 'RedditPersonaAnalyzer/1.0')
    
    # AI API Configuration
    OPENROUTER_API_KEY: Optional[str] = os.getenv('OPENROUTER_API_KEY')
    AI_API_URL: str = os.getenv('AI_API_URL', 'https://openrouter.ai/api/v1/chat/completions')
    
    # Application Settings
    MAX_POSTS: int = int(os.getenv('MAX_POSTS', '50'))
    MAX_COMMENTS: int = int(os.getenv('MAX_COMMENTS', '50'))
    OUTPUT_DIR: str = os.getenv('OUTPUT_DIR', 'output')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present"""
        required_vars = [
            ('REDDIT_CLIENT_ID', cls.REDDIT_CLIENT_ID),
            ('REDDIT_CLIENT_SECRET', cls.REDDIT_CLIENT_SECRET),
            ('OPENROUTER_API_KEY', cls.OPENROUTER_API_KEY)
        ]
        missing = [name for name, value in required_vars if not value]
        if missing:
            print(f"❌ Missing required environment variables: {', '.join(missing)}")
            print("Please check your .env file and ensure all required variables are set.")
            return False
        return True
    
    @classmethod
    def get_reddit_config(cls) -> Dict[str, str]:
        """Get Reddit API configuration"""
        return {
            'client_id': cls.REDDIT_CLIENT_ID,
            'client_secret': cls.REDDIT_CLIENT_SECRET,
            'user_agent': cls.REDDIT_USER_AGENT
        }
    
    @classmethod
    def get_ai_config(cls) -> Dict[str, str]:
        """Get AI API configuration"""
        return {
            'api_key': cls.OPENROUTER_API_KEY,
            'api_url': cls.AI_API_URL
        }
