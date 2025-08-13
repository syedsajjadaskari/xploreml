#!/bin/bash
# scripts/setup.sh - XploreML Environment Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# XploreML ASCII Art
echo -e "${BLUE}"
cat << "EOF"
 __  __      _                 __  __ _     
|  \/  |    | |               |  \/  | |    
| \  / |    | |     ___  _ __ | \  / | |    
| |\/| |_  _| |    / _ \| '__|| |\/| | |    
| |  | | |_| | |  | (_) | |   | |  | | |____
|_|  |_|\__,_|_|   \___/|_|   |_|  |_|______|

XploreML - Learn, Experiment, and Discover Machine Learning without Code
EOF
echo -e "${NC}"

echo -e "${GREEN}🚀 Setting up XploreML development environment...${NC}"

# Check if Python 3.9+ is installed
echo -e "${BLUE}📋 Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo -e "${GREEN}✅ Python $python_version is installed${NC}"
else
    echo -e "${RED}❌ Python 3.9+ is required. Current version: $python_version${NC}"
    exit 1
fi

# Check if pip is installed
echo -e "${BLUE}📋 Checking pip installation...${NC}"
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✅ pip is installed${NC}"
else
    echo -e "${RED}❌ pip is required but not installed${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${BLUE}📦 Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "${BLUE}📦 Installing XploreML dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Install development dependencies if available
if [ -f "requirements-dev.txt" ]; then
    echo -e "${BLUE}📦 Installing development dependencies...${NC}"
    pip install -r requirements-dev.txt
    echo -e "${GREEN}✅ Development dependencies installed${NC}"
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating necessary directories...${NC}"
mkdir -p models logs data .streamlit
echo -e "${GREEN}✅ Directories created${NC}"

# Copy example config if it doesn't exist
if [ ! -f ".streamlit/config.toml" ]; then
    echo -e "${BLUE}⚙️  Creating Streamlit configuration...${NC}"
    cat > .streamlit/config.toml << EOF
[server]
port = 8501
address = "0.0.0.0"
maxUploadSize = 200

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#667eea"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
EOF
    echo -e "${GREEN}✅ Streamlit configuration created${NC}"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${BLUE}⚙️  Creating environment file...${NC}"
    cat > .env << EOF
# XploreML Environment Variables
APP_NAME=XploreML
APP_VERSION=2.0.0
ENVIRONMENT=development

# Google Cloud (Optional)
# GCS_TEMP_BUCKET=your-temp-bucket
# GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Streamlit Settings
STREAMLIT_SERVER_HEADLESS=false
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
EOF
    echo -e "${GREEN}✅ Environment file created${NC}"
fi

# Run basic health check
echo -e "${BLUE}🏥 Running health check...${NC}"
python3 -c "
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sklearn
print('✅ All core dependencies are working')
"

echo -e "${GREEN}🎉 XploreML setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo -e "  1. Activate virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "  2. Run XploreML: ${YELLOW}streamlit run app.py${NC}"
echo -e "  3. Open browser: ${YELLOW}http://localhost:8501${NC}"
echo ""
echo -e "${GREEN}🚀 Happy machine learning with XploreML!${NC}"

---
