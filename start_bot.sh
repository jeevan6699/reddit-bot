#!/bin/bash

# Reddit Bot Menu Script
# Interactive menu with auto-start functionality and command-line arguments

set -e  # Exit on any error

# Parse command-line arguments
SKIP_MENU=false
ACTION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --service)
            SKIP_MENU=true
            ACTION="service"
            shift
            ;;
        --tests)
            SKIP_MENU=true
            ACTION="tests"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --service    Start the bot service directly"
            echo "  --tests      Run the test suite directly"
            echo "  --help, -h   Show this help message"
            echo ""
            echo "If no options are provided, an interactive menu will be shown."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Colors for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to display menu
show_menu() {
    clear
    echo -e "${CYAN}======================================${NC}"
    echo -e "${CYAN}       Reddit Bot Manager${NC}"
    echo -e "${CYAN}======================================${NC}"
    echo
    echo -e "${GREEN}Please select an option:${NC}"
    echo -e "${YELLOW}1.${NC} Start Bot Service"
    echo -e "${YELLOW}2.${NC} Proceed to Tests"
    echo -e "${YELLOW}3.${NC} Exit"
    echo
    echo -e "${BLUE}Auto-starting Bot Service in 15 seconds...${NC}"
    echo -e "${BLUE}Press any key to select manually.${NC}"
}

# Function to start bot service
start_bot() {
    echo
    echo -e "${GREEN}Starting Reddit Bot...${NC}"
    echo -e "${CYAN}==============================${NC}"
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}ERROR: Python 3 is not installed${NC}"
        echo -e "${YELLOW}Please install Python 3.8+ and try again${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Found: $(python3 --version)${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo -e "${RED}ERROR: Failed to create virtual environment${NC}"
            exit 1
        fi
    fi
    
    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    
    # Check if .env file exists
    if [ ! -f "config/.env" ]; then
        echo -e "${RED}ERROR: Configuration file config/.env not found!${NC}"
        echo -e "${YELLOW}Please copy config/.env.example to config/.env and configure your credentials${NC}"
        exit 1
    fi
    
    # Install/update requirements
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to install dependencies${NC}"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p logs database templates
    
    echo
    echo -e "${GREEN}Starting Reddit Bot with Web UI...${NC}"
    echo -e "${CYAN}Web UI will be available at: http://localhost:5000${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop the bot${NC}"
    echo
    
    # Start the bot
    python src/main.py
}

# Function to run tests
run_tests() {
    echo
    echo -e "${GREEN}Running Reddit Bot Tests...${NC}"
    echo -e "${CYAN}==============================${NC}"
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}ERROR: Python 3 is not installed${NC}"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Run tests
    if [ -f "tests/run_tests.py" ]; then
        python tests/run_tests.py
    else
        echo -e "${RED}ERROR: Test suite not found${NC}"
        echo -e "${YELLOW}Please ensure tests/run_tests.py exists${NC}"
    fi
    
    echo
    echo -e "${BLUE}Press Enter to return to menu...${NC}"
    read
}

# Function to handle timeout input with proper key detection
read_with_timeout() {
    local timeout=15
    local choice=""
    
    echo -e "${CYAN}Auto-starting Bot Service in ${timeout} seconds...${NC}"
    echo -e "${CYAN}Press 1, 2, or 3 to select an option:${NC}"
    
    # Count down with user input check
    for ((i=timeout; i>0; i--)); do
        printf "\r${CYAN}Starting in %2d seconds... (Press 1, 2, or 3)${NC}" $i
        
        # Check if input is available (non-blocking)
        if read -t 1 -n 1 choice 2>/dev/null; then
            echo  # New line after input
            case $choice in
                [123])
                    echo "$choice"
                    return 0
                    ;;
                *)
                    echo -e "\n${RED}Invalid choice '$choice'. Please press 1, 2, or 3${NC}"
                    choice=""
                    ;;
            esac
        fi
    done
    
    echo  # New line after countdown
    echo -e "${BLUE}Timeout reached. Starting Bot Service...${NC}"
    echo "1"  # Default to option 1
}

# Main menu loop
main() {
    # Handle command-line arguments
    if [ "$SKIP_MENU" = true ]; then
        case $ACTION in
            "service")
                start_bot
                exit 0
                ;;
            "tests")
                run_tests
                exit 0
                ;;
        esac
    fi
    
    # Interactive menu
    while true; do
        show_menu
        
        choice=$(read_with_timeout)
        
        case $choice in
            1)
                start_bot
                break
                ;;
            2)
                run_tests
                ;;
            3)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                # This should not happen with the new read_with_timeout function
                echo -e "${RED}Unexpected error. Starting Bot Service...${NC}"
                sleep 1
                start_bot
                break
                ;;
        esac
    done
}

# Run main function
main