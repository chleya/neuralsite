#!/bin/bash
# =============================================================================
# NeuralSite 一键部署脚本
# Usage: ./deploy.sh [development|production]
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default environment
ENV=${1:-development}

# Project directories
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  NeuralSite Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${YELLOW}$ENV${NC}"
echo ""

# =============================================================================
# Pre-deployment checks
# =============================================================================
echo -e "${GREEN}[1/6] Running pre-deployment checks...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Use docker compose if available (V2)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo -e "${GREEN}  ✓ Docker and Docker Compose found${NC}"

# =============================================================================
# Build frontend
# =============================================================================
echo -e "${GREEN}[2/6] Building frontend...${NC}"

if [ -d "packages/studio" ]; then
    cd packages/studio
    if command -v npm &> /dev/null; then
        npm install --legacy-peer-deps
        npm run build
        echo -e "${GREEN}  ✓ Frontend built successfully${NC}"
    else
        echo -e "${YELLOW}  ⚠ npm not found, using pre-built dist${NC}"
    fi
    cd "$PROJECT_DIR"
else
    echo -e "${YELLOW}  ⚠ Frontend not found, skipping build${NC}"
fi

# =============================================================================
# Build backend Docker image
# =============================================================================
echo -e "${GREEN}[3/6] Building backend Docker image...${NC}"

# Copy frontend dist to backend static folder if exists
if [ -d "packages/studio/dist" ]; then
    mkdir -p packages/core/static
    cp -r packages/studio/dist/* packages/core/static/
    echo -e "${GREEN}  ✓ Frontend assets copied to backend${NC}"
fi

# Build Docker image
$DOCKER_COMPOSE build backend
echo -e "${GREEN}  ✓ Backend image built${NC}"

# =============================================================================
# Start services
# =============================================================================
echo -e "${GREEN}[4/6] Starting services...${NC}"

# Stop existing containers
$DOCKER_COMPOSE down 2>/dev/null || true

# Start infrastructure services first
$DOCKER_COMPOSE up -d postgres neo4j redis

# Wait for database to be ready
echo -e "${GREEN}  Waiting for PostgreSQL...${NC}"
sleep 10

# Start backend
$DOCKER_COMPOSE up -d backend

# Start nginx
$DOCKER_COMPOSE up -d nginx

echo -e "${GREEN}  ✓ All services started${NC}"

# =============================================================================
# Health checks
# =============================================================================
echo -e "${GREEN}[5/6] Running health checks...${NC}"

# Check nginx
if curl -s http://localhost/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Nginx is healthy${NC}"
else
    echo -e "${YELLOW}  ⚠ Nginx health check failed (may still be starting)${NC}"
fi

# Check backend (if exposed)
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Backend is healthy${NC}"
else
    echo -e "${YELLOW}  ⚠ Backend health check failed (may still be starting)${NC}"
fi

# =============================================================================
# Summary
# =============================================================================
echo -e "${GREEN}[6/6] Deployment complete!${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Service URLs:${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "  Frontend:    ${YELLOW}http://localhost${NC}"
echo -e "  API:         ${YELLOW}http://localhost/api${NC}"
echo -e "  Backend:     ${YELLOW}http://localhost:8000${NC}"
echo -e "  PostgreSQL:  ${YELLOW}localhost:5432${NC}"
echo -e "  Neo4j:       ${YELLOW}http://localhost:7474${NC}"
echo -e "  Redis:       ${YELLOW}localhost:6379${NC}"
echo ""
echo -e "${GREEN}  To view logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "${GREEN}  To stop:      ${YELLOW}docker-compose down${NC}"
echo ""
