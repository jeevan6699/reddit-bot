#!/usr/bin/env python3
"""Test Reddit authentication separately to diagnose issues."""

import os
import praw
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

def test_reddit_auth():
    """Test Reddit authentication with detailed error reporting."""
    
    print("🔍 Testing Reddit Authentication...")
    print("=" * 50)
    
    # Get credentials
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    username = os.getenv('REDDIT_USERNAME')
    password = os.getenv('REDDIT_PASSWORD')
    user_agent = os.getenv('REDDIT_USER_AGENT')
    
    # Check if credentials exist
    print(f"Client ID: {'✓' if client_id else '✗'} ({client_id[:8]}... if exists)")
    print(f"Client Secret: {'✓' if client_secret else '✗'} ({'*' * 8 if client_secret else 'Missing'})")
    print(f"Username: {'✓' if username else '✗'} ({username if username else 'Missing'})")
    print(f"Password: {'✓' if password else '✗'} ({'*' * len(password) if password else 'Missing'})")
    print(f"User Agent: {'✓' if user_agent else '✗'} ({user_agent if user_agent else 'Missing'})")
    print()
    
    if not all([client_id, client_secret, username, password, user_agent]):
        print("❌ Missing required credentials!")
        return False
    
    try:
        print("🔄 Attempting to authenticate with Reddit...")
        
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=username,
            password=password
        )
        
        print("🔄 Testing user authentication...")
        user = reddit.user.me()
        
        if user:
            print(f"✅ Successfully authenticated as: {user.name}")
            print(f"📊 Account details:")
            print(f"   - Karma: {user.link_karma + user.comment_karma}")
            print(f"   - Account created: {user.created_utc}")
            print(f"   - Verified: {'Yes' if user.verified else 'No'}")
            return True
        else:
            print("❌ Authentication returned None user")
            return False
            
    except Exception as e:
        error_str = str(e)
        print(f"❌ Authentication failed: {error_str}")
        print()
        print("🔧 Troubleshooting suggestions:")
        
        if "invalid_grant" in error_str:
            print("   1. Check username and password are correct")
            print("   2. Disable 2FA on your Reddit account")
            print("   3. Try creating a new Reddit app with 'script' type")
            print("   4. Make sure password doesn't have special characters")
            
        elif "invalid_client" in error_str:
            print("   1. Check CLIENT_ID and CLIENT_SECRET are correct")
            print("   2. Make sure the app type is 'script'")
            print("   3. Verify the app hasn't been deleted or suspended")
            
        elif "Forbidden" in error_str:
            print("   1. Account might be suspended or restricted")
            print("   2. Check if 2FA is enabled (must be disabled for bots)")
            
        else:
            print("   1. Check internet connection")
            print("   2. Verify Reddit isn't down")
            print("   3. Try recreating the Reddit app")
        
        return False

def test_api_keys():
    """Test LLM API keys."""
    print("\n🔍 Testing LLM API Keys...")
    print("=" * 50)
    
    google_key = os.getenv('GOOGLE_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"Google API Key: {'✓' if google_key and google_key != 'your_google_api_key_here' else '✗'}")
    print(f"Anthropic API Key: {'✓' if anthropic_key and anthropic_key != 'your_anthropic_api_key' else '✗'}")
    print(f"OpenAI API Key: {'✓' if openai_key and openai_key != 'your_openai_api_key' else '✗'}")
    
    if not any([
        google_key and google_key != 'your_google_api_key_here',
        anthropic_key and anthropic_key != 'your_anthropic_api_key',
        openai_key and openai_key != 'your_openai_api_key'
    ]):
        print("⚠️  No LLM API keys configured - bot won't generate responses")
        print("   Get a Google API key from: https://makersuite.google.com/app/apikey")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Reddit Bot Authentication Test")
    print("=" * 50)
    
    reddit_ok = test_reddit_auth()
    llm_ok = test_api_keys()
    
    print(f"\n📊 Summary:")
    print(f"Reddit Auth: {'✅ PASS' if reddit_ok else '❌ FAIL'}")
    print(f"LLM APIs: {'✅ PASS' if llm_ok else '⚠️ NEEDS SETUP'}")
    
    if reddit_ok and llm_ok:
        print("\n🎉 All tests passed! You can now run the bot.")
    else:
        print("\n🔧 Please fix the issues above before running the bot.")