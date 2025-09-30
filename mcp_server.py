#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import httpx
import json
from typing import Any, Dict, Optional, List
from mcp.server.fastmcp import FastMCP
from mcp_app import celery_app
from Redis.redis_client import get_redis_client, get_all_tasks, get_tasks_by_category, get_all_categories, register_celery_task, get_task_info

# 创建MCP服务器
mcp = FastMCP("Demo")

# Redis客户端
redis_client = get_redis_client()

# 简单加法工具
@mcp.tool()
def add(a: int, b: int) -> int:
    """两数相加"""
    return a + b

# Celery任务触发器（同步执行，等待结果）
@mcp.tool()
async def trigger_celery_task(task_name: str, args: Optional[list] = None, kwargs: Optional[Dict[str, Any]] = None, queue: Optional[str] = None) -> Dict[str, Any]:
    """
    触发一次完整的远程Celery任务，并获取对应结果

    Args:
        task_name: Celery任务名称 (例如: 'myapp.tasks.process_data')
        args: 位置参数列表
        kwargs: 关键字参数字典
        queue: 指定队列（可选，不指定则从Redis获取）

    Returns:
        包含任务ID和状态信息的字典
    """
    try:
        args = args or []
        kwargs = kwargs or {}

        # 如果没指定队列，从Redis获取任务信息中的队列
        if not queue:
            task_info = get_task_info(redis_client, task_name)
            if task_info:
                queue = task_info.get('queue', 'celery')
            else:
                queue = 'celery'  # 默认队列

        # 异步触发任务
        task = celery_app.send_task('mcp_app.'+task_name, args=args, kwargs=kwargs, queue=queue)
        result=task.get()
        return {
            "success": True,
            "task_id": task.id,
            "task_name": task_name,
            "queue": queue,
            "status": "PENDING",
            "message": f"执行结果：{result}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"提交任务失败: {e}"
        }

# 异步发送Celery任务（不等待结果）
@mcp.tool()
async def send_celery_task(task_name: str, args: Optional[list] = None, kwargs: Optional[Dict[str, Any]] = None, queue: Optional[str] = None) -> Dict[str, Any]:
    """
    异步发送Celery任务（不等待结果，适用于长时间运行的任务）

    Args:
        task_name: Celery任务名称 (例如: 'myapp.tasks.process_data')
        args: 位置参数列表
        kwargs: 关键字参数字典
        queue: 指定队列（可选，不指定则从Redis获取）

    Returns:
        包含任务ID的字典
    """
    try:
        args = args or []
        kwargs = kwargs or {}

        # 如果没指定队列，从Redis获取任务信息中的队列
        if not queue:
            task_info = get_task_info(redis_client, task_name)
            if task_info:
                queue = task_info.get('queue', 'celery')
            else:
                queue = 'celery'  # 默认队列

        # 异步发送任务，不等待结果
        task = celery_app.send_task('mcp_app.'+task_name, args=args, kwargs=kwargs, queue=queue)

        return {
            "success": True,
            "task_id": task.id,
            "task_name": task_name,
            "queue": queue,
            "status": "SENT",
            "message": f"任务已发送到队列 {queue}，任务ID: {task.id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"发送任务失败: {e}"
        }

# 查询Celery任务结果
@mcp.tool()
async def get_celery_result(task_id: str) -> Dict[str, Any]:
    """
    查询Celery任务的执行结果

    Args:
        task_id: 任务ID

    Returns:
        包含任务状态和结果的字典
    """
    try:
        # 根据任务ID获取任务状态
        task_result = celery_app.AsyncResult(task_id)

        result_info = {
            "success": True,
            "task_id": task_id,
            "status": task_result.status,
            "result": None,
            "error": None
        }

        if task_result.ready():
            if task_result.successful():
                result_info["result"] = task_result.result
                result_info["message"] = "任务执行成功"
            else:
                result_info["error"] = str(task_result.info)
                result_info["message"] = "任务执行失败"
        else:
            result_info["message"] = f"任务状态: {task_result.status}"

        return result_info

    except Exception as e:
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e),
            "message": f"查询任务结果失败: {e}"
        }

