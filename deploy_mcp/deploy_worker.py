#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import uuid
import json
import logging
import base64
from pathlib import Path
from typing import Dict, Any, List
from celery import Celery
from urllib.parse import quote

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量或配置文件获取Redis配置
try:
    from Redis.redis_config import get_redis_config
    redis_config = get_redis_config()
except:
    # 如果无法导入配置，使用默认值
    redis_config = {
        "host": "localhost",
        "port": 6379,
        "password": "",
        "db": 0
    }

# 环境变量配置 (优先级高于配置文件)
REDIS_HOST = os.getenv('REDIS_HOST', redis_config["host"])
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', redis_config.get("password", ""))
REDIS_PORT = os.getenv('REDIS_PORT', redis_config["port"])
REDIS_BROKER_DB = os.getenv('REDIS_BROKER_DB', '0')
REDIS_BACKEND_DB = os.getenv('REDIS_BACKEND_DB', '1')

# URL编码密码
encoded_password = quote(REDIS_PASSWORD)

# 构建 Redis URL
BROKER_URL = f'redis://:{encoded_password}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_BROKER_DB}'
BACKEND_URL = f'redis://:{encoded_password}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_BACKEND_DB}'

# 创建 Celery 应用
celery_app = Celery('mcp_app',
                    broker=BROKER_URL,
                    backend=BACKEND_URL)

# Celery 配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    result_expires=3600,
)

