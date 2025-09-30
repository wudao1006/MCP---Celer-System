#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux 兼容版本的 Celery 应用
适配 Linux 环境下的路径和配置
"""
import os
from celery import Celery
from urllib.parse import quote
from Redis.redis_config import get_redis_config

# 使用统一的Redis配置
redis_config = get_redis_config()

# 环境变量配置 (优先级高于配置文件)
REDIS_HOST = os.getenv('REDIS_HOST', redis_config['host'])
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', redis_config.get('password', ''))
REDIS_PORT = os.getenv('REDIS_PORT', str(redis_config['port']))
REDIS_BROKER_DB = os.getenv('REDIS_BROKER_DB', '0')
REDIS_BACKEND_DB = os.getenv('REDIS_BACKEND_DB', '1')

# URL编码密码
encoded_password = quote(REDIS_PASSWORD)

# 构建 Redis URL
BROKER_URL = f'redis://:{encoded_password}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_BROKER_DB}'
BACKEND_URL = f'redis://:{encoded_password}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_BACKEND_DB}'

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



