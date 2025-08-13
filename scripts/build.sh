#!/bin/bash
# scripts/build.sh - XploreML Build Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔨 Building XploreML...${NC}"

# Run tests
echo -e "${BLUE}🧪 Running tests...${NC}"


# Build Docker image
echo -e "${BLUE}🐳 Building Docker image...${NC}"
docker build -t xploreml:latest .

# Tag for GCR
if [ ! -z "$GCP_PROJECT_ID" ]; then
    echo -e "${BLUE}🏷️  Tagging for Google Container Registry...${NC}"
    docker tag xploreml:latest gcr.io/$GCP_PROJECT_ID/xploreml:latest
    docker tag xploreml:latest gcr.io/$GCP_PROJECT_ID/xploreml:$(git rev-parse --short HEAD)
fi

echo -e "${GREEN}✅ Build completed successfully!${NC}"

---
