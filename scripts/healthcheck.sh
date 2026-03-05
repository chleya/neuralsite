#!/bin/bash
# NeuralSite 健康检查脚本
# 检查 PostgreSQL, Neo4j, Redis 服务状态
# 使用方法: ./healthcheck.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数
PASSED=0
FAILED=0

echo "========================================"
echo "NeuralSite 健康检查"
echo "时间: $(date)"
echo "========================================"

# 检查 PostgreSQL
echo -n "[PostgreSQL] "
if docker ps --filter "name=neuralsite-postgres" --filter "status=running" | grep -q neuralsite-postgres; then
    # 尝试执行SQL查询
    PGPASSWORD="password" psql -h localhost -U neuralsite -d neuralsite -c "SELECT 1;" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 运行正常${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ 连接失败${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗ 容器未运行${NC}"
    ((FAILED++))
fi

# 检查 Neo4j
echo -n "[Neo4j] "
if docker ps --filter "name=neuralsite-neo4j" --filter "status=running" | grep -q neuralsite-neo4j; then
    # Neo4j HTTP 健康检查
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then
        echo -e "${GREEN}✓ 运行正常 (HTTP: ${HTTP_STATUS})${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ 运行中但HTTP响应异常 (${HTTP_STATUS})${NC}"
        ((PASSED++))  # 容器运行就算通过
    fi
else
    echo -e "${RED}✗ 容器未运行${NC}"
    ((FAILED++))
fi

# 检查 Redis
echo -n "[Redis] "
if docker ps --filter "name=neuralsite-redis" --filter "status=running" | grep -q neuralsite-redis; then
    # Redis ping
    REDIS_PING=$(docker exec neuralsite-redis redis-cli ping 2>/dev/null || echo "FAILED")
    if [ "$REDIS_PING" = "PONG" ]; then
        echo -e "${GREEN}✓ 运行正常${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ 连接失败${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗ 容器未运行${NC}"
    ((FAILED++))
fi

# 检查数据目录
echo ""
echo "数据目录检查:"
for dir in "F:/neuralsite/postgres-data" "F:/neuralsite/neo4j-data" "F:/neuralsite/redis-data"; do
    if [ -d "$dir" ]; then
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "unknown")
        echo -e "  ${GREEN}✓${NC} $dir (${SIZE})"
    else
        echo -e "  ${RED}✗${NC} $dir (不存在)"
    fi
done

# 总结
echo ""
echo "========================================"
echo "健康检查总结: ${PASSED} 通过, ${FAILED} 失败"
echo "========================================"

# 返回状态码
if [ $FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi
