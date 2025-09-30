@echo off
REM 部署Worker启动脚本 (Windows版本)
REM 用于启动专门处理部署任务的Celery Worker

setlocal enabledelayedexpansion

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo === 部署Worker启动配置 ===
echo 工作目录: %SCRIPT_DIR%
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查Docker是否可用
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Docker未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查Docker daemon是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Docker daemon未运行
    pause
    exit /b 1
)

REM 设置环境变量
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"
if not defined DEPLOYMENT_BASE_PATH set "DEPLOYMENT_BASE_PATH=C:\opt\celery_deployments"

REM 创建部署基础目录
if not exist "%DEPLOYMENT_BASE_PATH%" mkdir "%DEPLOYMENT_BASE_PATH%"

echo Python版本:
python --version
echo Docker版本:
docker --version
echo 部署基础路径: %DEPLOYMENT_BASE_PATH%
echo.

REM 设置日志级别
if not defined LOG_LEVEL set "LOG_LEVEL=info"

echo 启动部署Worker...
echo 队列: deploy
echo 日志级别: %LOG_LEVEL%
echo.

REM 切换到脚本目录
cd /d "%SCRIPT_DIR%"

REM 启动部署Worker
python -m celery -A deploy_worker worker ^
    --loglevel=%LOG_LEVEL% ^
    --queues=deploy ^
    --concurrency=2 ^
    --hostname=deploy-worker@%%h ^
    --pidfile=%TEMP%\celery-deploy-worker.pid ^
    --logfile=%TEMP%\celery-deploy-worker.log

pause