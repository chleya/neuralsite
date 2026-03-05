# NeuralSite 系统监控脚本 (PowerShell)
# 监控 CPU, 内存, 磁盘使用情况
# 使用方法: .\monitor.ps1 [-Continuous] [-Interval Seconds]

param(
    [switch]$Continuous = $false,
    [int]$Interval = 5
)

$ErrorActionPreference = "Continue"

# 阈值配置
$CpuWarn = 70
$CpuCrit = 90
$MemWarn = 70
$MemCrit = 90
$DiskWarn = 70
$DiskCrit = 90

function Get-CpuUsage {
    $cpu = (Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue
    [Math]::Round($cpu, 1)
}

function Get-MemoryUsage {
    $os = Get-CimInstance Win32_OperatingSystem
    $total = $os.TotalVisibleMemorySize
    $free = $os.FreePhysicalMemory
    $used = $total - $free
    [Math]::Round(($used / $total) * 100, 1)
}

function Get-DiskUsage {
    $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='F:'" -ErrorAction SilentlyContinue
    if (!$disk) {
        $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction SilentlyContinue
    }
    if ($disk) {
        [Math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 1)
    } else {
        0
    }
}

function Get-MemoryInfo {
    $os = Get-CimInstance Win32_OperatingSystem
    $totalGB = [Math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
    $freeGB = [Math]::Round($os.FreePhysicalMemory / 1MB, 1)
    $usedGB = [Math]::Round($totalGB - $freeGB, 1)
    @{
        Used = $usedGB
        Total = $totalGB
    }
}

function Show-Monitor {
    param([string]$Title = "NeuralSite 系统监控")
    
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "时间: $(Get-Date)"
    Write-Host "主机: $env:COMPUTERNAME"
    Write-Host "========================================" -ForegroundColor Cyan
    
    # CPU
    $cpu = Get-CpuUsage
    $cpuColor = if ($cpu -ge $CpuCrit) { "Red" } elseif ($cpu -ge $CpuWarn) { "Yellow" } else { "Green" }
    $cpuStatus = if ($cpu -ge $CpuCrit) { "[CRITICAL]" } elseif ($cpu -ge $CpuWarn) { "[WARNING]" } else { "[OK]" }
    Write-Host -NoNewline "CPU:     "
    Write-Host "$cpu%" -ForegroundColor $cpuColor -NoNewline
    Write-Host " $cpuStatus"
    
    # Memory
    $mem = Get-MemoryUsage
    $memInfo = Get-MemoryInfo
    $memColor = if ($mem -ge $MemCrit) { "Red" } elseif ($mem -ge $MemWarn) { "Yellow" } else { "Green" }
    $memStatus = if ($mem -ge $MemCrit) { "[CRITICAL]" } elseif ($mem -ge $MemWarn) { "[WARNING]" } else { "[OK]" }
    Write-Host -NoNewline "内存:    "
    Write-Host "$mem% ($($memInfo.Used)GB / $($memInfo.Total)GB)" -ForegroundColor $memColor -NoNewline
    Write-Host " $memStatus"
    
    # Disk
    $disk = Get-DiskUsage
    $diskColor = if ($disk -ge $DiskCrit) { "Red" } elseif ($disk -ge $DiskWarn) { "Yellow" } else { "Green" }
    $diskStatus = if ($disk -ge $DiskCrit) { "[CRITICAL]" } elseif ($disk -ge $DiskWarn) { "[WARNING]" } else { "[OK]" }
    Write-Host -NoNewline "磁盘:    "
    Write-Host "$disk%" -ForegroundColor $diskColor -NoNewline
    Write-Host " $diskStatus"
    
    # Docker 容器
    Write-Host ""
    Write-Host "Docker 容器状态:" -ForegroundColor Cyan
    
    $containers = @("neuralsite-postgres", "neuralsite-neo4j", "neuralsite-redis")
    foreach ($container in $containers) {
        $status = docker ps --filter "name=$container" --format "{{.Status}}" 2>$null
        if ($status -match "Up") {
            Write-Host "  [OK] $container : $status" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] $container : 未运行" -ForegroundColor Red
        }
    }
    
    # 数据目录
    Write-Host ""
    Write-Host "数据目录使用:" -ForegroundColor Cyan
    
    $dirs = @{
        "PostgreSQL" = "F:\neuralsite\postgres-data"
        "Neo4j" = "F:\neuralsite\neo4j-data"
        "Redis" = "F:\neuralsite\redis-data"
    }
    
    foreach ($name in $dirs.Keys) {
        $path = $dirs[$name]
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
            Write-Host "  [OK] $name : $([Math]::Round($size, 1)) MB" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] $name : 不存在" -ForegroundColor Red
        }
    }
    
    Write-Host ""
}

# 主逻辑
if ($Continuous) {
    while ($true) {
        Show-Monitor
        Write-Host "刷新间隔: $Interval 秒 (Ctrl+C 退出)" -ForegroundColor Gray
        Start-Sleep -Seconds $Interval
    }
} else {
    Show-Monitor
}