# 获取所有可用的Celery任务信息
@mcp.tool()
async def get_available_tasks() -> Dict[str, Any]:
    """
    从Redis获取所有可用的Celery任务信息

    Returns:
        包含所有可用任务信息的字典
    """
    try:
        if not redis_client:
            return {
                "success": False,
                "error": "Redis连接不可用",
                "tasks": [],
                "message": "无法连接到Redis服务器"
            }

        tasks = get_all_tasks(redis_client)

        return {
            "success": True,
            "tasks": tasks,
            "total_count": len(tasks),
            "message": f"成功获取 {len(tasks)} 个可用任务"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tasks": [],
            "message": f"获取任务列表失败: {e}"
        }

# 根据分类获取任务信息
@mcp.tool()
async def get_tasks_by_category_name(category: str) -> Dict[str, Any]:
    """
    根据分类获取Celery任务信息

    Args:
        category: 任务分类名称

    Returns:
        包含该分类下任务信息的字典
    """
    try:
        if not redis_client:
            return {
                "success": False,
                "error": "Redis连接不可用",
                "tasks": [],
                "message": "无法连接到Redis服务器"
            }

        tasks = get_tasks_by_category(redis_client, category)

        return {
            "success": True,
            "tasks": tasks,
            "category": category,
            "count": len(tasks),
            "message": f"成功获取分类 '{category}' 下的 {len(tasks)} 个任务"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tasks": [],
            "message": f"获取分类任务失败: {e}"
        }

# 获取所有任务分类
@mcp.tool()
async def get_task_categories() -> Dict[str, Any]:
    """
    获取所有任务分类

    Returns:
        包含所有分类信息的字典
    """
    try:
        if not redis_client:
            return {
                "success": False,
                "error": "Redis连接不可用",
                "categories": [],
                "message": "无法连接到Redis服务器"
            }

        categories = get_all_categories(redis_client)

        return {
            "success": True,
            "categories": categories,
            "count": len(categories),
            "message": f"成功获取 {len(categories)} 个任务分类"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "categories": [],
            "message": f"获取分类列表失败: {e}"
        }

# 获取单个任务详细信息
@mcp.tool()
async def get_task_details(task_name: str) -> Dict[str, Any]:
    """
    获取单个任务的详细信息

    Args:
        task_name: 任务名称

    Returns:
        包含任务详细信息的字典
    """
    try:
        if not redis_client:
            return {
                "success": False,
                "error": "Redis连接不可用",
                "task": None,
                "message": "无法连接到Redis服务器"
            }

        task_info = get_task_info(redis_client, task_name)

        if task_info:
            return {
                "success": True,
                "task": task_info,
                "message": f"成功获取任务 '{task_name}' 的详细信息"
            }
        else:
            return {
                "success": False,
                "task": None,
                "message": f"未找到任务 '{task_name}'"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "task": None,
            "message": f"获取任务详细信息失败: {e}"
        }

# 注册任务信息到Redis（供Celery端调用）
@mcp.tool()
async def register_task_info(task_name: str, description: str, parameters: List[Dict[str, Any]],
                           return_type: str = "Any", category: str = "general", queue: str = "celery") -> Dict[str, Any]:
    """
    注册任务信息到Redis

    Args:
        task_name: 任务名称
        description: 任务描述
        parameters: 参数列表，格式如：[{"name": "param1", "type": "int", "required": true, "description": "参数描述"}]
        return_type: 返回值类型
        category: 任务分类
        queue: 任务队列

    Returns:
        注册结果
    """
    try:
        if not redis_client:
            return {
                "success": False,
                "error": "Redis连接不可用",
                "message": "无法连接到Redis服务器"
            }

        success = register_celery_task(redis_client, task_name, description, parameters, return_type, category, queue)

        if success:
            return {
                "success": True,
                "task_name": task_name,
                "message": f"成功注册任务: {task_name}"
            }
        else:
            return {
                "success": False,
                "error": "注册失败",
                "message": f"注册任务失败: {task_name}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"注册任务失败: {e}"
        }

@mcp.tool()
async def _get_redis_config():
    from Redis.redis_config import get_redis_config
    return get_redis_config()

# ====== 代码生成与部署服务 ======

