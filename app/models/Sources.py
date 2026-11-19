"""来源表（第 2 步）：书从哪儿来（日本轻小说 / 中国轻小说 / 名著 / 中国长篇 / 中国短篇）。

固定 5 条种子数据，不提供增删改接口。和图书是多对多（中间表 book_sources）。
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.database import base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.Book import Book
from app.models.Category import book_sources


class Source(base):
    """来源：固定 5 条（日本轻小说 / 中国轻小说 / 名著 / 中国长篇 / 中国短篇），不做增删。"""
    __tablename__="sources"
    id:Mapped[int]=mapped_column(primary_key=True)   # 主键
    name:Mapped[str]=mapped_column(String(200))      # 来源名
    books:Mapped[list["Book"]]=relationship(secondary=book_sources,back_populates="sources")   # ↔ Book.sources
