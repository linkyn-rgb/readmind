"""Redis 连接（第 9 步）。

这个文件只负责「连接」：连接池、客户端、健康检查、关闭。
业务读写不在这里 —— 按分工，黑名单的存放 / 删除 / 判断状态、热搜计数、借阅榜
都写在用它们的路由里。

API 依据：本机安装的 redis-py 8.1.0，用 `inspect.signature` 逐条核对过：
    Redis.from_url(url, **kwargs) -> Redis
    ConnectionPool.from_url(url, **kwargs)
    Redis.ping() -> bool
    Redis.close() -> None
（redis.io 官方文档本次网络不可达，未能附在线链接；升级 redis-py 后请重核上面四个签名。）

业务 key 的口径见设计文档 §二 Redis：
    登出黑名单  blacklist:<jti>     值 1，TTL = token 剩余秒数
    热搜        search:hot          有序集合
    借阅榜      book:borrow_rank    有序集合
"""
from __future__ import annotations

from redis import ConnectionPool, Redis
from redis.exceptions import RedisError

from app.core.config import settings

_pool: ConnectionPool | None = None   # 全局唯一连接池，懒加载
_client: Redis | None = None          # 全局唯一客户端，复用上面的池


def get_pool() -> ConnectionPool:
    """连接池：第一次调用时才建，之后一直复用。

    连接参数全部来自 settings，别在业务代码里另写 host / port。
    decode_responses=True → 读出来就是 str，不用每次手动 decode。
    """
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
            decode_responses=True,
        )
    return _pool


def get_redis() -> Redis:
    """业务代码统一从这里拿客户端，不要自己 `Redis(...)` 另开池。"""
    global _client
    if _client is None:
        _client = Redis(connection_pool=get_pool())
    return _client


def ping() -> bool:
    """健康检查：连得上 True，连不上 False（不抛异常）。

    刻意吞掉 RedisError：调用方一般只关心「能不能用」；
    真要把故障冒出来，业务层自己决定怎么处理（9.5 的降级口径）。
    """
    try:
        return bool(get_redis().ping())
    except RedisError:
        return False


def close() -> None:
    """服务停止时调用一次：关客户端、断开池里的连接。"""
    global _client, _pool
    if _client is not None:
        _client.close()
        _client = None
    if _pool is not None:
        _pool.disconnect()
        _pool = None
