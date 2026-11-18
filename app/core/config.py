"""全局配置（pydantic-settings）：环境变量 > .env 文件 > 这里的默认值。"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置：优先读环境变量，其次读 .env 文件。"""

    # ── 数据库 ──────────────────────────────────────────────────────
    # 不写死账号密码：复制 app/.env.example 为 app/.env，填自己的连接串。
    DATABASE_URL: str = "mysql+pymysql://root:password@127.0.0.1:3306/library_stream?charset=utf8mb4"

    # ── 认证 ────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-请改成随机长字符串"   # JWT 签名密钥；上线前必须换，泄露 = 谁都能伪造 token
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24          # token 有效期（分钟），默认 24 小时

    # ── Redis（第 9 步）：连接参数，业务 key 不在这里 ──────────────────
    REDIS_URL: str = "redis://127.0.0.1:6379/0"    # 库号 0；黑名单 / 热搜 / 借阅榜共用，靠 key 前缀区分
    REDIS_MAX_CONNECTIONS: int = 20                # 连接池上限；本地开发够用
    REDIS_SOCKET_TIMEOUT: float = 2.0              # 连不上时 2 秒就失败，别让请求挂死
    REDIS_HEALTH_CHECK_INTERVAL: int = 30          # 空闲连接每 30 秒探活一次，防止拿到被服务端断掉的连接

    model_config = {"env_file": ".env"}            # 同目录的 .env；环境变量的优先级更高


settings = Settings()   # 模块级单例，别处 `from app.core.config import settings` 直接用
