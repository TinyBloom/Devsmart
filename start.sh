#!/bin/bash

# DevSmart 启动脚本
# 按 PRD 要求依次启动：Docker -> Backend -> Frontend

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "======================================"
echo "DevSmart 启动脚本"
echo "======================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 启动 Docker (PostgreSQL)
echo -e "${YELLOW}[1/3] 启动 Docker (PostgreSQL)...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
    echo -e "${GREEN}✓ PostgreSQL 已启动${NC}"
else
    echo -e "${RED}✗ docker-compose 未安装，请手动启动 PostgreSQL${NC}"
    exit 1
fi

# 等待 PostgreSQL 就绪
echo -e "${YELLOW}等待 PostgreSQL 就绪...${NC}"
sleep 3
until docker exec devsmart-postgres pg_isready -U devsmart -d devsmart &> /dev/null; do
    echo -e "${YELLOW}PostgreSQL 未就绪，等待中...${NC}"
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL 已就绪${NC}"

# 2. 启动 Backend (FastAPI)
echo -e "${YELLOW}[2/3] 启动 Backend (FastAPI)...${NC}"

# 创建 logs 目录（如果不存在）
mkdir -p "$PROJECT_ROOT/logs"

cd "$PROJECT_ROOT/backend"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}虚拟环境不存在，创建中...${NC}"
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/lib/python3.site-packages/fastapi" ]; then
    echo -e "${YELLOW}安装依赖...${NC}"
    pip install -r requirements.txt
fi

# 启动后端（后台运行，使用 unbuffered 模式）
echo -e "${GREEN}✓ 启动 FastAPI 服务 (http://localhost:8000)${NC}"
nohup python -u main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
echo -e "${GREEN}✓ Backend 已启动 (PID: $BACKEND_PID)${NC}"

cd "$PROJECT_ROOT"

# 3. 启动 Frontend (Vite)
echo -e "${YELLOW}[3/3] 启动 Frontend (Vite)...${NC}"
cd "$PROJECT_ROOT/frontend"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装前端依赖...${NC}"
    npm install
fi

# 启动前端（后台运行）
echo -e "${GREEN}✓ 启动 Vite 开发服务器 (http://localhost:5173)${NC}"
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
echo -e "${GREEN}✓ Frontend 已启动 (PID: $FRONTEND_PID)${NC}"

cd "$PROJECT_ROOT"

echo ""
echo "======================================"
echo -e "${GREEN}✓ DevSmart 启动完成！${NC}"
echo "======================================"
echo ""
echo "访问地址："
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "日志目录: $PROJECT_ROOT/logs/"
echo "  - backend.log"
echo "  - frontend.log"
echo ""
echo "停止服务: ./stop.sh"
echo "======================================"