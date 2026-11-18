"""项目入口：创建 FastAPI 应用、挂载路由、建表。

这个是开端切片：只包含第 1 步「用户认证」。
完整项目按设计文档 §五 的 11 步推进，其余模块随步骤并入本仓库。

启动（在仓库根目录、激活虚拟环境之后）：
    uvicorn main:app --reload
Swagger 文档：http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI

from app.routers import auth
from app.database import engine, base
from app import models

app = FastAPI(
    title="Library Stream",
    description="图书阅读平台后端 —— 当前开放用户认证模块",
    version="0.1.0",
)

# 完整项目里 auth.router 曾同时挂在 /user 和 /auth 两套前缀下；
# 这里只保留 /auth，一套前缀更好维护。
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# 开发期靠它同步表结构；接真实数据之前要换成 Alembic 迁移
# ⚠️ drop_all 会删掉全部表，任何时候都不要打开
base.metadata.create_all(bind=engine)
