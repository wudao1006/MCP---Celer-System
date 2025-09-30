# MCS (MCP-Celery System)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Celery](https://img.shields.io/badge/celery-5.0+-green.svg)](https://docs.celeryproject.org/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

> 🚀 **一个革命性的 AI Agent 自主任务管理系统** - 基于 MCP 和 Celery 打造，让 AI Agent 能够自动生成、部署、测试和调用分布式任务。

---

## 📋 目录

- [简介](#-简介)
- [核心特性](#-核心特性)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [详细使用指南](#-详细使用指南)
- [优势与特点](#-优势与特点)
- [使用场景](#-使用场景)
- [项目结构](#-项目结构)
- [配置说明](#-配置说明)
- [API 文档](#-api-文档)
- [最佳实践](#-最佳实践)
- [未来规划](#-未来规划)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🌟 简介

**MCS (MCP-Celery System)** 是一个创新的分布式任务管理系统，它将 **Model Context Protocol (MCP)** 与 **Celery** 深度集成，为 AI Agent 提供了完整的任务生命周期管理能力。

传统的任务系统需要人工编写代码、手动部署和配置。而 MCS 让 AI Agent 能够：

- 🤖 **自主生成代码** - 根据需求自动生成完整的 Celery 任务代码
- 🚀 **自动部署** - 一键部署到 Docker 容器化的 Worker 节点
- 🧪 **自我测试** - 部署后自动测试任务功能
- 📞 **动态调用** - 通过统一接口发现和调用任何已注册的任务
- 📊 **智能管理** - 自动维护任务元数据和分类信息

### 为什么选择 MCS？

在 AI Agent 时代，我们需要一个能够让 Agent **自主扩展能力**的系统。MCS 就是这样一个系统：

- ✅ **零人工干预** - Agent 可以自主完成从代码生成到部署的全流程
- ✅ **完全隔离** - 每个任务运行在独立的 Docker 容器中，互不影响
- ✅ **动态发现** - 新部署的任务立即可被其他 Agent 发现和使用
- ✅ **弹性扩展** - 支持水平扩展，轻松应对高并发场景
- ✅ **开箱即用** - 提供完整的模板和工具链，降低使用门槛

---

## ✨ 核心特性

### 1. 🔄 完整的任务生命周期管理

```
需求描述 → 代码生成 → 自动部署 → 容器化运行 → 功能测试 → 任务注册 → 动态调用
```

### 2. 🐳 Docker 容器化部署

- **自动构建镜像** - 根据代码自动生成 Dockerfile 并构建镜像
- **隔离运行环境** - 每个任务独立运行，资源隔离
- **自动重启** - 容器异常退出自动重启
- **环境变量注入** - 自动配置 Redis 等环境变量

### 3. 📦 智能任务注册与发现

- **Redis 元数据存储** - 任务信息、参数、分类统一存储
- **分类管理** - 支持任务分类，方便查询和管理
- **动态发现** - 新任务部署后立即可被发现
- **版本管理** - 支持任务更新和版本控制

### 4. 🎯 双模式任务执行

- **同步模式** (`trigger_celery_task`) - 等待任务完成并返回结果
- **异步模式** (`send_celery_task`) - 立即返回任务 ID，适合长时间任务

### 5. 🛠️ 强大的 MCP 工具集

| 工具名称 | 功能描述 |
|---------|---------|
| `generate_startMain_code` | 生成标准的 Celery 任务代码模板 |
| `deploy_task` | 一键部署代码到 Worker 节点 |
| `trigger_celery_task` | 同步执行任务并获取结果 |
| `send_celery_task` | 异步发送任务到队列 |
| `get_celery_result` | 查询任务执行结果 |
| `get_available_tasks` | 获取所有可用任务列表 |
| `get_task_details` | 获取任务详细信息 |
| `register_task_info` | 注册任务元数据到 Redis |

### 6. 🔧 灵活的配置系统

- **环境变量优先** - 支持通过环境变量覆盖配置
- **多队列支持** - 支持自定义队列，实现任务隔离
- **Redis 配置统一** - 统一的 Redis 配置管理

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI Agent (Claude)                       │
│                  通过 MCP 工具与系统交互                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Server (mcp_server.py)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Task Tools   │  │ Query Tools  │  │ Deploy Tools │           │
│  │ • trigger    │  │ • get_tasks  │  │ • deploy     │           │
│  │ • send       │  │ • get_result │  │ • generate   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└────────────┬────────────────────────────────────┬────────────────┘
             │                                    │
             ↓                                    ↓
┌────────────────────────────────┐   ┌────────────────────────────┐
│      Redis (消息代理 & 存储)    │   │  Deploy Worker (部署服务) │
│  • 任务队列 (Broker)            │   │  • 接收部署请求          │
│  • 结果后端 (Backend)           │   │  • 构建 Docker 镜像      │
│  • 任务元数据 (Metadata)        │   │  • 启动容器              │
└────────────┬───────────────────┘   └────────────────────────────┘
             │                                    │
             ↓                                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Celery Worker 集群 (Docker 容器)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Worker 1     │  │ Worker 2     │  │ Worker N     │           │
│  │ Queue: queue1│  │ Queue: queue2│  │ Queue: queueN│           │
│  │ • Task A     │  │ • Task C     │  │ • Task X     │           │
│  │ • Task B     │  │ • Task D     │  │ • Task Y     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 工作流程

1. **任务生成阶段**
   ```
   AI Agent → 描述需求 → generate_startMain_code → 生成代码模板 → 保存到本地
   ```

2. **部署阶段**
   ```
   AI Agent → deploy_task → 读取代码文件夹 → 发送到 Deploy Worker
   → Deploy Worker 接收 → 创建部署目录 → 写入文件
   → 构建 Docker 镜像 → 启动容器 → 返回部署结果
   ```

3. **测试阶段**
   ```
   AI Agent → trigger_celery_task → 发送测试任务 → Celery Worker 执行
   → 返回执行结果 → AI Agent 验证功能
   ```

4. **注册阶段**
   ```
   AI Agent → register_task_info → 写入 Redis → 任务可被发现和调用
   ```

5. **调用阶段**
   ```
   Any Agent → get_available_tasks → 发现任务
   → trigger_celery_task/send_celery_task → 执行任务
   → get_celery_result → 获取结果
   ```

---

## 🚀 快速开始

### 前置要求

- **Python 3.12+**
- **Docker** (用于容器化部署)
- **Redis** (消息代理和存储)

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/MCS.git
cd MCS
```

### 2. 安装依赖

```bash
# 安装主服务依赖
pip install -r requirement.txt

# 安装部署服务依赖
pip install -r deploy_mcp/deploy_worker_requirements.txt
```

### 3. 配置 Redis

⚠️ **重要：请勿直接修改示例文件，创建你自己的配置文件**

**方式 A：使用配置文件**

```bash
# 复制示例配置
cp Redis/redis_config.example.py Redis/redis_config.py

# 编辑配置文件
nano Redis/redis_config.py
```

修改为你的实际配置：
```python
def get_redis_config():
    return {
        "host": "your-redis-host",
        "port": 6379,
        "password": "your-secure-password",
        "db": 0,
        "decode_responses": True,
        "socket_timeout": 30,
        "socket_connect_timeout": 30,
        "retry_on_timeout": True
    }
```

**方式 B：使用环境变量（推荐）**

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

修改为你的实际配置：
```bash
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-secure-password
REDIS_BROKER_DB=0
REDIS_BACKEND_DB=1
```

### 4. 安全检查

在首次提交代码前，运行安全检查：

```bash
# Linux/Mac
chmod +x security_check.sh
./security_check.sh

# Windows
security_check.bat
```

### 5. 启动 Redis

```bash
# Linux/Mac
redis-server

# Docker（推荐）
docker run -d --name redis -p 6379:6379 redis:latest

# 如果需要密码
docker run -d --name redis -p 6379:6379 \
  --requirepass your-password \
  redis:latest
```

### 6. 启动部署 Worker

```bash
# Linux/Mac
cd deploy_mcp
chmod +x start_deploy_worker.sh
./start_deploy_worker.sh

# Windows
cd deploy_mcp
start_deploy_worker.bat
```

### 7. 启动 MCP 服务器

```bash
python mcp_server.py
```

### 8. 配置 Claude Desktop

在 Claude Desktop 的配置文件中添加 MCP 服务器：

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcs": {
      "command": "python",
      "args": ["C:/Users/YourUsername/Desktop/MCS/mcp_server.py"]
    }
  }
}
```

### 9. 测试系统

在 Claude Desktop 中：

```
请帮我创建一个简单的加法任务：
- 任务名称：simple_add
- 功能：接收两个数字并返回它们的和
- 队列：test_queue

然后部署并测试它。
```

Claude 将自动：
1. 生成代码
2. 创建 Dockerfile
3. 部署到 Worker 节点
4. 测试功能
5. 注册任务

---

## 📖 详细使用指南

### 完整工作流示例

#### 场景：创建一个 MongoDB 操作任务

**1. 描述需求**

```
我需要一个 MongoDB 操作 Worker，需要支持以下功能：
- 插入文档
- 查询文档
- 更新文档
- 删除文档

MongoDB 配置：
- host: localhost
- port: 27017
- database: mydb
```

**2. AI Agent 生成功能模块**

Agent 会根据需求生成 `mongodb_operations.py`：

```python
from pymongo import MongoClient

def get_mongo_client(host='localhost', port=27017, database='mydb'):
    client = MongoClient(host, port)
    return client[database]

def insert_document(collection_name, document):
    db = get_mongo_client()
    result = db[collection_name].insert_one(document)
    return str(result.inserted_id)

def find_documents(collection_name, query):
    db = get_mongo_client()
    documents = list(db[collection_name].find(query))
    return documents

# ... 其他函数
```

**3. 生成主启动文件**

Agent 调用 `generate_startMain_code`：

```python
await generate_startMain_code(
    task_name="mongodb_operation",
    description="MongoDB 数据库操作任务",
    parameters=[
        {"name": "operation", "type": "str", "required": True, "description": "操作类型：insert/find/update/delete"},
        {"name": "collection", "type": "str", "required": True, "description": "集合名称"},
        {"name": "data", "type": "dict", "required": True, "description": "操作数据"}
    ],
    function_body="""
    from mongodb_operations import insert_document, find_documents, update_document, delete_document

    if operation == 'insert':
        return insert_document(collection, data)
    elif operation == 'find':
        return find_documents(collection, data)
    elif operation == 'update':
        return update_document(collection, data.get('query'), data.get('update'))
    elif operation == 'delete':
        return delete_document(collection, data)
    else:
        raise ValueError(f"Unsupported operation: {operation}")
    """,
    queue="mongodb",
    return_type="Any",
    additional_files=[
        {"filename": "mongodb_operations.py", "content": "# 之前生成的代码"}
    ]
)
```

生成的模板会保存到 `./generated_tasks/mongodb_operation_mongodb/`。

**4. Agent 完善代码并创建 Dockerfile**

Agent 会创建完整的项目结构：

```
generated_tasks/mongodb_operation_mongodb/
├── app_mongodb.py          # 主启动文件
├── mongodb_operations.py    # 功能模块
├── requirements.txt         # 依赖包列表
└── Dockerfile              # Docker 构建文件
```

`Dockerfile` 示例：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "app_mongodb", "worker", "-l", "info", "-Q", "mongodb"]
```

**5. 部署到 Worker 节点**

Agent 调用 `deploy_task`：

```python
result = await deploy_task(
    task_name="mongodb_operation",
    description="MongoDB 数据库操作任务",
    parameters=[...],  # 同上
    queue="mongodb",
    category="database",
    code_folder_path="./generated_tasks/mongodb_operation_mongodb"
)
```

系统会：
- 读取代码文件夹中的所有文件
- 发送到 Deploy Worker
- 构建 Docker 镜像：`celery-mongodb-operation:uuid`
- 启动容器：`mongodb_operation_mongodb_worker`
- 自动注册任务到 Redis

**6. 测试功能**

Agent 调用 `trigger_celery_task` 测试：

```python
# 测试插入操作
result = await trigger_celery_task(
    task_name="mongodb_operation",
    kwargs={
        "operation": "insert",
        "collection": "users",
        "data": {"name": "Alice", "age": 30}
    },
    queue="mongodb"
)

# 测试查询操作
result = await trigger_celery_task(
    task_name="mongodb_operation",
    kwargs={
        "operation": "find",
        "collection": "users",
        "data": {"name": "Alice"}
    },
    queue="mongodb"
)
```

**7. 任务已可用**

其他 Agent 现在可以：

```python
# 发现任务
tasks = await get_available_tasks()
# 找到 mongodb_operation 任务

# 获取详细信息
details = await get_task_details("mongodb_operation")

# 使用任务
result = await trigger_celery_task(
    task_name="mongodb_operation",
    kwargs={...}
)
```

---

## 💡 优势与特点

### 1. 🤖 AI-Native 设计

- **为 AI Agent 而生** - 所有接口都设计为易于 Agent 理解和使用
- **自然语言驱动** - Agent 可以通过自然语言描述需求，系统自动完成实现
- **零学习成本** - Agent 无需了解 Celery 或 Docker 的复杂细节

### 2. 🔒 安全隔离

- **容器级隔离** - 每个任务运行在独立的 Docker 容器中
- **资源限制** - 可配置 CPU、内存等资源限制
- **网络隔离** - 支持自定义网络配置

### 3. 🚀 高性能

- **异步执行** - 基于 Celery 的分布式任务队列
- **并发控制** - 支持多 Worker 并发执行
- **结果缓存** - Redis 结果后端，快速查询任务结果

### 4. 📊 可观测性

- **完整日志** - Docker 容器日志记录所有执行过程
- **状态追踪** - 实时查询任务执行状态
- **元数据管理** - Redis 存储所有任务元信息

### 5. 🔧 易于扩展

- **模块化设计** - 各组件松耦合，易于替换和扩展
- **插件系统** - 支持自定义工具和钩子
- **多语言支持** - 理论上可支持任何语言的任务（通过 Docker）

### 6. 🌐 分布式架构

- **水平扩展** - 轻松添加更多 Worker 节点
- **负载均衡** - Celery 自动分配任务到可用 Worker
- **容错机制** - 任务失败自动重试

---

## 🎯 使用场景

### 1. 🤖 AI Agent 能力扩展

**场景**：AI Agent 需要动态获取新能力

```
Agent: "我需要能够处理 PDF 文件，提取文本和图片。"

MCS:
1. 生成 PDF 处理代码（使用 PyPDF2, pdf2image）
2. 部署为 pdf_processor 任务
3. Agent 立即可以调用该任务处理 PDF
```

**优势**：Agent 在运行时动态扩展能力，无需重启或人工干预。

### 2. 🔄 工作流自动化

**场景**：构建复杂的数据处理流水线

```python
# Agent 创建一系列任务
tasks = [
    "data_fetcher",      # 从 API 获取数据
    "data_cleaner",      # 清洗数据
    "data_analyzer",     # 分析数据
    "report_generator"   # 生成报告
]

# Agent 编排执行
data = await trigger_celery_task("data_fetcher", ...)
cleaned = await trigger_celery_task("data_cleaner", kwargs={"data": data})
analyzed = await trigger_celery_task("data_analyzer", kwargs={"data": cleaned})
report = await trigger_celery_task("report_generator", kwargs={"data": analyzed})
```

### 3. 🧪 快速原型开发

**场景**：快速验证想法

```
开发者: "帮我创建一个图片压缩服务"

MCS:
- 5分钟内生成代码
- 自动部署到容器
- 立即可用的 API 端点
```

**优势**：从想法到可用服务，几分钟内完成。

### 4. 🔌 微服务架构

**场景**：构建松耦合的微服务系统

- 每个服务作为独立的 Celery 任务
- 通过队列通信
- 独立部署和扩展

### 5. 📊 数据处理平台

**场景**：大规模数据 ETL

```python
# Agent 创建数据处理任务
tasks = {
    "csv_processor": "处理 CSV 文件",
    "json_processor": "处理 JSON 文件",
    "excel_processor": "处理 Excel 文件",
    "data_aggregator": "聚合多种数据源"
}

# 并行处理大量文件
for file in files:
    await send_celery_task(
        task_name=get_processor_for(file),
        kwargs={"file_path": file},
        queue="data_processing"
    )
```

### 6. 🌐 多租户 SaaS 平台

**场景**：为不同租户提供定制化服务

- 每个租户独立的任务队列
- 隔离的执行环境
- 灵活的资源分配

---

## 📁 项目结构

```
MCS/
├── mcp_server.py              # MCP 服务器主文件
├── mcp_app.py                 # Celery 应用配置
├── file_Reader.py             # 文件读取工具
├── requirement.txt            # 主要依赖
├── example_input.txt          # 使用示例
├── .mcp.json                  # MCP 配置文件
│
├── Redis/                     # Redis 相关模块
│   ├── redis_client.py        # Redis 客户端和任务管理
│   └── redis_config.py        # Redis 配置
│
├── deploy_mcp/                # 部署服务模块
│   ├── deploy_worker.py       # 部署 Worker 实现
│   ├── mcp_app.py             # 部署服务 Celery 配置
│   ├── deploy_worker_requirements.txt  # 部署服务依赖
│   ├── DEPLOYMENT_README.md   # 部署服务文档
│   ├── start_deploy_worker.sh # Linux/Mac 启动脚本
│   └── start_deploy_worker.bat # Windows 启动脚本
│
└── generated_tasks/           # 生成的任务代码（自动创建）
    └── {task_name}_{queue}/
        ├── app_{queue}.py     # 任务主文件
        ├── Dockerfile         # Docker 构建文件
        ├── requirements.txt   # 任务依赖
        └── ...                # 其他辅助文件
```

---

### Redis 配置

**方式 1：配置文件** (`Redis/redis_config.py`)

```python
DEFAULT_REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'password': 'your_password',
    'db': 0,
    'decode_responses': True
}
```

**方式 2：环境变量**（优先级更高）

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=your_password
export REDIS_BROKER_DB=0
export REDIS_BACKEND_DB=1
```

### Celery 配置

在 `mcp_app.py` 中：

```python
celery_app.conf.update(
    task_serializer='json',           # 任务序列化格式
    accept_content=['json'],          # 接受的内容类型
    result_serializer='json',         # 结果序列化格式
    timezone='UTC',                   # 时区
    enable_utc=True,                  # 启用 UTC
    worker_prefetch_multiplier=1,     # Worker 预取任务数
    task_acks_late=True,              # 任务完成后确认
    result_expires=3600,              # 结果过期时间（秒）
)
```

### Docker 配置

部署 Worker 自动配置以下环境变量：

```bash
REDIS_HOST
REDIS_PORT
REDIS_PASSWORD
REDIS_BROKER_DB
REDIS_BACKEND_DB
C_FORCE_ROOT=1  # 允许以 root 运行
```

---

## 📚 API 文档

### MCP 工具列表

#### 1. `generate_startMain_code`

生成 Celery 任务代码模板。

**参数**：
- `task_name` (str): 任务名称
- `description` (str): 任务描述
- `parameters` (List[Dict]): 参数列表
- `function_body` (str): 函数实现代码
- `queue` (str): 队列名称，默认 "celery"
- `return_type` (str): 返回类型，默认 "Any"
- `tasks` (List[Dict], 可选): 额外任务列表
- `additional_files` (List[Dict], 可选): 额外文件列表

**返回**：代码生成提示模板（字符串）

**示例**：
```python
prompt = generate_startMain_code(
    task_name="add_numbers",
    description="两数相加",
    parameters=[
        {"name": "a", "type": "int", "required": True, "description": "第一个数"},
        {"name": "b", "type": "int", "required": True, "description": "第二个数"}
    ],
    function_body="return a + b",
    queue="math",
    return_type="int"
)
```

#### 2. `deploy_task`

部署任务到 Worker 节点。

**参数**：
- `task_name` (str): 任务名称
- `description` (str): 任务描述
- `parameters` (List[Dict]): 参数列表
- `queue` (str): 队列名称
- `category` (str): 任务分类，默认 "general"
- `code_folder_path` (str, 可选): 代码文件夹路径

**返回**：部署结果（字典）

**示例**：
```python
result = await deploy_task(
    task_name="add_numbers",
    description="两数相加",
    parameters=[...],
    queue="math",
    category="arithmetic",
    code_folder_path="./generated_tasks/add_numbers_math"
)

# 返回示例
{
    "success": True,
    "deployment_id": "abc-123-def",
    "docker_image": "celery-add-numbers:abc-123-def",
    "container_id": "xyz789",
    "worker_status": "RUNNING",
    "message": "任务 add_numbers 代码文件夹已成功部署"
}
```

#### 3. `trigger_celery_task`

同步执行任务并等待结果。

**参数**：
- `task_name` (str): 任务名称
- `args` (list, 可选): 位置参数
- `kwargs` (dict, 可选): 关键字参数
- `queue` (str, 可选): 队列名称

**返回**：执行结果（字典）

**示例**：
```python
result = await trigger_celery_task(
    task_name="add_numbers",
    kwargs={"a": 10, "b": 20},
    queue="math"
)

# 返回示例
{
    "success": True,
    "task_id": "task-id-123",
    "task_name": "add_numbers",
    "queue": "math",
    "status": "PENDING",
    "message": "执行结果：30"
}
```

#### 4. `send_celery_task`

异步发送任务（不等待结果）。

**参数**：同 `trigger_celery_task`

**返回**：任务 ID（字典）

**示例**：
```python
result = await send_celery_task(
    task_name="long_running_task",
    kwargs={"data": "..."},
    queue="background"
)

# 返回示例
{
    "success": True,
    "task_id": "task-id-456",
    "task_name": "long_running_task",
    "queue": "background",
    "status": "SENT",
    "message": "任务已发送到队列 background，任务ID: task-id-456"
}
```

#### 5. `get_celery_result`

查询任务执行结果。

**参数**：
- `task_id` (str): 任务 ID

**返回**：任务状态和结果（字典）

**示例**：
```python
result = await get_celery_result("task-id-456")

# 返回示例（成功）
{
    "success": True,
    "task_id": "task-id-456",
    "status": "SUCCESS",
    "result": {"data": "..."},
    "message": "任务执行成功"
}

# 返回示例（进行中）
{
    "success": True,
    "task_id": "task-id-456",
    "status": "PENDING",
    "result": None,
    "message": "任务状态: PENDING"
}
```

#### 6. `get_available_tasks`

获取所有可用任务。

**参数**：无

**返回**：任务列表（字典）

**示例**：
```python
result = await get_available_tasks()

# 返回示例
{
    "success": True,
    "tasks": [
        {
            "name": "add_numbers",
            "description": "两数相加",
            "parameters": [...],
            "return_type": "int",
            "category": "arithmetic",
            "queue": "math",
            "created_at": "2025-01-15T10:00:00",
            "last_updated": "2025-01-15T10:00:00"
        },
        ...
    ],
    "total_count": 10,
    "message": "成功获取 10 个可用任务"
}
```

#### 7. `get_task_details`

获取任务详细信息。

**参数**：
- `task_name` (str): 任务名称

**返回**：任务详情（字典）

**示例**：
```python
result = await get_task_details("add_numbers")
```

#### 8. `register_task_info`

手动注册任务到 Redis。

**参数**：
- `task_name` (str): 任务名称
- `description` (str): 任务描述
- `parameters` (List[Dict]): 参数列表
- `return_type` (str): 返回类型，默认 "Any"
- `category` (str): 分类，默认 "general"
- `queue` (str): 队列，默认 "celery"

**返回**：注册结果（字典）

---

## 🎓 最佳实践

### 1. 任务命名规范

- 使用小写字母和下划线：`process_data`
- 使用动词开头：`fetch_users`, `generate_report`
- 明确任务用途：`mongodb_insert` 而不是 `db_op`

### 2. 队列组织

- 按功能分类：`database`, `processing`, `notification`
- 按优先级分类：`high_priority`, `normal`, `low_priority`
- 按资源需求分类：`cpu_intensive`, `io_intensive`

### 3. 错误处理

在任务中添加完善的错误处理：

```python
@celery_app.task(name='mcp_app.risky_task', queue='default')
def risky_task(data):
    try:
        # 任务逻辑
        result = process(data)
        return {"success": True, "result": result}
    except ValueError as e:
        # 参数错误
        return {"success": False, "error": "invalid_input", "message": str(e)}
    except Exception as e:
        # 其他错误
        return {"success": False, "error": "internal_error", "message": str(e)}
```

### 4. 任务超时设置

为长时间运行的任务设置超时：

```python
celery_app.conf.update(
    task_soft_time_limit=300,  # 5分钟软超时（抛出异常）
    task_time_limit=600,       # 10分钟硬超时（强制终止）
)
```

### 5. 资源清理

在任务结束时清理资源：

```python
@celery_app.task(name='mcp_app.file_processor', queue='processing')
def file_processor(file_path):
    temp_file = None
    try:
        # 处理文件
        temp_file = create_temp_file()
        result = process_file(file_path, temp_file)
        return result
    finally:
        # 确保清理临时文件
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
```

### 6. 任务幂等性

设计可重复执行的任务：

```python
@celery_app.task(name='mcp_app.update_user', queue='database')
def update_user(user_id, data):
    # 使用 upsert 而不是 insert
    db.users.update_one(
        {"_id": user_id},
        {"$set": data},
        upsert=True  # 不存在则创建
    )
```

### 7. 监控和日志

添加详细的日志：

```python
import logging
logger = logging.getLogger(__name__)

@celery_app.task(name='mcp_app.important_task', queue='critical')
def important_task(data):
    logger.info(f"开始处理任务，数据量: {len(data)}")

    try:
        result = process(data)
        logger.info(f"任务完成，结果: {result}")
        return result
    except Exception as e:
        logger.error(f"任务失败: {e}", exc_info=True)
        raise
```

---

## 🔮 可拓展方向

- [ ] **Web 管理界面** - 可视化管理任务和监控执行状态
- [ ] **任务版本管理** - 支持任务的多版本共存和灰度发布
- [ ] **性能监控** - 集成 Prometheus + Grafana 监控
- [ ] **任务依赖管理** - 支持任务间的依赖关系
- [ ] **自动重试策略** - 智能的任务重试和降级机制
- [ ] **Kubernetes 支持** - 基于 K8s 的容器编排
- [ ] **多语言支持** - 支持 Node.js, Go, Java 等语言编写任务
- [ ] **任务市场** - 社区共享的任务模板市场
- [ ] **A/B 测试** - 支持任务的 A/B 测试
- [ ] **智能调度** - 基于负载的智能任务调度
- [ ] **联邦学习支持** - 支持分布式机器学习任务
- [ ] **边缘计算** - 支持在边缘节点部署任务
- [ ] **多云部署** - 支持 AWS, Azure, GCP 等云平台
- [ ] **自动扩缩容** - 基于负载自动扩缩容 Worker
- [ ] **AI 辅助优化** - AI 自动优化任务代码和配置

---

## 📄 许可证

本项目采用 **MIT License** - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- **Anthropic** - Claude AI 和 MCP 协议
- **Celery** - 强大的分布式任务队列
- **Redis** - 高性能的内存数据库
- **Docker** - 容器化技术
- **开源社区** - 所有贡献者和用户

---

## 🌟 Star History

如果这个项目对你有帮助，请给我们一个 Star ⭐！

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/MCS&type=Date)](https://star-history.com/#yourusername/MCS&Date)

---

<div align="center">

**[⬆ 回到顶部](#mcs-mcp-celery-system)**

Made with ❤️ by the MCS Team


</div>
