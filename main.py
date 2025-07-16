import os
from dotenv import load_dotenv
# Load .env from absolute path
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path)
"""
Reddit User Persona Analyzer
Scrapes Reddit user data and generates detailed personas using AI analysis.
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import praw
import requests
from urllib.parse import urlparse

# Configure logging
log_path = os.path.join(os.path.expanduser('~'), 'reddit_analyzer.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RedditContent:
    """Data class for Reddit content"""
    content_type: str  # 'post' or 'comment'
    title: str
    body: str
    score: int
    created_utc: float
    subreddit: str
    url: str
    permalink: str

class RedditScraper:
    """Handles Reddit data scraping using PRAW"""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit API client"""
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            # Test connection
            self.reddit.user.me()
            logger.info("Successfully connected to Reddit API")
        except Exception as e:
            logger.error(f"Failed to connect to Reddit API: {e}")
            raise
    
    def extract_username(self, url_or_username: str) -> str:
        """Extract username from Reddit URL or return username directly"""
        if url_or_username.startswith('http'):
            # Parse URL to extract username
            parsed = urlparse(url_or_username)
            path_parts = parsed.path.strip('/').split('/')
            if 'user' in path_parts:
                username_index = path_parts.index('user') + 1
                if username_index < len(path_parts):
                    return path_parts[username_index]
            raise ValueError(f"Could not extract username from URL: {url_or_username}")
        else:
            # Remove u/ prefix if present
            return url_or_username.replace('u/', '').replace('/u/', '')
    
    def scrape_user_data(self, username: str, max_posts: int = 50, max_comments: int = 50) -> Tuple[List[RedditContent], List[RedditContent]]:
        """Scrape user's posts and comments"""
        try:
            user = self.reddit.redditor(username)
            posts = []
            comments = []
            
            logger.info(f"Scraping data for user: {username}")
            
            # Scrape posts
            logger.info("Scraping posts...")
            for submission in user.submissions.new(limit=max_posts):
                if submission.selftext or submission.title:
                    posts.append(RedditContent(
                        content_type='post',
                        title=submission.title,
                        body=submission.selftext,
                        score=submission.score,
                        created_utc=submission.created_utc,
                        subreddit=str(submission.subreddit),
                        url=submission.url,
                        permalink=f"https://reddit.com{submission.permalink}"
                    ))
            
            # Scrape comments
            logger.info("Scraping comments...")
            for comment in user.comments.new(limit=max_comments):
                if hasattr(comment, 'body') and comment.body:
                    comments.append(RedditContent(
                        content_type='comment',
                        title=f"Comment in r/{comment.subreddit}",
                        body=comment.body,
                        score=comment.score,
                        created_utc=comment.created_utc,
                        subreddit=str(comment.subreddit),
                        url="",
                        permalink=f"https://reddit.com{comment.permalink}"
                    ))
            
            logger.info(f"Scraped {len(posts)} posts and {len(comments)} comments")
            return posts, comments
            
        except Exception as e:
            logger.error(f"Error scraping user data: {e}")
            raise

