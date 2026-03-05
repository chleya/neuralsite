#!/bin/bash
# NeuralSite 数据库备份脚本
# 备份 PostgreSQL + Neo4j 数据
# 使用方法: ./backup.sh

set -e

# 配置
BACKUP_DIR="F:/neuralsite/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="neuralsite_backup_${TIMESTAMP}"

# PostgreSQL 配置
PG_HOST="localhost"
PG_PORT="5432"
PG_USER="neuralsite"
PG_PASSWORD="password"
PG_DATABASE="neuralsite"

# Neo4j 配置
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="password"
NEO4J_DATA_DIR="F:/neuralsite/neo4j-data"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

echo "========================================"
echo "NeuralSite 数据库备份"
echo "时间: $(date)"
echo "========================================"

# 备份 PostgreSQL
echo "[1/2] 备份 PostgreSQL 数据库..."
PG_BACKUP_FILE="${BACKUP_DIR}/postgres_${BACKUP_NAME}.sql"

export PGPASSWORD="${PG_PASSWORD}"
pg_dump -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DATABASE}" -F c -b -v -f "${PG_BACKUP_FILE}"

if [ -f "${PG_BACKUP_FILE}" ]; then
    PG_SIZE=$(du -h "${PG_BACKUP_FILE}" | cut -f1)
    echo "  ✓ PostgreSQL 备份完成: ${PG_BACKUP_FILE} (${PG_SIZE})"
else
    echo "  ✗ PostgreSQL 备份失败"
    exit 1
fi

# 备份 Neo4j
echo "[2/2] 备份 Neo4j 数据..."
NEO4J_BACKUP_FILE="${BACKUP_DIR}/neo4j_${TIMESTAMP}.tar.gz"

# 停止 Neo4j 写入以确保一致性 (可选)
# docker stop neuralsite-neo4j 2>/dev/null || true

tar -czf "${NEO4J_BACKUP_FILE}" -C "$(dirname "${NEO4J_DATA_DIR}")" neo4j-data 2>/dev/null || {
    # 如果tar失败，尝试直接复制
    echo "  ! 使用备选备份方式..."
    cp -r "${NEO4J_DATA_DIR}" "${BACKUP_DIR}/neo4j_${TIMESTAMP}"
    NEO4J_BACKUP_FILE="${BACKUP_DIR}/neo4j_${TIMESTAMP}"
}

if [ -e "${NEO4J_BACKUP_FILE}" ]; then
    NEO4J_SIZE=$(du -h "${NEO4J_BACKUP_FILE}" | cut -f1)
    echo "  ✓ Neo4j 备份完成: ${NEO4J_BACKUP_FILE} (${NEO4J_SIZE})"
else
    echo "  ✗ Neo4j 备份失败"
fi

# 清理旧备份 (保留最近7天)
echo ""
echo "清理旧备份 (保留7天)..."
find "${BACKUP_DIR}" -name "neuralsite_backup_*" -mtime +7 -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "postgres_*.sql" -mtime +7 -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "neo4j_*.tar.gz" -mtime +7 -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "neo4j_*" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true

echo ""
echo "========================================"
echo "备份完成!"
echo "备份目录: ${BACKUP_DIR}"
echo "时间: $(date)"
echo "========================================"

# 列出最近备份
echo ""
echo "最近备份:"
ls -lh "${BACKUP_DIR}" | tail -5
