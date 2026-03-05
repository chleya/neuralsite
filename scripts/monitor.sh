#!/bin/bash
# NeuralSite 系统监控脚本
# 监控 CPU, 内存, 磁盘使用情况
# 使用方法: ./monitor.sh [--continuous] [--interval SECONDS]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 阈值配置
CPU_WARN=70
CPU_CRIT=90
MEM_WARN=70
MEM_CRIT=90
DISK_WARN=70
DISK_CRIT=90

# 解析参数
CONTINUOUS=false
INTERVAL=5

while [[ $# -gt 0 ]]; do
    case $1 in
        --continuous)
            CONTINUOUS=true
            shift
            ;;
        --interval)
            INTERVAL=$2
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 获取系统信息
get_os_info() {
    echo "========================================"
    echo "NeuralSite 系统监控"
    echo "时间: $(date)"
    echo "主机: $(hostname)"
    echo "========================================"
}

# 监控 CPU
check_cpu() {
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    cpu_usage=${cpu_usage%.*}
    
    local color=$GREEN
    if [ "$cpu_usage" -ge "$CPU_CRIT" ]; then
        color=$RED
    elif [ "$cpu_usage" -ge "$CPU_WARN" ]; then
        color=$YELLOW
    fi
    
    printf "CPU:     ${color}%3d%%${NC}" "$cpu_usage"
    
    if [ "$cpu_usage" -ge "$CPU_CRIT" ]; then
        echo " [CRITICAL]"
        return 1
    elif [ "$cpu_usage" -ge "$CPU_WARN" ]; then
        echo " [WARNING]"
        return 0
    else
        echo " [OK]"
        return 0
    fi
}

# 监控内存
check_memory() {
    local mem_total mem_used mem_usage
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        mem_total=$(sysctl -n hw.memsize)
        mem_used=$(vm_stat | grep "Pages active" | awk '{print $3}' | tr -d '.')
        mem_used=$((mem_used * 4096))
    else
        # Linux/Windows Git Bash
        mem_total=$(free -b | grep Mem | awk '{print $2}')
        mem_used=$(free -b | grep Mem | awk '{print $3}')
    fi
    
    mem_usage=$((mem_used * 100 / mem_total))
    
    local color=$GREEN
    if [ "$mem_usage" -ge "$MEM_CRIT" ]; then
        color=$RED
    elif [ "$mem_usage" -ge "$MEM_WARN" ]; then
        color=$YELLOW
    fi
    
    local mem_used_gb=$(echo "scale=1; $mem_used / 1024 / 1024 / 1024" | bc)
    local mem_total_gb=$(echo "scale=1; $mem_total / 1024 / 1024 / 1024" | bc)
    
    printf "内存:    ${color}%3d%%${NC} (%.1fGB / %.1fGB)" "$mem_usage" "$mem_used_gb" "$mem_total_gb"
    
    if [ "$mem_usage" -ge "$MEM_CRIT" ]; then
        echo " [CRITICAL]"
        return 1
    elif [ "$mem_usage" -ge "$MEM_WARN" ]; then
        echo " [WARNING]"
        return 0
    else
        echo " [OK]"
        return 0
    fi
}

# 监控磁盘
check_disk() {
    local disk_usage
    disk_usage=$(df -h "F:" 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')
    
    if [ -z "$disk_usage" ]; then
        disk_usage=$(df -h "/" 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')
    fi
    
    local color=$GREEN
    if [ "$disk_usage" -ge "$DISK_CRIT" ]; then
        color=$RED
    elif [ "$disk_usage" -ge "$DISK_WARN" ]; then
        color=$YELLOW
    fi
    
    printf "磁盘:    ${color}%3d%%${NC}" "$disk_usage"
    
    if [ "$disk_usage" -ge "$DISK_CRIT" ]; then
        echo " [CRITICAL]"
        return 1
    elif [ "$disk_usage" -ge "$DISK_WARN" ]; then
        echo " [WARNING]"
        return 0
    else
        echo " [OK]"
        return 0
    fi
}

# 监控 Docker 容器
check_docker() {
    echo ""
    echo "Docker 容器状态:"
    
    local containers=("neuralsite-postgres" "neuralsite-neo4j" "neuralsite-redis")
    
    for container in "${containers[@]}"; do
        local status
        status=$(docker ps --filter "name=${container}" --format "{{.Status}}" 2>/dev/null || echo "未运行")
        
        if echo "$status" | grep -q "Up"; then
            echo -e "  ${GREEN}✓${NC} ${container}: ${status}"
        else
            echo -e "  ${RED}✗${NC} ${container}: ${status}"
        fi
    done
}

# 监控数据目录
check_data_dirs() {
    echo ""
    echo "数据目录使用:"
    
    local dirs=(
        "F:/neuralsite/postgres-data:PostgreSQL"
        "F:/neuralsite/neo4j-data:Neo4j"
        "F:/neuralsite/redis-data:Redis"
    )
    
    for item in "${dirs[@]}"; do
        local dir="${item%%:*}"
        local name="${item##*:}"
        
        if [ -d "$dir" ]; then
            local size
            size=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "unknown")
            echo -e "  ${GREEN}✓${NC} ${name}: ${size}"
        else
            echo -e "  ${RED}✗${NC} ${name}: 不存在"
        fi
    done
}

# 单次检查
run_check() {
    clear
    get_os_info
    check_cpu
    check_memory
    check_disk
    check_docker
    check_data_dirs
    echo ""
}

# 连续监控
run_continuous() {
    while true; do
        run_check
        echo "刷新间隔: ${INTERVAL}秒 (Ctrl+C 退出)"
        sleep "$INTERVAL"
    done
}

# 主逻辑
if [ "$CONTINUOUS" = true ]; then
    run_continuous
else
    run_check
fi