# 代码生成提示模板（支持多文件、多任务）
@mcp.tool()
def generate_startMain_code(task_name: str, description: str, parameters: List[Dict[str, Any]],
                                  function_body: str, queue: str = "celery",
                                  return_type: str = "Any", tasks: List[Dict[str, Any]] = None,
                                  additional_files: List[Dict[str, str]] = None) -> str:
    """
    提供Celery任务代码生成的标准模板提示（支持多文件、多任务）

    Args:
        task_name: 主要任务名称
        description: 主要任务描述
        parameters: 主要任务参数列表
        function_body: 主要任务函数实现代码
        queue: 指定队列
        return_type: 主要任务返回值类型
        tasks: 额外任务列表 [{"name": "task2", "description": "...", "parameters": [...], "function_body": "...", "return_type": "..."}]
        additional_files: 额外文件列表 [{"filename": "utils.py", "content": "..."}]

    Returns:
        生成代码的提示模板
    """
    # 0. 获取redis参数
    from Redis.redis_config import get_redis_config
    redis_config=get_redis_config()
    logging.info(redis_config)
    # 1. 生成主要任务参数列表描述
    def format_parameters(params):
        param_descriptions = []
        for param in params:
            param_name = param.get('name', 'param')
            param_type = param.get('type', 'Any')
            param_desc = param.get('description', '参数描述')
            required = "必需" if param.get('required', True) else "可选"
            param_descriptions.append(f"  - {param_name} ({param_type}, {required}): {param_desc}")
        return "\n".join(param_descriptions) if param_descriptions else "  - 无参数"

    main_param_list = format_parameters(parameters)

    # 2. 处理额外任务
    additional_tasks_info = ""
    if tasks:
        additional_tasks_info = "\n**额外任务：**\n"
        for i, task in enumerate(tasks, 1):
            task_params = format_parameters(task.get('parameters', []))
            additional_tasks_info += f"""
{i}. 任务名称: {task.get('name', 'unknown_task')}
   - 描述: {task.get('description', '无描述')}
   - 返回类型: {task.get('return_type', 'Any')}
   - 参数列表:
{task_params}
   - 函数实现:
```python
{task.get('function_body', 'pass')}
```
"""

    # 3. 处理额外文件
    additional_files_info = ""
    if additional_files:
        additional_files_info = "\n**额外文件：**\n"
        for i, file in enumerate(additional_files, 1):
            additional_files_info += f"""
{i}. 文件名: {file.get('filename', 'unknown.py')}
   - 内容:
```python
{file.get('content', '# 空文件')}
```
"""

    # 4. 返回完整的提示模板
    return f"""
请严格按照以下模板生成Celery任务代码：

**主要任务信息：**
- 任务名称: {task_name}
- 任务描述: {description}
- 队列: {queue}
- 返回类型: {return_type}

**主要任务参数列表：**
{main_param_list}

**主要任务函数实现：**
```python
{function_body}
```
{additional_tasks_info}{additional_files_info}

**请生成以下格式的完整代码结构：**

1. **主启动文件 (app_{queue}.py):**
```python
import os
from celery import Celery
from urllib.parse import quote

# 环境变量配置 (优先级高于配置文件)
REDIS_HOST = os.getenv('REDIS_HOST', '{redis_config["host"]}')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '{redis_config.get("password", "")}')
REDIS_PORT = os.getenv('REDIS_PORT', '{redis_config["port"]}')
REDIS_BROKER_DB = os.getenv('REDIS_BROKER_DB', '0')
REDIS_BACKEND_DB = os.getenv('REDIS_BACKEND_DB', '1')

# URL编码密码
encoded_password = quote(REDIS_PASSWORD)

# 构建 Redis URL
BROKER_URL = f'redis://:{{encoded_password}}@{{REDIS_HOST}}:{{REDIS_PORT}}/{{REDIS_BROKER_DB}}'
BACKEND_URL = f'redis://:{{encoded_password}}@{{REDIS_HOST}}:{{REDIS_PORT}}/{{REDIS_BACKEND_DB}}'

# 创建 Celery 应用 - Linux 优化配置
celery_app = Celery('mcp_app',
                    broker=BROKER_URL,
                    backend=BACKEND_URL
                    )

# Linux 环境下的 Celery 配置优化
celery_app.conf.update(
    # 序列化配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # 时区配置
    timezone='UTC',
    enable_utc=True,

    # Worker 配置 - Linux 环境优化
    worker_prefetch_multiplier=1,  # 减少预取，避免内存问题
    task_acks_late=True,  # 任务完成后确认，提高可靠性

    # 结果过期时间
    result_expires=3600,  # 1小时后过期

    # 任务超时配置
    # task_soft_time_limit=300,      # 5分钟软超时
    # task_time_limit=600,           # 10分钟硬超时
)


# 如果有额外文件，在这里导入
# from .utils import helper_function

@celery_app.task(name='mcp_app.{task_name}', queue='{queue}')
def {task_name}(参数列表){f" -> {return_type}" if return_type != "Any" else ""}:
    \"""{description}\"""
    {function_body}

# 如果有额外任务，在这里添加
# @celery_app.task(name='mcp_app.(自定义)', queue='{queue}')
# def task2(...):
#     '''任务描述'''
#     实现代码
```

2. **如果需要额外文件，请生成相应的模块文件**

**生成要求：**
1. 严格按照模板格式
2. 主启动文件必须包含所有@celery_app.task装饰的函数
3. 确保参数类型注解正确
4. 保持代码缩进一致（4个空格）
5. 函数体需要正确缩进
6. 确保import语句完整
7. 如果有多个任务，都要放在同一个启动文件中
8. 额外的工具函数可以放在单独的模块文件中
9. 启动文件命名格式：app_{queue}.py
10. 所有task函数必须使用相同的queue: '{queue}'
11. 全部代码文件生成完毕后，为主启动文件 (app_{queue}.py)编写dockerfile文件，容器内部的启动命令应为 celery -A app_{queue} worker -l info -Q {queue}
"""

