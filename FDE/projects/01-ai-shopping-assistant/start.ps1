#Requires -Version 5.1
<#
.SYNOPSIS
    乐高智能导购助手 - Windows 11 一键启动脚本

.EXAMPLE
    .\start.ps1 local
    .\start.ps1 ingest
    .\start.ps1 docker
    .\start.ps1 stop
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet("local", "docker", "stop", "ingest", "help")]
    [string]$Command = "local"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

# 控制台统一 UTF-8，避免中文日志乱码
$env:PYTHONUTF8 = "1"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # 某些旧版 PowerShell 终端不支持，忽略即可
}

function Write-Info([string]$Message) { Write-Host "[INFO]  $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "[WARN]  $Message" -ForegroundColor Yellow }
function Write-Err([string]$Message)  { Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Step([string]$Message) { Write-Host "`n=== $Message ===" -ForegroundColor Cyan }

function Assert-Command([string]$Name, [string]$Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Err "未找到命令：$Name"
        Write-Host "  $Hint"
        exit 1
    }
}

function Ensure-EnvFile {
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Info "已从 .env.example 创建 .env"
    }
}

function Invoke-UvSync {
    Assert-Command "uv" "安装 uv：winget install --id astral-sh.uv -e"
    Write-Step "同步 Python 依赖"
    uv sync --extra dev
}

function Ensure-FrontendDeps {
    Assert-Command "npm" "安装 Node.js：winget install --id OpenJS.NodeJS.LTS -e"
    foreach ($dir in @("public", "admin")) {
        if (-not (Test-Path (Join-Path $dir "node_modules"))) {
            Write-Step "安装前端依赖：$dir"
            Push-Location $dir
            try { npm ci --no-audit --no-fund } finally { Pop-Location }
        }
    }
}

function Ensure-OllamaModel {
    if (-not (Get-Command "ollama" -ErrorAction SilentlyContinue)) {
        Write-Warn "未安装 Ollama：聊天功能不可用，但 API/前端仍可启动。"
        Write-Warn "安装：winget install --id Ollama.Ollama -e"
        return
    }

    try {
        $models = & ollama list 2>$null | Out-String
    } catch {
        $models = ""
    }

    $needed = @("qwen2.5:3b")
    if ((Get-Content ".env" -ErrorAction SilentlyContinue | Select-String "EMBED_PROVIDER=ollama")) {
        $needed += "bge-m3:latest"
    }

    foreach ($model in $needed) {
        if ($models -notmatch [regex]::Escape($model)) {
            Write-Step "拉取 Ollama 模型：$model"
            ollama pull $model
        }
    }
}

function Ensure-Data {
    Write-Step "初始化本地 SQLite 商品/库存数据"
    uv run python scripts/init_db.py

    $marker = Join-Path "db" ".ingest_hash"
    if (Test-Path ".env") {
        $embedLine = Get-Content ".env" | Select-String "^EMBED_PROVIDER=" | Select-Object -First 1
        if ($embedLine) {
            $provider = ($embedLine.Line -split "=", 2)[1].Trim()
            $marker = Join-Path "db" ".ingest_$provider"
        }
    }

    if (-not (Test-Path $marker)) {
        Write-Step "构建向量库（首次运行）"
        uv run python main.py ingest
    }
}

function Start-Local {
    Ensure-EnvFile
    Invoke-UvSync
    Ensure-FrontendDeps
    Ensure-OllamaModel
    Ensure-Data

    Write-Step "启动服务"
    Start-Process powershell -WorkingDirectory $ProjectRoot -ArgumentList @(
        "-NoExit", "-Command", '$env:PYTHONUTF8="1"; uv run python main.py serve'
    )

    Start-Process powershell -WorkingDirectory (Join-Path $ProjectRoot "public") -ArgumentList @(
        "-NoExit", "-Command", "npm run dev"
    )

    Start-Process powershell -WorkingDirectory (Join-Path $ProjectRoot "admin") -ArgumentList @(
        "-NoExit", "-Command", "npm run dev"
    )

    Start-Sleep -Seconds 4
    Write-Host ""
    Write-Info "后端 API:    http://localhost:8000"
    Write-Info "API 文档:    http://localhost:8000/docs"
    Write-Info "客户端聊天:  http://localhost:3000"
    Write-Info "客服端:      http://localhost:3001"
    Write-Host ""
    Write-Info "已在新窗口启动三个服务，关闭对应窗口即可停止。"
    Start-Process "http://localhost:3000"
}

function Start-Docker {
    Assert-Command "docker" "安装 Docker Desktop：winget install --id Docker.DockerDesktop -e"
    Write-Step "Docker Compose 启动"
    docker compose up -d --build
    Write-Host ""
    Write-Info "后端 API: http://localhost:8000"
    Write-Info "前端请本地启动：cd public; npm run dev"
    Write-Info "                cd admin;  npm run dev"
}

function Stop-Docker {
    if (Get-Command "docker" -ErrorAction SilentlyContinue) {
        docker compose down
        Write-Info "Docker 服务已停止"
    } else {
        Write-Warn "未安装 Docker，无需停止"
    }
}

function Invoke-Ingest {
    Ensure-EnvFile
    Invoke-UvSync
    Write-Step "重建向量库"
    uv run python main.py ingest
}

function Show-Help {
    @(
        "用法: .\start.ps1 [local|docker|stop|ingest|help]",
        "",
        "  local   默认，本地启动后端 + 客户端 + 客服端（推荐）",
        "  docker  使用 Docker Compose 启动后端",
        "  stop    停止 Docker 服务",
        "  ingest  重建向量库",
        "  help    显示帮助",
        "",
        "首次运行会自动：",
        "  1. 从 .env.example 生成 .env",
        "  2. uv sync 安装 Python 依赖",
        "  3. npm ci 安装两个前端依赖",
        "  4. 检查/拉取 Ollama 模型",
        "  5. 初始化 SQLite 并构建向量库"
    ) | ForEach-Object { Write-Host $_ }
}

switch ($Command) {
    "local"  { Start-Local }
    "docker" { Start-Docker }
    "stop"   { Stop-Docker }
    "ingest" { Invoke-Ingest }
    "help"   { Show-Help }
}
