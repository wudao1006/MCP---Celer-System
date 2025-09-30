#!/bin/bash

# 部署Worker启动脚本
# 用于启动专门处理部署任务的Celery Worker

# 设置脚本严格模式
set -euo pipefail

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "错误: Python未安装或不在PATH中"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装或不在PATH中"
    exit 1
fi

# 检查Docker daemon是否运行
if ! docker info &> /dev/null; then
    echo "错误: Docker daemon未运行，请先启动Docker服务"
    echo "Ubuntu/Debian: sudo systemctl start docker"
    echo "CentOS/RHEL: sudo systemctl start docker"
    exit 1
fi

# 设置环境变量
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"
export DEPLOYMENT_BASE_PATH="${DEPLOYMENT_BASE_PATH:-/opt/celery_deployments}"

# 创建部署基础目录
sudo mkdir -p "$DEPLOYMENT_BASE_PATH"
sudo chown -R "$(whoami):$(whoami)" "$DEPLOYMENT_BASE_PATH" 2>/dev/null || true

echo "=== 部署Worker启动配置 ==="
echo "工作目录: $SCRIPT_DIR"
echo "部署基础路径: $DEPLOYMENT_BASE_PATH"
echo "Python命令: $PYTHON_CMD"
echo "Python版本: $($PYTHON_CMD --version)"
echo "Docker版本: $(docker --version)"
echo ""

# 检查deploy_worker.py是否存在
if [ ! -f "$SCRIPT_DIR/deploy_worker.py" ]; then
    echo "错误: deploy_worker.py 文件不存在"
    echo "请确保deploy_worker.py在当前目录中"
    exit 1
fi

# 设置日志级别
LOG_LEVEL="${LOG_LEVEL:-info}"

# 启动部署Worker
echo "启动部署Worker..."
echo "队列: deploy"
echo "日志级别: $LOG_LEVEL"
echo "使用Ctrl+C停止worker"
echo ""

# 启动Celery Worker
cd "$SCRIPT_DIR"
exec $PYTHON_CMD -m celery -A deploy_worker worker \
    --loglevel="$LOG_LEVEL" \
    --queues=deploy \
    --concurrency=2 \
    --hostname=deploy-worker@%h \
    --pidfile=/tmp/celery-deploy-worker.pid