# 一键部署服务（MCP工具）- 只负责上传和部署已生成的代码文件夹
@mcp.tool()
async def deploy_task(task_name: str, description: str, parameters: List[Dict[str, Any]],
                                 queue: str, category: str = "general",
                                 code_folder_path: str = None) -> Dict[str, Any]:
    """
    部署已生成的代码文件夹到worker节点

    注意：此函数不负责代码生成！代码应该通过generate_celery_task_code提示词在本地生成完毕。
    此函数只负责上传和部署已经准备好的代码文件夹。

    Args:
        task_name: 任务名称
        description: 任务描述
        parameters: 参数列表
        queue: 指定队列
        category: 任务分类
        code_folder_path: 本地已生成的代码文件夹路径

    Returns:
        部署和注册的完整结果
    """
    try:
        # 1. 验证代码文件夹路径
        if not code_folder_path:
            code_folder_path = f"./generated_tasks/{task_name}_{queue}"

        # 规范化路径
        import os
        code_folder_path = os.path.abspath(code_folder_path)

        # 2. 使用FileReader读取代码文件夹中的所有文件
        import importlib
        from file_Reader import FileReader
        file_reader = FileReader()

        # 读取代码文件夹中的所有文件内容
        read_result = file_reader.read_all_files_in_folder(os.path.dirname(code_folder_path),
                                                          os.path.basename(code_folder_path))

        if read_result["status"] != "success":
            return {
                "success": False,
                "error": f"读取代码文件夹失败: {read_result['message']}",
                "code_folder_path": code_folder_path
            }

        files_content = read_result["files"]
        if not files_content:
            return {
                "success": False,
                "error": "代码文件夹为空或没有找到支持的文件",
                "code_folder_path": code_folder_path
            }

        # 处理文件路径：去掉顶层目录前缀，保持内部结构
        processed_files = {}
        folder_name = os.path.basename(code_folder_path)

        for file_path, file_info in files_content.items():
            # 去掉顶层目录前缀，保持相对路径结构
            clean_path = file_path
            if file_path.startswith(f"{folder_name}\\") or file_path.startswith(f"{folder_name}/"):
                # Windows路径: "mongodb_deploy\\app.py" -> "app.py"
                # Linux路径: "mongodb_deploy/app.py" -> "app.py"
                if '\\' in file_path:
                    clean_path = file_path[len(folder_name)+1:]  # +1 for the separator
                else:
                    clean_path = file_path[len(folder_name)+1:]

            processed_files[clean_path] = file_info

        # 调试信息：打印处理后的文件列表
        print(f"DEBUG: 处理后的文件列表: {list(processed_files.keys())}")

        files_content = processed_files

        # 调试信息：打印读取到的文件
        print(f"DEBUG: 读取到的文件列表: {list(files_content.keys())}")

        # 3. 验证必要文件是否存在
        required_files = [f"app_{queue}.py", "Dockerfile"]
        missing_files = []

        for required_file in required_files:
            # 更精确的文件匹配：文件名完全匹配或路径结尾匹配
            found = any(
                file_path == required_file or
                file_path.endswith(f"/{required_file}") or
                file_path.endswith(f"\\{required_file}") or
                os.path.basename(file_path) == required_file
                for file_path in files_content.keys()
            )
            if not found:
                missing_files.append(required_file)
                print(f"DEBUG: 缺少文件 {required_file}，可用文件: {list(files_content.keys())}")

        if missing_files:
            return {
                "success": False,
                "error": f"缺少必要文件: {', '.join(missing_files)}",
                "code_folder_path": code_folder_path,
                "available_files": list(files_content.keys())
            }

        # 4. 准备部署信息 - 包含文件内容而不是路径
        deployment_info = {
            "task_name": task_name,
            "queue": queue,
            "files_content": files_content,  # 传递文件内容
            "main_file": f"app_{queue}.py",
            "dockerfile": "Dockerfile",
            "source_path": code_folder_path,  # 仅用于记录来源
            "file_count": len(files_content)
        }

        # 5. 准备任务信息
        task_info = {
            "name": task_name,
            "description": description,
            "parameters": parameters,
            "queue": queue,
            "category": category
        }

        # 6. 调用部署服务 - 上传整个代码文件夹
        try:
            deploy_task = celery_app.send_task('mcp_app.deploy_code_folder',
                                              args=[deployment_info, task_info], queue="deploy")
            result = deploy_task.get(timeout=600)  # 10分钟超时
        except Exception as deploy_error:
            return {
                "success": False,
                "error": f"部署服务调用失败: {str(deploy_error)}",
                "code_folder_path": code_folder_path,
                "file_count": len(files_content),
                "message": "无法连接到部署服务或部署服务执行失败"
            }

        if not result.get('success'):
            return {
                "success": False,
                "error": result.get('error', '部署失败'),
                "deployment_id": result.get('deployment_id'),
                "build_log": result.get('build_log', ''),
                "message": f"代码文件夹部署失败: {result.get('message', '未知错误')}"
            }

        # 7. 自动注册任务到Redis
        registration_result = await register_task_info(
            task_name=task_name,
            description=description,
            parameters=parameters,
            category=category,
            queue=queue
        )

        return {
            "success": True,
            "task_name": task_name,
            "deployment_result": result,
            "deployment_info": deployment_info,
            "steps": {
                "file_reading": "SUCCESS",
                "folder_upload": "SUCCESS" if result.get('success') else "FAILED",
                "docker_build": "SUCCESS" if result.get('docker_image') else "FAILED",
                "container_start": "SUCCESS" if result.get('container_id') else "FAILED",
                "registration": "SUCCESS" if registration_result.get("success") else "FAILED"
            },
            "deployment_notes": [
                f"代码文件夹路径：{code_folder_path}",
                f"读取文件数量：{deployment_info['file_count']}",
                f"上传文件数量：{len(result.get('uploaded_files', []))}",
                f"Docker镜像：{result.get('docker_image', 'N/A')}",
                f"容器ID：{result.get('container_id', 'N/A')}",
                f"Worker状态：{result.get('worker_status', 'UNKNOWN')}"
            ],
            "message": f"任务 {task_name} 代码文件夹已成功部署"
        }
    except FileNotFoundError as e:
        return {
            "success": False,
            "error": f"代码文件夹不存在: {code_folder_path}",
            "message": "请检查代码文件夹路径是否正确"
        }
    except PermissionError as e:
        return {
            "success": False,
            "error": "权限不足，无法读取代码文件夹",
            "message": "请检查文件夹权限"
        }
    except Exception as e:
        # 记录完整错误但只返回安全信息
        import logging
        logging.error(f"deploy_task执行失败: {str(e)}", exc_info=True)

        return {
            "success": False,
            "error": "部署过程中发生未知错误",
            "message": f"代码文件夹部署失败，请检查日志获取详细信息"
        }




# 直接运行时的入口点
if __name__ == "__main__":
    print("MCP服务已启动")
    mcp.run()