@celery_app.task(name='mcp_app.deploy_code_folder', queue='deploy')
def deploy_code_folder(deployment_info: Dict[str, Any], task_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    部署代码文件夹到worker节点

    Args:
        deployment_info: 部署信息字典，包含：
            - task_name: 任务名称
            - queue: 队列名称
            - files_content: 文件内容字典 (文件路径 -> 文件信息)
            - main_file: 主启动文件名
            - dockerfile: Dockerfile文件名
            - source_path: 源路径（仅用于记录）
            - file_count: 文件数量
        task_info: 任务信息字典，包含：
            - name: 任务名称
            - description: 任务描述
            - parameters: 参数列表
            - queue: 队列名称
            - category: 任务分类

    Returns:
        部署结果字典
    """
    deployment_id = str(uuid.uuid4())
    task_name = deployment_info.get('task_name')
    queue = deployment_info.get('queue')
    files_content = deployment_info.get('files_content', {})

    logger.info(f"开始部署任务 {task_name}，部署ID: {deployment_id}")
    logger.info(f"接收到 {len(files_content)} 个文件")

    try:
        # 1. 创建部署目录 - 使用当前工作目录下的code文件夹
        current_dir = os.getcwd()
        code_base_path = os.path.join(current_dir, 'code')
        os.makedirs(code_base_path, exist_ok=True)

        deployment_path = os.path.join(code_base_path, f"{task_name}_{queue}_{deployment_id}")
        os.makedirs(deployment_path, exist_ok=True)

        # 2. 写入所有文件内容到部署目录，完全按照原始结构还原
        uploaded_files = []
        for file_path, file_info in files_content.items():
            # 提取文件名，去除路径部分
            # 使用 os.path.basename 获取纯文件名
            file_name = os.path.basename(file_path)
            dest_file_path = os.path.join(deployment_path, file_name)

            # 创建文件所在的目录
            dest_dir = os.path.dirname(dest_file_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)

            try:
                if file_info.get('type') == 'binary' and file_info.get('encoding') == 'base64':
                    # 处理base64编码的二进制文件
                    binary_content = base64.b64decode(file_info['content'])
                    with open(dest_file_path, 'wb') as f:
                        f.write(binary_content)
                else:
                    # 处理文本文件
                    with open(dest_file_path, 'w', encoding='utf-8') as f:
                        f.write(file_info['content'])

                uploaded_files.append(file_path)
                logger.info(f"写入文件: {file_path} ({file_info.get('size', 0)} bytes)")

            except Exception as e:
                logger.error(f"写入文件失败 {file_path}: {e}")
                return {
                    "success": False,
                    "error": f"写入文件失败 {file_path}: {e}",
                    "deployment_id": deployment_id
                }

        logger.info(f"成功写入 {len(uploaded_files)} 个文件")

        # 3. 验证必要文件
        main_file = deployment_info.get('main_file', f'app_{queue}.py')
        dockerfile = deployment_info.get('dockerfile', 'Dockerfile')

        main_file_path = os.path.join(deployment_path, main_file)
        dockerfile_path = os.path.join(deployment_path, dockerfile)

        if not os.path.exists(main_file_path):
            return {
                "success": False,
                "error": f"主启动文件不存在: {main_file}",
                "deployment_id": deployment_id,
                "uploaded_files": uploaded_files
            }

        if not os.path.exists(dockerfile_path):
            return {
                "success": False,
                "error": f"Dockerfile不存在: {dockerfile}",
                "deployment_id": deployment_id,
                "uploaded_files": uploaded_files
            }

        # 4. 构建Docker镜像
        image_name = f"celery-{task_name.lower().replace('_', '-')}"
        build_result = build_docker_image(deployment_path, image_name, deployment_id)

        if not build_result["success"]:
            return {
                "success": False,
                "error": f"Docker镜像构建失败: {build_result.get('error', '未知错误')}",
                "deployment_id": deployment_id,
                "uploaded_files": uploaded_files,
                "build_log": build_result.get("log", "")
            }

        docker_image = build_result["image_name"]

        # 5. 启动容器
        container_result = start_container(
            image_name=docker_image,
            container_name=f"{task_name}_{queue}_worker",
            queue=queue,
            task_name=task_name
        )

        if not container_result["success"]:
            return {
                "success": False,
                "error": f"容器启动失败: {container_result.get('error', '未知错误')}",
                "deployment_id": deployment_id,
                "uploaded_files": uploaded_files,
                "docker_image": docker_image,
                "container_log": container_result.get("log", "")
            }

        container_id = container_result["container_id"]

        # 6. 检查worker状态
        worker_status = check_worker_status(container_id)

        logger.info(f"部署完成: {task_name}, 容器ID: {container_id}")

        return {
            "success": True,
            "deployment_id": deployment_id,
            "uploaded_files": uploaded_files,
            "docker_image": docker_image,
            "container_id": container_id,
            "worker_status": worker_status,
            "deployment_path": deployment_path,
            "files_processed": len(files_content),
            "message": f"任务 {task_name} 部署成功"
        }

    except Exception as e:
        logger.error(f"部署失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "deployment_id": deployment_id,
            "message": f"任务 {task_name} 部署失败"
        }

def build_docker_image(build_path: str, image_name: str, deployment_id: str) -> Dict[str, Any]:
    """
    构建Docker镜像

    Args:
        build_path: 构建路径
        image_name: 镜像名称
        deployment_id: 部署ID

    Returns:
        构建结果
    """
    try:
        # 添加部署ID作为镜像标签
        full_image_name = f"{image_name}:{deployment_id}"

        # 构建Docker镜像
        build_cmd = [
            'docker', 'build',
            '-t', full_image_name,
            build_path
        ]

        logger.info(f"构建Docker镜像: {' '.join(build_cmd)}")

        result = subprocess.run(
            build_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )

        if result.returncode == 0:
            logger.info(f"Docker镜像构建成功: {full_image_name}")
            return {
                "success": True,
                "image_name": full_image_name,
                "log": result.stdout
            }
        else:
            logger.error(f"Docker镜像构建失败: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr,
                "log": result.stdout
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Docker镜像构建超时",
            "log": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "log": ""
        }

def start_container(image_name: str, container_name: str, queue: str, task_name: str) -> Dict[str, Any]:
    """
    启动Docker容器

    Args:
        image_name: 镜像名称
        container_name: 容器名称
        queue: 队列名称
        task_name: 任务名称

    Returns:
        启动结果
    """
    try:
        # 停止并删除同名容器（如果存在）
        cleanup_cmd = f"docker stop {container_name} 2>/dev/null && docker rm {container_name} 2>/dev/null || true"
        subprocess.run(cleanup_cmd, shell=True)

        # 启动新容器
        start_cmd = [
            'docker', 'run',
            '-d',
            '--name', container_name,
            '--restart', 'unless-stopped',
            '-e', f'REDIS_HOST={REDIS_HOST}',
            '-e', f'REDIS_PORT={REDIS_PORT}',
            '-e', f'REDIS_PASSWORD={REDIS_PASSWORD}',
            '-e', f'REDIS_BROKER_DB={REDIS_BROKER_DB}',
            '-e', f'REDIS_BACKEND_DB={REDIS_BACKEND_DB}',
            '-e', 'C_FORCE_ROOT=1',
            image_name,
            'celery', '-A', f'app_{queue}', 'worker', '-l', 'info', '-Q', queue
        ]

        logger.info(f"启动容器: {' '.join(start_cmd)}")

        result = subprocess.run(
            start_cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1分钟超时
        )

        if result.returncode == 0:
            container_id = result.stdout.strip()
            logger.info(f"容器启动成功: {container_name}, ID: {container_id}")
            return {
                "success": True,
                "container_id": container_id,
                "container_name": container_name
            }
        else:
            logger.error(f"容器启动失败: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr,
                "log": result.stdout
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "容器启动超时"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def check_worker_status(container_id: str) -> str:
    """
    检查worker状态

    Args:
        container_id: 容器ID

    Returns:
        worker状态
    """
    try:
        # 检查容器是否运行
        check_cmd = ['docker', 'ps', '-q', '-f', f'id={container_id}']
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            return "RUNNING"
        else:
            return "STOPPED"

    except Exception as e:
        logger.error(f"检查worker状态失败: {e}")
        return "UNKNOWN"

@celery_app.task(name='mcp_app.stop_deployed_task', queue='deploy')
def stop_deployed_task(deployment_id: str, container_name: str = None) -> Dict[str, Any]:
    """
    停止已部署的任务

    Args:
        deployment_id: 部署ID
        container_name: 容器名称（可选）

    Returns:
        停止结果
    """
    try:
        if container_name:
            # 停止指定容器
            stop_cmd = ['docker', 'stop', container_name]
            result = subprocess.run(stop_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # 删除容器
                rm_cmd = ['docker', 'rm', container_name]
                subprocess.run(rm_cmd, capture_output=True, text=True)

                return {
                    "success": True,
                    "deployment_id": deployment_id,
                    "message": f"容器 {container_name} 已停止并删除"
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "deployment_id": deployment_id
                }
        else:
            return {
                "success": False,
                "error": "缺少容器名称",
                "deployment_id": deployment_id
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "deployment_id": deployment_id
        }

@celery_app.task(name='mcp_app.list_deployed_tasks', queue='deploy')
def list_deployed_tasks() -> Dict[str, Any]:
    """
    列出所有已部署的任务

    Returns:
        部署列表
    """
    try:
        # 列出所有以celery-开头的容器
        list_cmd = ['docker', 'ps', '-a', '--filter', 'name=*_worker', '--format', 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}']
        result = subprocess.run(list_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            containers = []
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行

            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        containers.append({
                            "name": parts[0],
                            "image": parts[1],
                            "status": parts[2],
                            "created": parts[3]
                        })

            return {
                "success": True,
                "containers": containers,
                "count": len(containers)
            }
        else:
            return {
                "success": False,
                "error": result.stderr,
                "containers": []
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "containers": []
        }

# 直接运行时的入口点
if __name__ == "__main__":
    print("部署Worker服务已启动")
    celery_app.start()