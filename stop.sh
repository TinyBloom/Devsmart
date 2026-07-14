#!/bin/bash

# DevSmart 停止脚本

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "======================================"
echo "DevSmart 停止脚本"
echo "======================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 停止 Frontend
echo -e "${YELLOW}停止 Frontend...${NC}"
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID"
        echo -e "${GREEN}✓ Frontend 已停止 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}Frontend 进程不存在${NC}"
    fi
    rm -f logs/frontend.pid
else
    echo -e "${YELLOW}未找到 frontend.pid${NC}"
fi

# 停止 Backend
echo -e "${YELLOW}停止 Backend...${NC}"
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID"
        echo -e "${GREEN}✓ Backend 已停止 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${YELLOW}Backend 进程不存在${NC}"
    fi
    rm -f logs/backend.pid
else
    echo -e "${YELLOW}未找到 backend.pid${NC}"
fi

# 停止 Docker
echo -e "${YELLOW}停止 Docker (PostgreSQL)...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose down
    echo -e "${GREEN}✓ Docker 已停止${NC}"
else
    echo -e "${RED}docker-compose 未安装${NC}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✓ DevSmart 已完全停止${NC}"
echo "======================================"