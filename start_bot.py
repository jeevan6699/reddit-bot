#!/usr/bin/env python3
"""
Reddit Bot Python Startup Script
Cross-platform menu interface with timeout and command-line arguments
"""

import sys
import os
import subprocess
import time
import threading
import argparse
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

class BotManager:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.venv_path = self.script_dir / "venv"
        self.timeout_interrupted = False
        self.user_choice = None
        
    def colored_print(self, text, color=Colors.NC):
        """Print colored text"""
        print(f"{color}{text}{Colors.NC}")
        
    def show_menu(self):
        """Display the interactive menu"""
        os.system('clear' if os.name == 'posix' else 'cls')
        self.colored_print("=" * 40, Colors.CYAN)
        self.colored_print("       Reddit Bot Manager", Colors.CYAN)
        self.colored_print("=" * 40, Colors.CYAN)
        print()
        self.colored_print("Please select an option:", Colors.GREEN)
        self.colored_print("1. Start Bot Service", Colors.YELLOW)
        self.colored_print("2. Proceed to Tests", Colors.YELLOW)
        self.colored_print("3. Exit", Colors.YELLOW)
        print()
        
    def check_python(self):
        """Check if Python is available"""
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True, check=True)
            self.colored_print(f"Found: {result.stdout.strip()}", Colors.GREEN)
            return True
        except subprocess.CalledProcessError:
            self.colored_print("ERROR: Python is not working properly", Colors.RED)
            return False
            
    def setup_environment(self):
        """Set up virtual environment and dependencies"""
        os.chdir(self.script_dir)
        self.colored_print(f"Working directory: {self.script_dir}", Colors.BLUE)
        
        # Create virtual environment if it doesn't exist
        if not self.venv_path.exists():
            self.colored_print("Creating virtual environment...", Colors.BLUE)
            result = subprocess.run([sys.executable, '-m', 'venv', str(self.venv_path)])
            if result.returncode != 0:
                self.colored_print("ERROR: Failed to create virtual environment", Colors.RED)
                return False
                
        # Determine python executable in venv
        if os.name == 'nt':  # Windows
            python_exe = self.venv_path / "Scripts" / "python.exe"
            pip_exe = self.venv_path / "Scripts" / "pip.exe"
        else:  # Unix-like
            python_exe = self.venv_path / "bin" / "python"
            pip_exe = self.venv_path / "bin" / "pip"
            
        if not python_exe.exists():
            self.colored_print("ERROR: Virtual environment python not found", Colors.RED)
            return False
            
        # Check if .env file exists
        env_file = self.script_dir / "config" / ".env"
        if not env_file.exists():
            self.colored_print("ERROR: Configuration file config/.env not found!", Colors.RED)
            self.colored_print("Please copy config/.env.example to config/.env and configure your credentials", Colors.YELLOW)
            return False
            
        # Install/update dependencies
        self.colored_print("Installing dependencies...", Colors.BLUE)
        
        # Upgrade pip
        subprocess.run([str(pip_exe), 'install', '--upgrade', 'pip'], 
                      capture_output=True)
        
        # Install requirements
        result = subprocess.run([str(pip_exe), 'install', '-r', 'requirements.txt'])
        if result.returncode != 0:
            self.colored_print("ERROR: Failed to install dependencies", Colors.RED)
            return False
            
        # Create necessary directories
        for directory in ['logs', 'database', 'templates']:
            dir_path = self.script_dir / directory
            dir_path.mkdir(exist_ok=True)
            
        return True
        
    def start_bot(self):
        """Start the Reddit bot"""
        self.colored_print("Starting Reddit Bot...", Colors.CYAN)
        self.colored_print("=" * 30, Colors.CYAN)
        
        if not self.check_python():
            return False
            
        if not self.setup_environment():
            return False
            
        print()
        self.colored_print("Starting Reddit Bot with Web UI...", Colors.GREEN)
        self.colored_print("Web UI will be available at: http://localhost:5000", Colors.BLUE)
        self.colored_print("Press Ctrl+C to stop the bot", Colors.YELLOW)
        print()
        
        # Determine python executable in venv
        if os.name == 'nt':  # Windows
            python_exe = self.venv_path / "Scripts" / "python.exe"
        else:  # Unix-like
            python_exe = self.venv_path / "bin" / "python"
            
        # Start the bot
        try:
            result = subprocess.run([str(python_exe), 'src/main.py'])
            if result.returncode != 0:
                self.colored_print("ERROR: Failed to start bot", Colors.RED)
                return False
        except KeyboardInterrupt:
            self.colored_print("\nBot stopped by user", Colors.YELLOW)
            
        print()
        self.colored_print("Bot stopped.", Colors.BLUE)
        return True
        
    def run_tests(self):
        """Run the test suite"""
        self.colored_print("Running Test Suite...", Colors.CYAN)
        self.colored_print("=" * 30, Colors.CYAN)
        
        if not self.check_python():
            return False
            
        os.chdir(self.script_dir)
        
        # Create virtual environment if it doesn't exist
        if not self.venv_path.exists():
            self.colored_print("Creating virtual environment...", Colors.BLUE)
            result = subprocess.run([sys.executable, '-m', 'venv', str(self.venv_path)])
            if result.returncode != 0:
                self.colored_print("ERROR: Failed to create virtual environment", Colors.RED)
                return False
                
        # Determine pip executable in venv
        if os.name == 'nt':  # Windows
            python_exe = self.venv_path / "Scripts" / "python.exe"
            pip_exe = self.venv_path / "Scripts" / "pip.exe"
        else:  # Unix-like
            python_exe = self.venv_path / "bin" / "python"
            pip_exe = self.venv_path / "bin" / "pip"
            
        # Install test dependencies
        self.colored_print("Installing test dependencies...", Colors.BLUE)
        subprocess.run([str(pip_exe), 'install', '--upgrade', 'pip'], 
                      capture_output=True)
        subprocess.run([str(pip_exe), 'install', 'pytest', 'pytest-asyncio', 'pytest-mock'], 
                      capture_output=True)
        
        # Run tests
        print()
        self.colored_print("Running tests...", Colors.GREEN)
        result = subprocess.run([str(python_exe), '-m', 'pytest', 'tests/', '-v'])
        
        print()
        self.colored_print("Test run completed.", Colors.BLUE)
        return True
        
    def handle_timeout_input(self):
        """Handle user input during timeout"""
        try:
            choice = input().strip()
            if choice in ['1', '2', '3']:
                self.user_choice = choice
                self.timeout_interrupted = True
            elif choice:
                self.colored_print(f"Invalid choice '{choice}'. Please press 1, 2, or 3", Colors.RED)
        except (EOFError, KeyboardInterrupt):
            pass
            
    def read_with_timeout(self, timeout_seconds=15):
        """Read user input with timeout and countdown"""
        self.colored_print(f"Auto-starting Bot Service in {timeout_seconds} seconds...", Colors.CYAN)
        self.colored_print("Press 1, 2, or 3 to select an option:", Colors.CYAN)
        
        self.timeout_interrupted = False
        self.user_choice = None
        
        # Start input thread
        input_thread = threading.Thread(target=self.handle_timeout_input, daemon=True)
        input_thread.start()
        
        # Countdown with checking for input
        for i in range(timeout_seconds, 0, -1):
            if self.timeout_interrupted:
                return self.user_choice
                
            print(f"\rStarting in {i:2d} seconds... (Press 1, 2, or 3)", end='', flush=True)
            time.sleep(1)
            
        print()  # New line
        self.colored_print("Timeout reached. Starting Bot Service...", Colors.BLUE)
        return "1"  # Default to option 1
        
    def run_interactive_menu(self):
        """Run the interactive menu loop"""
        while True:
            self.show_menu()
            
            choice = self.read_with_timeout()
            
            if choice == "1":
                self.start_bot()
                break
            elif choice == "2":
                self.run_tests()
                print()
                self.colored_print("Press Enter to return to menu...", Colors.BLUE)
                input()
            elif choice == "3":
                self.colored_print("Goodbye!", Colors.GREEN)
                sys.exit(0)
            else:
                # This should not happen with the new timeout function
                self.colored_print("Unexpected error. Starting Bot Service...", Colors.RED)
                time.sleep(1)
                self.start_bot()
                break

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Reddit Bot Manager - Start bot or run tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_bot.py              # Show interactive menu
  python start_bot.py --service    # Start bot directly
  python start_bot.py --tests      # Run tests directly
        """
    )
    
    parser.add_argument('--service', action='store_true',
                       help='Start the bot service directly')
    parser.add_argument('--tests', action='store_true',
                       help='Run the test suite directly')
    
    args = parser.parse_args()
    
    bot_manager = BotManager()
    
    # Handle command-line arguments
    if args.service:
        bot_manager.start_bot()
    elif args.tests:
        bot_manager.run_tests()
    else:
        # Show interactive menu
        bot_manager.run_interactive_menu()

if __name__ == "__main__":
    main()