# Celery代码部署系统

这是一个完整的Celery任务代码部署系统，支持将本地生成的代码文件夹部署到远程worker节点。

## 系统架构

```
用户本地 → 代码生成 → 部署调用 → 部署Worker → Docker构建 → 容器运行
```

## 文件说明

### 核心文件

- **`mcp_server.py`**: 主MCP服务器，包含 `deploy_task` 函数
- **`deploy_worker.py`**: 部署Worker，负责实际的代码部署操作
- **`start_deploy_worker.sh`**: Linux/Mac启动脚本
- **`start_deploy_worker.bat`**: Windows启动脚本
- **`deploy_worker_requirements.txt`**: 部署Worker的依赖包

### 主要功能

1. **`deploy_task`** (在 `mcp_server.py` 中)
   - 接收本地生成的代码文件夹路径
   - 调用部署Worker进行实际部署

2. **`deploy_code_folder`** (在 `deploy_worker.py` 中)
   - 上传代码文件夹到部署目录
   - 构建Docker镜像
   - 启动Celery Worker容器

3. **`stop_deployed_task`** (在 `deploy_worker.py` 中)
   - 停止指定的部署任务

4. **`list_deployed_tasks`** (在 `deploy_worker.py` 中)
   - 列出所有已部署的任务

## 使用流程

### 1. 环境准备

```bash
# 安装部署Worker依赖
pip install -r deploy_worker_requirements.txt

# 确保Docker已安装并运行
docker --version
docker info
```

### 2. 启动部署Worker

**Linux/Mac:**
```bash
chmod +x start_deploy_worker.sh
./start_deploy_worker.sh
```

**Windows:**
```cmd
start_deploy_worker.bat
```

### 3. 代码生成和部署

1. **生成代码**: 使用 `generate_celery_task_code` 提示词生成所有代码文件
2. **生成Dockerfile**: 为主启动文件生成对应的Dockerfile
3. **调用部署**: 使用 `deploy_task` 函数部署代码文件夹

```python
# 示例调用
result = await deploy_task(
    task_name="my_task",
    description="我的任务",
    parameters=[{"name": "input", "type": "str", "required": True}],
    queue="my_queue",
    category="general",
    code_folder_path="./generated_tasks/my_task_my_queue"
)
```

## 部署目录结构

```
/opt/celery_deployments/  (Linux)
C:\opt\celery_deployments\  (Windows)
├── task1_queue1_uuid1/
│   ├── app_queue1.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── 其他生成的文件...
├── task2_queue2_uuid2/
│   ├── app_queue2.py
│   ├── Dockerfile
│   └── ...
```

## 环境变量配置

可以通过环境变量配置系统行为：

```bash
# Redis配置
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=your_password
export REDIS_BROKER_DB=0
export REDIS_BACKEND_DB=1

# 部署配置
export DEPLOYMENT_BASE_PATH=/opt/celery_deployments
export LOG_LEVEL=info
```

## Docker容器管理

部署的任务会以Docker容器形式运行：

- **容器命名**: `{task_name}_{queue}_worker`
- **启动命令**: `celery -A app_{queue} worker -l info -Q {queue}`
- **自动重启**: `--restart unless-stopped`

### 查看容器状态

```bash
# 查看所有部署的容器
docker ps -f name=*_worker

# 查看容器日志
docker logs {container_name}

# 停止容器
docker stop {container_name}
```

## API接口

### deploy_task
```python
async def deploy_task(
    task_name: str,
    description: str,
    parameters: List[Dict[str, Any]],
    queue: str,
    category: str = "general",
    code_folder_path: str = None
) -> Dict[str, Any]
```

### deploy_code_folder (Celery任务)
```python
def deploy_code_folder(
    deployment_info: Dict[str, Any],
    task_info: Dict[str, Any]
) -> Dict[str, Any]
```

## 返回值示例

```json
{
    "success": true,
    "deployment_id": "uuid-string",
    "uploaded_files": ["app_queue.py", "Dockerfile", "requirements.txt"],
    "docker_image": "celery-my-task:deployment-id",
    "container_id": "container-id",
    "worker_status": "RUNNING",
    "deployment_path": "/opt/celery_deployments/my_task_queue_uuid",
    "message": "任务 my_task 部署成功"
}
```

## 错误处理

系统会处理以下常见错误：

1. **本地代码路径不存在**
2. **必要文件缺失** (主启动文件、Dockerfile)
3. **Docker镜像构建失败**
4. **容器启动失败**

所有错误都会在返回值中提供详细的错误信息和日志。

## 注意事项

1. **权限要求**: 运行部署Worker需要Docker操作权限
2. **磁盘空间**: 确保有足够的磁盘空间用于代码存储和Docker镜像
3. **网络连接**: 确保Redis和Docker registry网络连接正常
4. **资源限制**: 考虑设置适当的并发数量以避免资源耗尽

## 故障排除

### 常见问题

1. **Docker权限错误**
   ```bash
   sudo usermod -aG docker $USER
   # 重新登录或使用 newgrp docker
   ```

2. **Redis连接失败**
   - 检查Redis服务是否运行
   - 验证连接参数和密码

3. **容器启动失败**
   - 检查Dockerfile语法
   - 验证依赖包安装
   - 查看容器日志定位问题

4. **文件权限问题**
   ```bash
   sudo chown -R $USER:$USER /opt/celery_deployments
   ```

## 扩展功能

系统支持以下扩展：

1. **远程部署**: 通过SSH部署到远程服务器
2. **云存储**: 支持AWS S3、Azure Blob等云存储
3. **集群部署**: 支持Kubernetes等容器编排
4. **监控集成**: 集成Prometheus、Grafana等监控系统