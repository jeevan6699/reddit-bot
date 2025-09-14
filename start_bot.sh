#!/bin/bash

# Reddit Bot Startup Script

echo "Starting Reddit Bot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f "config/.env" ]; then
    echo "Configuration file not found!"
    echo "Please copy config/.env.example to config/.env and fill in your API keys"
    exit 1
fi

# Create necessary directories
mkdir -p logs
mkdir -p database
mkdir -p database/backups

# Start the bot
echo "Starting Reddit Bot with Web UI..."
echo "Web UI will be available at: http://localhost:5000"
python src/main.py