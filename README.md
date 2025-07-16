# Reddit Persona Analyzer

This tool analyzes Reddit user profiles to create detailed personas based on their posts and comments.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up API Keys

#### Reddit API
1. Go to https://www.reddit.com/prefs/apps
2. Create a new application (script type)
3. Note down the client ID and client secret

#### OpenRouter API
1. Go to https://openrouter.ai/
2. Create an account and get your API key

### 3. Configure Environment Variables

Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```

Edit the `.env` file and add your API keys:
```
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=python:com.yourusername.redditbot:v0.1 (by u/yourusername)
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 4. Run the Application

**Main application (uses config.py):**
```bash
python main.py
```

**Simple version:**
```bash
python main3.py
```

## Files Description

- `main.py` - Full-featured version with comprehensive logging and configuration
- `main3.py` - Simplified version for quick testing
- `config.py` - Configuration management
- `.env` - Environment variables (create this file with your API keys)
- `.env.example` - Example environment file
- `requirements.txt` - Python dependencies

## Security Note

Never commit your `.env` file to version control. The `.env` file contains sensitive API keys.
