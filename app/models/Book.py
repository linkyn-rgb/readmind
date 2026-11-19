"""图书主表（第 2 步）。

books 表只存元数据；正文在 chapters 表，题材 / 来源 / 标签走三张多对多中间表。
「有没有正文」不存字段，靠 chapters 里有没有这本书的行来判断（见 Chapter.py）。
"""
from sqlalchemy import String,Integer,Boolean,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.database import base
from app.models.Category import book_categories,book_sources
from app.models.Tags import Tags
from app.models.Tags import book_tags
from app.models.Category import Category
from app.models.Sources import Source
from app.models.BorrowRecord import BorrowRecord
from app.models.Chapter import Chapter
from app.models.Review import Review
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.Shelf import user_book,Readinglogs


class Book(base):
    """图书本体：只存元数据；正文在 chapters 表（「半本书」= chapters 里没有行）。"""
    __tablename__="books"
    id:Mapped[int]=mapped_column(primary_key=True)               # 主键
    title:Mapped[str]=mapped_column(String(200),index=True)      # 书名；搜索按它查，所以建索引
    author:Mapped[str]=mapped_column(String(200))                # 作者
    isbn:Mapped[str | None]=mapped_column(String(200))           # ISBN，可能没有
    desc:Mapped[String | None]=mapped_column(Text)               # 简介
    cover:Mapped[String | None]=mapped_column(Text)              # 封面路径 / URL
    author_bio:Mapped[String| None]=mapped_column(Text)          # 作者简介
    # 多对多：关系存在中间表里（secondary），books 表本身没有这些列
    categories:Mapped[list["Category"]]=relationship(secondary=book_categories,back_populates="books")  # ↔ Category.books
    sources:Mapped[list["Source"]]=relationship(secondary=book_sources,back_populates="books")         # ↔ Source.books
    tags:Mapped[list["Tags"]]=relationship(secondary=book_tags,back_populates="books")                 # ↔ Tags.books
    # 反向关系：一本书可以被很多用户加进书架（一对多）
    shelves:Mapped[list["user_book"]]=relationship(back_populates="book")     # ↔ user_book.book
    readinglogs:Mapped[list["Readinglogs"]]=relationship(back_populates="book")   # ↔ Readinglogs.book
    borrow_records:Mapped[list["BorrowRecord"]]=relationship(back_populates="book")   # ↔ BorrowRecord.book
    chapters:Mapped[list["Chapter"]]=relationship(back_populates="book")          # ↔ Chapter.book；没有行 = 半本书
    reviews:Mapped[list["Review"]]=relationship(back_populates="book")            # ↔ Review.book；这本书的全部评价
