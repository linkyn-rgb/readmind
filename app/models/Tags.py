"""标签表（第 2 步）。

自由词标签，只用来喂推荐，不作为筛选入口。和图书是多对多（中间表 book_tags）。
同文件定义 book_tags 中间表；列名是 tags_id（10-20 定的契约，不是 book_id 的笔误）。
"""
from sqlalchemy import String,Integer,Table,ForeignKey,Column
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.database import base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.Book import Book

# 图书 ↔ 标签（多对多）
book_tags=Table(
    "book_tags",base.metadata,
    Column("tags_id",ForeignKey("tags.id"),primary_key=True),   # 列名就叫 tags_id（10-20 定的，不是笔误，别改）
    Column("book_id",ForeignKey("books.id"),primary_key=True),
)


class Tags(base):
    """标签：自由词，只喂推荐用，不做筛选入口。"""
    __tablename__="tags"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)    # 主键
    name:Mapped[str]=mapped_column(String(200),unique=True)   # 标签名唯一；同义词入库前要收成一个
    books:Mapped[list["Book"]]=relationship(secondary=book_tags,back_populates="tags")   # ↔ Book.tags
