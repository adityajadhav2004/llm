import os
import logging
from datetime import datetime
from typing import List, Tuple
from dataclasses import dataclass
import praw
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

@dataclass
class RedditContent:
    content_type: str
    title: str
    body: str
    score: int
    created_utc: float
    subreddit: str
    url: str
    permalink: str

class RedditScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    def extract_username(self, url_or_username: str) -> str:
        if url_or_username.startswith('http'):
            parsed = urlparse(url_or_username)
            path_parts = parsed.path.strip('/').split('/')
            if 'user' in path_parts:
                username_index = path_parts.index('user') + 1
                return path_parts[username_index]
            raise ValueError(f"Could not extract username from URL: {url_or_username}")
        else:
            return url_or_username.replace('u/', '').replace('/u/', '')

    def scrape_user_data(self, username: str, max_posts: int = 50, max_comments: int = 50) -> Tuple[List[RedditContent], List[RedditContent]]:
        user = self.reddit.redditor(username)
        posts = []
        comments = []
        logger.info(f"Scraping user: {username}")
        for submission in user.submissions.new(limit=max_posts):
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
        for comment in user.comments.new(limit=max_comments):
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
        return posts, comments

class PersonaAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "deepseek/deepseek-chat-v3-0324"

    def prepare_content(self, posts: List[RedditContent], comments: List[RedditContent]) -> str:
        content = "REDDIT USER CONTENT FOR ANALYSIS:\n\n"
        content += "=== POSTS ===\n"
        for i, post in enumerate(posts[:25], 1):
            content += f"\nPOST {i}:\nSubreddit: r/{post.subreddit}\nTitle: {post.title}\nContent: {post.body[:500]}\nScore: {post.score}\nLink: {post.permalink}\n"
        content += "\n=== COMMENTS ===\n"
        for i, comment in enumerate(comments[:25], 1):
            content += f"\nCOMMENT {i}:\nSubreddit: r/{comment.subreddit}\nContent: {comment.body[:300]}\nScore: {comment.score}\nLink: {comment.permalink}\n"
        return content

    def analyze_persona(self, username: str, content: str) -> str:
        prompt = f"""
        Analyze the following Reddit user's posts and comments to create a detailed user persona. 
        For the user '{username}', provide a comprehensive analysis including:
        1. PERSONALITY TRAITS
        2. INTERESTS AND HOBBIES
        3. WRITING STYLE
        4. POSSIBLE DEMOGRAPHICS
        5. BEHAVIORAL PATTERNS
        6. VALUES AND BELIEFS
        IMPORTANT: For EACH characteristic you identify, cite the specific post or comment that supports this conclusion.
        {content}
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert social media analyst."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        response = requests.post(self.api_url, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }, json=payload)
        if response.status_code != 200:
            logger.error(f"API error {response.status_code}: {response.text}")
            raise Exception(f"API error {response.status_code}: {response.text}")
        return response.json()['choices'][0]['message']['content']

def main():
    # Load API credentials from environment variables
    reddit_config = {
        'client_id': os.getenv('REDDIT_CLIENT_ID', ''),
        'client_secret': os.getenv('REDDIT_CLIENT_SECRET', ''),
        'user_agent': os.getenv('REDDIT_USER_AGENT', 'python:com.adityajadhav.myredditbot:v0.1 (by u/adityajadhav)')
    }
    api_key = os.getenv('OPENROUTER_API_KEY', '')
    
    # Validate that API keys are set
    if not reddit_config['client_id'] or not reddit_config['client_secret'] or not api_key:
        print("❌ Error: API credentials not found!")
        print("Please set the following environment variables in your .env file:")
        print("- REDDIT_CLIENT_ID")
        print("- REDDIT_CLIENT_SECRET") 
        print("- OPENROUTER_API_KEY")
        return

    scraper = RedditScraper(**reddit_config)
    analyzer = PersonaAnalyzer(api_key)

    user_input = input("Enter Reddit username or profile URL: ").strip()
    username = scraper.extract_username(user_input)

    posts, comments = scraper.scrape_user_data(username)
    content = analyzer.prepare_content(posts, comments)
    result = analyzer.analyze_persona(username, content)

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{username}_persona_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"Persona analysis complete. Results saved to {filepath}")

if __name__ == "__main__":
    main()
