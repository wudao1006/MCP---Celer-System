import redis

def get_redis_config():
    """获取Redis连接配置

    配置优先级：环境变量 > 配置文件

    环境变量：
    - REDIS_HOST: Redis服务器地址
    - REDIS_PORT: Redis端口
    - REDIS_PASSWORD: Redis密码
    - REDIS_DB: Redis数据库编号

    使用前请复制此文件为 redis_config.py 并修改配置
    """
    return {
        "host": "localhost",           # Redis服务器地址
        "port": 6379,                  # Redis端口
        "password": "",                # Redis密码（如果有）
        "db": 0,                       # Redis数据库编号
        "decode_responses": True,      # 自动解码响应
        "socket_timeout": 30,          # Socket超时时间（秒）
        "socket_connect_timeout": 30,  # 连接超时时间（秒）
        "retry_on_timeout": True       # 超时时重试
    }