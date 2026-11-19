"""章节正文（第 7 步）。

契约正本 = 设计文档 §二 chapters：

    id        主键
    book_id   外键 → books.id
    seq       章节序号，从 1 开始
    title     章节标题
    content   正文

    唯一约束：(book_id, seq)

「半本书」= 这本书在 chapters 里**没有行**（设计文档 §二「半本书」怎么认）：
详情页照常看，但读 / 试读 / 借 / 加书架全不给。表上不存「有没有正文」，
判定就是数这张表里 book_id 的行数，等于 0 就是半本。

⚠️ 顺序：正文内容第 7 步再灌；第 2 步只建空表（设计文档 §五 两处连带的）。
"""
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import base

# 只给类型检查用。运行时 import 会成环：Book.py 对这里是运行时 import，
# 三个文件只能有一个方向的运行时引用（样板是 Shelf.py / BorrowRecord.py）。
if TYPE_CHECKING:
    from app.models.Book import Book


class Chapter(base):
    __tablename__ = "chapters"
    # 同一本书里 seq 不能重复：章节序号是「第几章」的唯一标识
    __table_args__ = (
        UniqueConstraint("book_id", "seq", name="uq_chapter_book_seq"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)   # 主键

    # 属于哪本书
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))  # 外键 → books.id

    seq: Mapped[int] = mapped_column(Integer)          # 章节序号，从 1 开始
    title: Mapped[str] = mapped_column(String(200))    # 章节标题
    content: Mapped[str] = mapped_column(Text)         # 正文

    # 关系（不占数据库列）：一章 ↔ 一本书；反向在 Book.chapters
    book: Mapped["Book"] = relationship(back_populates="chapters")   # ↔ Book.chapters
