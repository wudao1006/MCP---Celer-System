import redis

def get_redis_config():
    """获取Redis连接配置"""
    return {
        "host": "your redis host",
        "port": 6379,
        "password":"your password",
        "db": 0,
        "decode_responses": True,
        "socket_timeout": 30,
        "socket_connect_timeout": 30,
        "retry_on_timeout": True
    }

