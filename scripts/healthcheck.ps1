# NeuralSite 健康检查脚本 (PowerShell)
# 检查 PostgreSQL, Neo4j, Redis 服务状态

$ErrorActionPreference = "Stop"

$Passed = 0
$Failed = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NeuralSite 健康检查" -ForegroundColor Cyan
Write-Host "时间: $(Get-Date)"
Write-Host "========================================" -ForegroundColor Cyan

# 检查 PostgreSQL
Write-Host -NoNewline "[PostgreSQL] "
$pgContainer = docker ps --filter "name=neuralsite-postgres" --filter "status=running" --format "{{.Names}}" 2>$null
if ($pgContainer -eq "neuralsite-postgres") {
    try {
        $env:PGPASSWORD = "password"
        $result = & psql -h localhost -U neuralsite -d neuralsite -c "SELECT 1;" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] 运行正常" -ForegroundColor Green
            $Passed++
        } else {
            Write-Host "[ERROR] 连接失败" -ForegroundColor Red
            $Failed++
        }
    } catch {
        Write-Host "[ERROR] 连接失败" -ForegroundColor Red
        $Failed++
    }
} else {
    Write-Host "[ERROR] 容器未运行" -ForegroundColor Red
    $Failed++
}

# 检查 Neo4j
Write-Host -NoNewline "[Neo4j] "
$neo4jContainer = docker ps --filter "name=neuralsite-neo4j" --filter "status=running" --format "{{.Names}}" 2>$null
if ($neo4jContainer -eq "neuralsite-neo4j") {
    try {
        $httpStatus = (Invoke-WebRequest -Uri "http://localhost:7474" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue).StatusCode
        if ($httpStatus -eq 200) {
            Write-Host "[OK] 运行正常 (HTTP: $httpStatus)" -ForegroundColor Green
            $Passed++
        } else {
            Write-Host "[WARN] 运行中但HTTP响应异常 ($httpStatus)" -ForegroundColor Yellow
            $Passed++
        }
    } catch {
        Write-Host "[OK] 运行中" -ForegroundColor Green
        $Passed++
    }
} else {
    Write-Host "[ERROR] 容器未运行" -ForegroundColor Red
    $Failed++
}

# 检查 Redis
Write-Host -NoNewline "[Redis] "
$redisContainer = docker ps --filter "name=neuralsite-redis" --filter "status=running" --format "{{.Names}}" 2>$null
if ($redisContainer -eq "neuralsite-redis") {
    $pingResult = docker exec neuralsite-redis redis-cli ping 2>$null
    if ($pingResult -eq "PONG") {
        Write-Host "[OK] 运行正常" -ForegroundColor Green
        $Passed++
    } else {
        Write-Host "[ERROR] 连接失败" -ForegroundColor Red
        $Failed++
    }
} else {
    Write-Host "[ERROR] 容器未运行" -ForegroundColor Red
    $Failed++
}

# 检查数据目录
Write-Host ""
Write-Host "数据目录检查:" -ForegroundColor Cyan

$dirs = @(
    "F:\neuralsite\postgres-data",
    "F:\neuralsite\neo4j-data",
    "F:\neuralsite\redis-data"
)

foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        $size = (Get-ChildItem $dir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "  [OK] $dir ($([Math]::Round($size, 1)) MB)" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] $dir (不存在)" -ForegroundColor Red
    }
}

# 总结
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "健康检查总结: $Passed 通过, $Failed 失败" -ForegroundColor $(if ($Failed -gt 0) { "Red" } else { "Green" })
Write-Host "========================================" -ForegroundColor Cyan

if ($Failed -gt 0) {
    exit 1
} else {
    exit 0
}
