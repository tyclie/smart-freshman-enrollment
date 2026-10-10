# 一键启动脚本（Windows PowerShell）
# 用法：在项目根目录执行 .\start.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "[1/4] 创建虚拟环境 ..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "[2/4] 安装依赖 ..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip -q
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt -q

if (-not (Test-Path "demo.db")) {
    Write-Host "[3/4] 初始化演示数据 ..." -ForegroundColor Cyan
    & ".\.venv\Scripts\python.exe" seed_data.py
} else {
    Write-Host "[3/4] 检测到 demo.db，跳过初始化（如需重置请执行 python seed_data.py）" -ForegroundColor Yellow
}

Write-Host "[4/4] 启动服务：http://127.0.0.1:5000" -ForegroundColor Green
& ".\.venv\Scripts\python.exe" app.py
