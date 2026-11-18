"""数据库连接与会话。

    engine      连接池（整个应用一个）
    sessionlocal Session 工厂（每个请求一个）
    base        所有 ORM 模型的基类（表注册在 base.metadata 上）
    get_db()    FastAPI 依赖，负责开 / 关 Session

连接串不写死在代码里：从环境变量 / .env 的 DATABASE_URL 读，
优先级是 环境变量 > app/.env > config.py 里的占位默认值。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

# 连接串格式：驱动://账号:密码@主机:端口/库名?charset=utf8mb4
# utf8mb4 才能存中文和 emoji
engine = create_engine(settings.DATABASE_URL)
# Session 工厂：每个请求开一个 Session；autoflush=False 手动控制刷库时机
sessionlocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class base(DeclarativeBase):
    """所有模型的基类。模型继承它，表才会进 base.metadata（建表靠这个）。"""
    pass


def get_db():
    """FastAPI 依赖：每个请求开一个 Session，请求结束自动 close。"""
    db = sessionlocal()
    try:
        yield db          # yield 之前 = 请求处理中
    finally:
        db.close()        # 无论成功还是抛异常都会执行，防止连接泄漏
