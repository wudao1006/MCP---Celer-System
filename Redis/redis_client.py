import redis
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .redis_config import get_redis_config


def get_redis_client():
    """获取Redis客户端连接"""
    config = get_redis_config()
    try:
        client = redis.Redis(**config)
        client.ping()  # 测试连接
        return client
    except Exception as e:
        print(f"Redis连接失败: {e}")
        return None

def register_celery_task(client: redis.Redis, task_name: str, description: str,
                        parameters: List[Dict[str, Any]], return_type: str = "Any",
                        category: str = "general", queue: str = "celery") -> bool:
    """
    注册Celery任务信息到Redis

    Args:
        client: Redis客户端
        task_name: 任务名称
        description: 任务描述
        parameters: 参数列表
        return_type: 返回值类型
        category: 任务分类
        queue: 任务队列

    Returns:
        注册是否成功
    """
    try:
        task_key = f"celery:task:{task_name}"
        task_info = {
            "name": task_name,
            "description": description,
            "parameters": json.dumps(parameters, ensure_ascii=False),
            "return_type": return_type,
            "category": category,
            "queue": queue,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }

        client.hset(task_key, mapping=task_info)

        # 同时添加到任务索引中，方便按分类查询
        client.sadd(f"celery:category:{category}", task_name)
        client.sadd("celery:all_tasks", task_name)

        return True
    except Exception as e:
        print(f"注册任务失败: {e}")
        return False

def get_all_tasks(client: redis.Redis) -> List[Dict[str, Any]]:
    """
    获取所有注册的任务信息

    Args:
        client: Redis客户端

    Returns:
        任务信息列表
    """
    try:
        task_names = client.smembers("celery:all_tasks")
        tasks = []

        for task_name in task_names:
            task_key = f"celery:task:{task_name}"
            task_info = client.hgetall(task_key)

            if task_info:
                # 解析参数JSON
                try:
                    parameters = json.loads(task_info.get("parameters", "[]"))
                except:
                    parameters = []

                tasks.append({
                    "name": task_info.get("name", ""),
                    "description": task_info.get("description", ""),
                    "parameters": parameters,
                    "return_type": task_info.get("return_type", "Any"),
                    "category": task_info.get("category", "general"),
                    "queue": task_info.get("queue", "celery"),
                    "created_at": task_info.get("created_at", ""),
                    "last_updated": task_info.get("last_updated", "")
                })

        return sorted(tasks, key=lambda x: x.get("category", ""))
    except Exception as e:
        print(f"获取任务列表失败: {e}")
        return []

def get_tasks_by_category(client: redis.Redis, category: str) -> List[Dict[str, Any]]:
    """
    根据分类获取任务信息

    Args:
        client: Redis客户端
        category: 任务分类

    Returns:
        该分类下的任务信息列表
    """
    try:
        task_names = client.smembers(f"celery:category:{category}")
        tasks = []

        for task_name in task_names:
            task_key = f"celery:task:{task_name}"
            task_info = client.hgetall(task_key)

            if task_info:
                try:
                    parameters = json.loads(task_info.get("parameters", "[]"))
                except:
                    parameters = []

                tasks.append({
                    "name": task_info.get("name", ""),
                    "description": task_info.get("description", ""),
                    "parameters": parameters,
                    "return_type": task_info.get("return_type", "Any"),
                    "category": task_info.get("category", "general"),
                    "queue": task_info.get("queue", "celery"),
                    "created_at": task_info.get("created_at", ""),
                    "last_updated": task_info.get("last_updated", "")
                })

        return tasks
    except Exception as e:
        print(f"获取分类任务失败: {e}")
        return []

def get_task_info(client: redis.Redis, task_name: str) -> Optional[Dict[str, Any]]:
    """
    获取单个任务的详细信息

    Args:
        client: Redis客户端
        task_name: 任务名称

    Returns:
        任务信息字典或None
    """
    try:
        task_key = f"celery:task:{task_name}"
        task_info = client.hgetall(task_key)

        if not task_info:
            return None

        try:
            parameters = json.loads(task_info.get("parameters", "[]"))
        except:
            parameters = []

        return {
            "name": task_info.get("name", ""),
            "description": task_info.get("description", ""),
            "parameters": parameters,
            "return_type": task_info.get("return_type", "Any"),
            "category": task_info.get("category", "general"),
            "queue": task_info.get("queue", "celery"),
            "created_at": task_info.get("created_at", ""),
            "last_updated": task_info.get("last_updated", "")
        }
    except Exception as e:
        print(f"获取任务信息失败: {e}")
        return None

def remove_task(client: redis.Redis, task_name: str) -> bool:
    """
    从Redis中移除任务信息

    Args:
        client: Redis客户端
        task_name: 任务名称

    Returns:
        移除是否成功
    """
    try:
        # 获取任务信息以获得分类
        task_info = get_task_info(client, task_name)
        if task_info:
            category = task_info.get("category", "general")
            # 从分类索引中移除
            client.srem(f"celery:category:{category}", task_name)

        # 从全局索引中移除
        client.srem("celery:all_tasks", task_name)

        # 删除任务信息
        task_key = f"celery:task:{task_name}"
        client.delete(task_key)

        return True
    except Exception as e:
        print(f"移除任务失败: {e}")
        return False

def get_all_categories(client: redis.Redis) -> List[str]:
    """
    获取所有任务分类

    Args:
        client: Redis客户端

    Returns:
        分类列表
    """
    try:
        # 获取所有分类键
        category_keys = client.keys("celery:category:*")
        categories = []

        for key in category_keys:
            # 提取分类名称
            category = key.replace("celery:category:", "")
            # 检查该分类下是否还有任务
            if client.scard(key) > 0:
                categories.append(category)

        return sorted(categories)
    except Exception as e:
        print(f"获取分类列表失败: {e}")
        return []

def update_task_info(client: redis.Redis, task_name: str, **kwargs) -> bool:
    """
    更新任务信息

    Args:
        client: Redis客户端
        task_name: 任务名称
        **kwargs: 要更新的字段

    Returns:
        更新是否成功
    """
    try:
        task_key = f"celery:task:{task_name}"

        # 检查任务是否存在
        if not client.exists(task_key):
            return False

        # 更新时间戳
        kwargs["last_updated"] = datetime.now().isoformat()

        # 如果更新了parameters，需要转换为JSON
        if "parameters" in kwargs:
            kwargs["parameters"] = json.dumps(kwargs["parameters"], ensure_ascii=False)

        # 更新字段
        client.hset(task_key, mapping=kwargs)

        return True
    except Exception as e:
        print(f"更新任务信息失败: {e}")
        return False