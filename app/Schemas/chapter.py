"""章节接口的出参（第 7 步）。

契约正本 = 设计文档 §三 正文与进度：

    GET /books/{id}/chapters        → 章节目录（不含正文） → list[ChapterOut]
    GET /books/{id}/chapters/{seq}  → 章节正文              → ChapterDetail

「能不能看」由路由判（试读没过期，或已借），这里只管形状。
"""
from pydantic import BaseModel, ConfigDict


class ChapterOut(BaseModel):
    """章节目录里的一条：标题 + 序号，不含正文。"""
    model_config = ConfigDict(from_attributes=True)
    seq: int        # 章节序号，从 1 开始
    title: str      # 章节标题


class ChapterDetail(ChapterOut):
    """章节正文：目录那两项 + content。"""
    content: str    # 正文
