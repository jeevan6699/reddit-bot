# Reddit Bot

A sophisticated Reddit bot that monitors subreddits and responds naturally using LLMs, with a focus on Gemini as the primary provider.

## Features

- **Smart Monitoring**: Monitors r/india and r/AskReddit for new posts hourly
- **Intelligent Filtering**: Advanced keyword-based post filtering with multiple match types
- **Natural Responses**: LLM-powered responses using Google Gemini (primary), with Claude and OpenAI as fallback options
- **Anti-Spam Controls**: Built-in rate limiting and spam prevention mechanisms
- **Comprehensive Logging**: SQLite database logging of all interactions and activities
- **Real-time Monitoring**: Minimal web UI for monitoring bot status and activity
- **Configurable**: Flexible YAML-based configuration system

## Project Structure

```
reddit-bot/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main bot entry point
│   ├── reddit_client.py     # Reddit API wrapper using PRAW
│   ├── llm_client.py        # LLM integration (Gemini primary)
│   ├── keyword_matcher.py   # Keyword detection and matching system
│   ├── database.py          # SQLite database operations
│   ├── web_ui.py           # Flask-based monitoring UI
│   └── utils.py            # Utility functions
├── config/
│   ├── settings.yaml       # Main bot configuration
│   ├── keywords.yaml       # Keyword rules and patterns
│   ├── .env.example        # Environment variables template
├── database/               # SQLite database and backups
├── logs/                   # Log files
├── requirements.txt        # Python dependencies
├── start_bot.sh           # Startup script
└── README.md
```

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd reddit-bot
   chmod +x start_bot.sh
   ```

2. **Configure Environment**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your API keys (see Configuration section)
   ```

3. **Run the Bot**
   ```bash
   ./start_bot.sh
   ```

4. **Access Web UI**
   - Open http://localhost:5000 in your browser
   - Monitor bot activity and control operation

## Configuration

### Required API Keys

#### Reddit API Setup
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" type
4. Note down the client ID and secret

#### Google Gemini API Setup (Primary)
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Add to your `.env` file

#### Optional Fallback Providers

**Claude (Anthropic)**
1. Go to https://console.anthropic.com/
2. Create an API key
3. Add to your `.env` file

**OpenAI**
1. Go to https://platform.openai.com/api-keys
2. Create an API key
3. Add to your `.env` file

### Environment Variables

Edit `config/.env` with your credentials:

```bash
# Reddit API (Required)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditBot/1.0 by /u/yourusername
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# Google Gemini API (Primary - Required)
GOOGLE_API_KEY=your_google_api_key

# Fallback Providers (Optional)
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Database and Logging
DATABASE_URL=sqlite:///./database/reddit_bot.db
LOG_LEVEL=INFO
LOG_FILE=./logs/reddit_bot.log
```

## Usage

### Starting the Bot
```bash
./start_bot.sh
```

### Web Interface
Access the monitoring interface at http://localhost:5000

**Features:**
- Real-time status monitoring
- Activity logs and statistics
- Bot control (start/stop/pause)
- Error tracking
- Configuration overview

### Manual Operation
```bash
# Activate virtual environment
source venv/bin/activate

# Run directly
python src/main.py
```

## Configuration Options

### Bot Settings (`config/settings.yaml`)
- **Subreddits**: Which subreddits to monitor
- **Check Interval**: How often to check for new posts
- **Rate Limits**: Maximum replies per hour
- **Response Settings**: Length limits and quality controls

### Keyword Rules (`config/keywords.yaml`)
- **India-specific topics**: High-priority Indian discussions
- **Help/Advice requests**: Medium-priority assistance posts
- **Technology discussions**: Medium-priority tech topics
- **Blacklist**: Topics to avoid completely

## Key Features in Detail

### Smart Keyword Matching
- **Multiple match types**: Exact, partial, and regex matching
- **Priority system**: High-priority topics get preference
- **Location-specific**: Match in title, body, or both
- **Blacklist filtering**: Automatically avoid sensitive topics

### LLM Integration
- **Primary provider**: Google Gemini (fast and cost-effective)
- **Automatic fallback**: Seamlessly switches to Claude or OpenAI if needed
- **Context-aware prompts**: Different templates for different topic types
- **Quality controls**: Response length and relevance checking

### Anti-Spam Measures
- **Rate limiting**: Maximum 3 replies per hour
- **Cooldown periods**: 10-minute minimum between replies
- **Post validation**: Avoids deleted, locked, or heavily downvoted posts
- **Duplicate prevention**: Tracks previously processed posts

### Comprehensive Logging
- **SQLite database**: Stores all interactions and metadata
- **Daily statistics**: Tracks performance metrics
- **Activity monitoring**: Real-time activity logging
- **Error tracking**: Detailed error logging and reporting

## Monitoring and Maintenance

### Web Dashboard
The built-in web interface provides:
- Current bot status and uptime
- Real-time statistics
- Recent activity feed
- Error logs
- Basic bot controls

### Log Files
- **Main log**: `logs/reddit_bot.log`
- **Database**: `database/reddit_bot.db`
- **Backups**: `database/backups/`

### Database Management
- Automatic cleanup of old data (30 days by default)
- Regular backups
- Performance optimization

## Safety and Compliance

### Reddit Guidelines
This bot is designed to:
- Respect Reddit's API rate limits
- Follow community guidelines
- Provide valuable contributions
- Avoid spammy behavior
- Maintain authentic interactions

### Content Safety
- Blacklist filtering for sensitive topics
- Quality scoring for responses
- Human-like response patterns
- Configurable safety thresholds

## Troubleshooting

### Common Issues

**Bot won't start**
- Check API credentials in `.env`
- Verify internet connection
- Check log files for errors

**No responses generated**
- Verify LLM API keys
- Check keyword configuration
- Review rate limiting settings

**Web UI not accessible**
- Ensure port 5000 is available
- Check firewall settings
- Verify Flask installation

### Log Analysis
```bash
# View recent logs
tail -f logs/reddit_bot.log

# Check for errors
grep -i error logs/reddit_bot.log

# Monitor database
sqlite3 database/reddit_bot.db ".tables"
```

## Development and Customization

### Adding New Keywords
Edit `config/keywords.yaml` to add new topics or modify priorities.

### Custom Response Templates
Modify the LLM templates in `src/llm_client.py` for different response styles.

### New LLM Providers
Extend the `BaseLLMClient` class to add support for additional providers.

### UI Customization
Modify `src/web_ui.py` to customize the monitoring interface.

## Legal and Ethical Considerations

- **Terms of Service**: Ensure compliance with Reddit's API terms
- **Community Guidelines**: Follow subreddit rules and Reddit policies
- **Rate Limiting**: Respect API limits and avoid excessive usage
- **Content Quality**: Provide valuable, relevant responses
- **Transparency**: Be open about bot nature if required by communities
- **Privacy**: Handle user data responsibly

## Support and Contributing

### Getting Help
1. Check the logs for error messages
2. Review configuration files
3. Verify API credentials and permissions
4. Check Reddit API status

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Version History

- **v1.0.0**: Initial release with Gemini integration, web UI, and comprehensive monitoring

---

**Important**: This bot is designed for educational and legitimate community engagement purposes. Use responsibly and in accordance with Reddit's terms of service and community guidelines.