class PersonaAnalyzer:
    """Handles AI-powered persona analysis"""
    
    def __init__(self, api_key: str, api_url: str = "https://openrouter.ai/api/v1/chat/completions", model: str = "openrouter/openai/gpt-3.5-turbo"):
        """Initialize AI API client"""
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def prepare_content_for_analysis(self, posts: List[RedditContent], comments: List[RedditContent]) -> str:
        """Prepare Reddit content for AI analysis"""
        content_text = "REDDIT USER CONTENT FOR ANALYSIS:\n\n"
        
        content_text += "=== POSTS ===\n"
        for i, post in enumerate(posts[:25], 1):  # Limit to avoid token limits
            content_text += f"\nPOST {i}:\n"
            content_text += f"Subreddit: r/{post.subreddit}\n"
            content_text += f"Title: {post.title}\n"
            content_text += f"Content: {post.body[:500]}...\n" if len(post.body) > 500 else f"Content: {post.body}\n"
            content_text += f"Score: {post.score}\n"
            content_text += f"Link: {post.permalink}\n"
        
        content_text += "\n=== COMMENTS ===\n"
        for i, comment in enumerate(comments[:25], 1):  # Limit to avoid token limits
            content_text += f"\nCOMMENT {i}:\n"
            content_text += f"Subreddit: r/{comment.subreddit}\n"
            content_text += f"Content: {comment.body[:300]}...\n" if len(comment.body) > 300 else f"Content: {comment.body}\n"
            content_text += f"Score: {comment.score}\n"
            content_text += f"Link: {comment.permalink}\n"
        
        return content_text
    
    def analyze_persona(self, content: str, username: str) -> str:
        """Send content to AI for persona analysis"""
        prompt = f"""
        Analyze the following Reddit user's posts and comments to create a detailed user persona. 
        
        For the user '{username}', provide a comprehensive analysis including:
        
        1. **PERSONALITY TRAITS** - What kind of person are they? (e.g., introverted/extroverted, optimistic/pessimistic, analytical/creative, etc.)
        
        2. **INTERESTS AND HOBBIES** - What are they passionate about? What do they spend time on?
        
        3. **WRITING STYLE** - How do they communicate? (formal/casual, humorous/serious, detailed/brief, etc.)
        
        4. **POSSIBLE DEMOGRAPHICS** - Age estimate, location clues, profession hints, education level, etc.
        
        5. **BEHAVIORAL PATTERNS** - How do they interact on Reddit? What triggers their engagement?
        
        6. **VALUES AND BELIEFS** - What seems important to them based on their content?
        
        **IMPORTANT**: For EACH characteristic you identify, you MUST cite the specific post or comment that supports this conclusion. Use the format [CITATION: POST/COMMENT X - brief quote] after each trait.
        
        Format your response as a detailed user persona report with clear sections and citations.
        
        {content}
        """
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert social media analyst specializing in creating detailed user personas from social media content. Provide thorough, evidence-based analysis with specific citations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            logger.info("Sending content to AI for analysis...")
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            if response.status_code != 200:
                logger.error(f"AI API error {response.status_code}: {response.text}")
                print(f"\n❌ AI API error {response.status_code}: {response.text}\n")
                raise Exception(f"AI API error {response.status_code}: {response.text}")
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            raise

class PersonaGenerator:
    """Main class that orchestrates the persona generation process"""
    
    def __init__(self, reddit_config: Dict, ai_config: Dict):
        """Initialize with API configurations"""
        self.scraper = RedditScraper(**reddit_config)
        self.analyzer = PersonaAnalyzer(**ai_config)
        
        # Create output directory
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_persona(self, url_or_username: str) -> str:
        """Generate complete user persona"""
        try:
            # Extract username
            username = self.scraper.extract_username(url_or_username)
            logger.info(f"Processing user: {username}")
            
            # Scrape Reddit data
            posts, comments = self.scraper.scrape_user_data(username)
            
            if not posts and not comments:
                raise ValueError(f"No content found for user {username}")
            
            # Prepare content for analysis
            content = self.analyzer.prepare_content_for_analysis(posts, comments)
            
            # Generate persona using AI
            persona = self.analyzer.analyze_persona(content, username)
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{username}_persona_{timestamp}.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"REDDIT USER PERSONA ANALYSIS\n")
                f.write(f"{'=' * 50}\n\n")
                f.write(f"Username: {username}\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Posts Analyzed: {len(posts)}\n")
                f.write(f"Comments Analyzed: {len(comments)}\n")
                f.write(f"\n{'=' * 50}\n\n")
                f.write(persona)
                f.write(f"\n\n{'=' * 50}\n")
                f.write("ANALYSIS COMPLETE\n")
            
            logger.info(f"Persona saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating persona: {e}")
            raise

