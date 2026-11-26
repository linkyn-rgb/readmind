"""Redis 连接（第 9 步）。

这个文件负责两块：连接层（连接池、客户端、健康检查、关闭），
以及第 9 步的 Redis key 纯命令包装（热搜 / 借阅榜的 +1 / Top N）。
「什么时候该调、失败了怎么降级」是业务，写在路由里 ——
黑名单的存放 / 删除 / 状态判断也仍在 auth.py / dep.py。

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


# ---------- 热搜 search:hot（9.3） ----------

SEARCH_HOT_KEY = "search:hot"   # 有序集合：member = 搜索词，score = 次数


def incr_search_hot(keyword: str) -> None:
    """热搜 +1。词在写入前统一 strip + lower —— Redis 的 member 区分大小写，
    不做这一步「Python」和「python」会变成榜上两条。

    不吞 RedisError：Redis 挂了让异常冒回路由，由调用方决定降级
    （搜索接口不能因为热搜计数失败而 500）。空词直接忽略。
    """
    word = keyword.strip().lower()
    if not word:
        return
    get_redis().zincrby(SEARCH_HOT_KEY, 1, word)


def top_search_hot(n: int = 10) -> list[tuple[str, float]]:
    """热搜 Top N：按次数降序，返回 [(词, 次数)]；榜空 / key 不存在时返回 []。

    读失败同样不吞 —— 由路由决定是返回空列表还是别的。
    """
    return get_redis().zrange(SEARCH_HOT_KEY, 0, n - 1, desc=True, withscores=True)


# ---------- 借阅榜 book:borrow_rank（9.4） ----------

BORROW_RANK_KEY = "book:borrow_rank"   # 有序集合：member = 书 id 的字符串，score = 被借次数


def incr_borrow_rank(book_id: int) -> None:
    """借阅榜 +1。只由「借书成功」调用 —— 续借 / 还书都不算（设计 §7.3）。

    不吞 RedisError：Redis 挂了让异常冒回路由，由调用方决定降级
    （借书主流程不能因为榜单计数失败而回滚）。
    """
    get_redis().zincrby(BORROW_RANK_KEY, 1, str(book_id))


def top_borrow_rank(n: int = 20) -> list[tuple[int, float]]:
    """借阅榜 Top N：按次数降序，返回 [(书 id, 次数)]；榜空 / key 不存在时返回 []。

    Redis 里 member 存的是字符串 id，这里转回 int —— 路由拿去查库时不用再转。
    读失败不吞，由路由决定返回空榜（9.5 降级口径）。
    """
    rows = get_redis().zrange(BORROW_RANK_KEY, 0, n - 1, desc=True, withscores=True)
    return [(int(member), score) for member, score in rows]
