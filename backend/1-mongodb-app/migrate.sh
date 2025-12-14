#!/bin/bash
# MongoDB to Elasticsearch Migration Script
# This script helps you migrate data from MongoDB to Elasticsearch

set -e  # Exit on error

echo "============================================================"
echo "MongoDB to Elasticsearch Migration"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Elasticsearch is running
echo "Checking Elasticsearch status..."
if curl -s http://localhost:9200 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Elasticsearch is running"
else
    echo -e "${RED}✗${NC} Elasticsearch is not running"
    echo ""
    echo "Starting Elasticsearch container..."
    docker-compose up -d elasticsearch
    
    echo "Waiting for Elasticsearch to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:9200 > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Elasticsearch is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    if ! curl -s http://localhost:9200 > /dev/null 2>&1; then
        echo -e "${RED}✗${NC} Elasticsearch failed to start"
        echo "Check logs with: docker logs es01"
        exit 1
    fi
fi

echo ""
echo "Elasticsearch info:"
curl -s http://localhost:9200 | grep -E '"name"|"version"' | head -2
echo ""

# Check Python environment
echo "Checking Python environment..."
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓${NC} uv found"
    
    # Navigate to backend directory
    cd "$(dirname "$0")/.."
    
    # Run migration
    echo ""
    echo "Starting migration..."
    echo "============================================================"
    uv run python -m 1-mongodb-app.migrate_to_elasticsearch
    
elif command -v poetry &> /dev/null; then
    echo -e "${GREEN}✓${NC} Poetry found"
    
    # Navigate to backend directory
    cd "$(dirname "$0")/.."
    
    # Run migration
    echo ""
    echo "Starting migration..."
    echo "============================================================"
    poetry run python -m 1-mongodb-app.migrate_to_elasticsearch
    
elif command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} uv/poetry not found, using python3 directly"
    
    cd "$(dirname "$0")/.."
    python3 -m 1-mongodb-app.migrate_to_elasticsearch
else
    echo -e "${RED}✗${NC} Python not found"
    echo "Please install Python 3.8+ and uv/poetry"
    exit 1
fi

echo ""
echo "============================================================"
echo -e "${GREEN}Migration Complete!${NC}"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. View data in Kibana: http://localhost:5601"
echo "2. Test search API: http://localhost:8000/docs"
echo "3. Try endpoints:"
echo "   - GET /search/songs?q=love"
echo "   - GET /search/songs/autocomplete?q=lo"
echo "   - GET /search/all?q=rock"
echo ""