def load_config() -> Tuple[Dict, Dict]:
    """Load API configurations from environment variables"""
    reddit_config = {
        'client_id': os.getenv('REDDIT_CLIENT_ID'),
        'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
        'user_agent': os.getenv('REDDIT_USER_AGENT', 'RedditPersonaAnalyzer/1.0')
    }

    ai_config = {
        'api_key': os.getenv('OPENROUTER_API_KEY'),
        'api_url': os.getenv('AI_API_URL', 'https://openrouter.ai/api/v1/chat/completions')
    }

    # Validate required configs early
    missing_configs = []
    for k, v in reddit_config.items():
        if not v:
            missing_configs.append(k.upper())
    for k, v in ai_config.items():
        if not v:
            missing_configs.append(k.upper())
    if missing_configs:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_configs)}")

    return reddit_config, ai_config

def main():
    """Main function"""
    try:
        print("Reddit User Persona Analyzer")
        print("=" * 40)

        # Load configurations once, validate early
        reddit_config, ai_config = load_config()

        # Get user input
        user_input = input("Enter Reddit username or profile URL: ").strip()
        if not user_input:
            print("Error: Please provide a username or URL")
            return

        # Initialize generator
        generator = PersonaGenerator(reddit_config, ai_config)

        # Generate persona
        print("\nGenerating persona... This may take a few minutes.")
        filepath = generator.generate_persona(user_input)

        print(f"\n✅ Persona analysis complete!")
        print(f"📄 Results saved to: {filepath}")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Error: {e}")
        print("Check the log file for more details.")

if __name__ == "__main__":
    main()

# Standalone OpenRouter API test
import requests
import os

api_key = os.getenv('OPENROUTER_API_KEY')
if api_key:
    # Example Reddit content for persona analysis
    sample_content = '''REDDIT USER CONTENT FOR ANALYSIS:

=== POSTS ===
POST 1:
Subreddit: r/delhi
Title: Real hiring or something fishy???
Content: Scam.
Score: 10
Link: https://reddit.com/r/delhi/comments/1lzqlj2/real_hiring_or_something_fishy/

=== COMMENTS ===
COMMENT 1:
Subreddit: r/nagpur
Content: I was caught without helmet and license. Cops outright wanted to fine me, but a 'common guy' came in and discussed bribe on my behalf with cops. I gave him 200rs and Cops let me go.
Score: 5
Link: https://reddit.com/r/nagpur/comments/1lyb0p5/a_very_odd_experience/
'''

    persona_prompt = f"""
    Analyze the following Reddit user's posts and comments to create a detailed user persona. 
    For the user 'sample_user', provide a comprehensive analysis including:
    1. PERSONALITY TRAITS - What kind of person are they? (e.g., introverted/extroverted, optimistic/pessimistic, analytical/creative, etc.)
    2. INTERESTS AND HOBBIES - What are they passionate about? What do they spend time on?
    3. WRITING STYLE - How do they communicate? (formal/casual, humorous/serious, detailed/brief, etc.)
    4. POSSIBLE DEMOGRAPHICS - Age estimate, location clues, profession hints, education level, etc.
    5. BEHAVIORAL PATTERNS - How do they interact on Reddit? What triggers their engagement?
    6. VALUES AND BELIEFS - What seems important to them based on their content?
    IMPORTANT: For EACH characteristic you identify, you MUST cite the specific post or comment that supports this conclusion. Use the format [CITATION: POST/COMMENT X - brief quote] after each trait.
    Format your response as a detailed user persona report with clear sections and citations.
    {sample_content}
    """

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek/deepseek-chat-v3-0324",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert social media analyst specializing in creating detailed user personas from social media content. Provide thorough, evidence-based analysis with specific citations."
                },
                {
                    "role": "user",
                    "content": persona_prompt
                }
            ]
        }
    )
    print("\nOpenRouter API test status:", response.status_code)
    try:
        result = response.json()
        print("\nOpenRouter API persona analysis output:\n")
        print(result['choices'][0]['message']['content'])
    except Exception as e:
        print("Error parsing response:", e)
        print(response.text)
else:
    print("\nOPENROUTER_API_KEY not set. Skipping OpenRouter API test.")
