"""用户评价（第 8 步）—— 读完一半以上，给这本书打一次分。

契约正本 = 设计文档 §二 reviews：

    id         主键
    user_id    外键 → users.id（服务端从 token 取，客户端传不进来）
    book_id    外键 → books.id
    rating     1~5 的整数
    content    评价内容
    created_at 服务端 datetime.now()

    唯一约束：(user_id, book_id)  —— 一本只能评一次
    普通索引：(book_id)           —— 详情页拉这本书的评价列表

「不能改、不能删」（10-08 定），所以只有 created_at，没有 updated_at。
评价门槛（进度 ≥ 50%）不写在表里 —— 那是路由拿 progress_fraction() 现算的；
表只负责最后一道：同一用户对同一本书最多一行。

⚠️ 路由捕获 IntegrityError 之后必须 db.rollback()：
   唯一约束撞了以后 Session 已经进入失败状态，不回滚的话同一请求里后面每条 SQL 都会报错。
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import base

# 只给类型检查用。运行时 import 会成环：Book.py / User.py 对这里是运行时 import，
# 三个文件只能有一个方向的运行时引用（样板是 Chapter.py）。
if TYPE_CHECKING:
    from app.models.Book import Book
    from app.models.User import User


class Review(base):
    """一条书评：一行 = 一个用户对一本书的唯一一次评价。"""

    __tablename__ = "reviews"
    __table_args__ = (
        # 应用层先查重（给友好提示），这条唯一约束防并发：两个请求同时进来时，
        # 数据库直接拒掉第二条 → 路由捕获 IntegrityError 转 409 REVIEW_EXISTS
        UniqueConstraint("user_id", "book_id", name="uq_review_user_book"),
        # 详情页「这本书的评价列表」按 book_id 查，走这条索引；
        # 上面那条唯一索引是 (user_id, book_id)，前导列是 user_id，帮不上 book_id 的查询
        Index("ix_reviews_book_id", "book_id"),
        # 第二道网：接口层已经用 Field(ge=1, le=5) 挡了，这条防绕过接口直接写库
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # 主键

    # 外键：谁评的、评的哪本
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # 评价人；从 token 取，不收客户端值
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))  # 被评的书

    rating: Mapped[int] = mapped_column(Integer)  # 评分 1~5；表上有 CHECK 兜底
    content: Mapped[str] = mapped_column(Text)    # 评价正文

    # 服务端写；用 Python 默认值而不是 SQL 的 NOW()，和其他表（borrows / reading_logs）保持同一种时间口径
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 关系（不占数据库列）：一条评价 ↔ 一个用户 / 一本书
    # 反向在 User.reviews / Book.reviews，名字必须成对，单复数错了 mapper 直接起不来
    user: Mapped["User"] = relationship(back_populates="reviews")
    book: Mapped["Book"] = relationship(back_populates="reviews")
