#!/usr/bin/env bash
# Codex-32 Setup Script - No Docker Required
# This script sets up Codex-32 for local development using the custom container engine

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Codex-32 AI Orchestration System - Local Setup            ║"
echo "║     Custom Container Engine (No Docker Required)              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}→ Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Found Python $python_version"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo -e "${RED}✗ Python 3.9+ is required${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version OK${NC}"
echo ""

# Check and create virtual environment
echo -e "${BLUE}→ Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "  Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${BLUE}→ Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install requirements
echo -e "${BLUE}→ Installing dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Create necessary directories
echo -e "${BLUE}→ Creating application directories...${NC}"
mkdir -p logs
mkdir -p bots
mkdir -p /tmp/codex32-containers
mkdir -p data
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Setup environment file
echo -e "${BLUE}→ Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    cp .env.template .env
    echo -e "${GREEN}✓ Created .env from template${NC}"
    echo -e "${YELLOW}  ⚠ Please edit .env and update sensitive values (passwords, keys)${NC}"
else
    echo -e "${YELLOW}  .env already exists (not overwriting)${NC}"
fi
echo ""

# Start database services (PostgreSQL)
echo -e "${BLUE}→ Checking database requirements...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL client found${NC}"
    
    if ! psql -U postgres -d codex32 -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${YELLOW}  ℹ PostgreSQL database 'codex32' not found${NC}"
        echo -e "${YELLOW}  Please ensure PostgreSQL is running and run: psql < database.sql${NC}"
    else
        echo -e "${GREEN}✓ PostgreSQL database 'codex32' is accessible${NC}"
    fi
else
    echo -e "${YELLOW}  ℹ PostgreSQL client not found${NC}"
    echo -e "${YELLOW}  Install PostgreSQL client or use your existing database connection${NC}"
fi
echo ""

# Start Redis
echo -e "${BLUE}→ Checking Redis requirement...${NC}"
if command -v redis-server &> /dev/null; then
    echo -e "${GREEN}✓ Redis found${NC}"
    if pgrep -x "redis-server" > /dev/null; then
        echo -e "${GREEN}✓ Redis is running${NC}"
    else
        echo -e "${YELLOW}  ℹ Redis not running. Start it with: redis-server${NC}"
    fi
else
    echo -e "${YELLOW}  ℹ Redis not found or not in PATH${NC}"
    echo -e "${YELLOW}  Install Redis: brew install redis (macOS) or apt-get install redis-server (Linux)${NC}"
fi
echo ""

# Initialize container storage
echo -e "${BLUE}→ Initializing custom container storage...${NC}"
CONTAINER_STORAGE="/tmp/codex32-containers"
mkdir -p "$CONTAINER_STORAGE"/{images,running}
echo -e "${GREEN}✓ Container storage ready at $CONTAINER_STORAGE${NC}"
echo ""

# Verify installation
echo -e "${BLUE}→ Verifying installation...${NC}"
python3 -c "
import sys
try:
    import fastapi
    import pydantic
    import psutil
    from app.config import settings
    from app.bot_registry import SecureRegistry
    from app.adaptive_executor import AdaptiveExecutor
    from app.container_engine import ContainerEngine
    print('✓ All required modules imported successfully')
    sys.exit(0)
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Installation verified${NC}"
else
    echo -e "${RED}✗ Installation verification failed${NC}"
    exit 1
fi
echo ""

# Installation complete
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  Setup Complete! 🎉                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${GREEN}Next steps:${NC}"
echo "1. Edit .env and update DATABASE_URL, REDIS_URL, and API keys"
echo "2. Start PostgreSQL and Redis (if not running)"
echo "3. Run the application:"
echo "   ${BLUE}python main.py${NC}"
echo "   or with uvicorn:"
echo "   ${BLUE}uvicorn main:app --reload${NC}"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "  - README.md ................... Project overview"
echo "  - GETTING_STARTED.md .......... Quick start guide"
echo "  - app/container_cli.py ........ CLI for container management"
echo ""
echo -e "${BLUE}Container Management:${NC}"
echo "  View all containers:"
echo "    ${BLUE}python -m app.container_cli list${NC}"
echo "  Create a container:"
echo "    ${BLUE}python -m app.container_cli create --name my-bot --image ./bots/sample_bot.py${NC}"
echo "  Start a container:"
echo "    ${BLUE}python -m app.container_cli start my-bot${NC}"
echo "  Inspect a container:"
echo "    ${BLUE}python -m app.container_cli inspect my-bot${NC}"
echo ""
