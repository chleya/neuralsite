# NeuralSite 数据库备份脚本 (PowerShell)
# 备份 PostgreSQL + Neo4j 数据

$ErrorActionPreference = "Stop"

# 配置
$BackupDir = "F:\neuralsite\backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupName = "neuralsite_backup_$Timestamp"

# PostgreSQL 配置
$PGHost = "localhost"
$PGPort = "5432"
$PGUser = "neuralsite"
$PGPassword = "password"
$PGDatabase = "neuralsite"

# Neo4j 数据目录
$Neo4jDataDir = "F:\neuralsite\neo4j-data"

# 创建备份目录
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NeuralSite 数据库备份" -ForegroundColor Cyan
Write-Host "时间: $(Get-Date)"
Write-Host "========================================" -ForegroundColor Cyan

# 备份 PostgreSQL
Write-Host "[1/2] 备份 PostgreSQL 数据库..." -ForegroundColor Yellow
$PGBackupFile = "$BackupDir\postgres_$Timestamp.sql"

$env:PGPASSWORD = $PGPassword
& pg_dump -h $PGHost -p $PGPort -U $PGUser -d $PGDatabase -F c -b -v -f $PGBackupFile 2>$null

if (Test-Path $PGBackupFile) {
    $PGSize = (Get-Item $PGBackupFile).Length / 1MB
    Write-Host "  [OK] PostgreSQL 备份完成: $PGBackupFile (${PGSize:N1} MB)" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] PostgreSQL 备份失败" -ForegroundColor Red
    exit 1
}

# 备份 Neo4j
Write-Host "[2/2] 备份 Neo4j 数据..." -ForegroundColor Yellow
$Neo4jBackupFile = "$BackupDir\neo4j_$Timestamp.zip"

try {
    Compress-Archive -Path $Neo4jDataDir -DestinationPath $Neo4jBackupFile -Force
    if (Test-Path $Neo4jBackupFile) {
        $Neo4jSize = (Get-Item $Neo4jBackupFile).Length / 1MB
        Write-Host "  [OK] Neo4j 备份完成: $Neo4jBackupFile (${Neo4jSize:N1} MB)" -ForegroundColor Green
    }
} catch {
    Write-Host "  [WARN] Neo4j 备份使用备选方式..." -ForegroundColor Yellow
    $Neo4jBackupDir = "$BackupDir\neo4j_$Timestamp"
    Copy-Item -Path $Neo4jDataDir -Destination $Neo4jBackupDir -Recurse -Force
    Write-Host "  [OK] Neo4j 备份完成: $Neo4jBackupDir" -ForegroundColor Green
}

# 清理旧备份 (保留7天)
Write-Host ""
Write-Host "清理旧备份 (保留7天)..." -ForegroundColor Yellow
$ cutoff = (Get-Date).AddDays(-7)
Get-ChildItem -Path $BackupDir -Recurse | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force -Recurse

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "备份完成!" -ForegroundColor Green
Write-Host "备份目录: $BackupDir"
Write-Host "========================================" -ForegroundColor Cyan

# 列出最近备份
Write-Host ""
Write-Host "最近备份:"
Get-ChildItem -Path $BackupDir | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
    $size = $_.Length / 1MB
    Write-Host "  $($_.Name) (${size:N1} MB)"
}
