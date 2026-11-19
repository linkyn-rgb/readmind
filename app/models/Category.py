"""题材分类（第 2 步）。

categories 是一张自关联的树（parent_id 指向自己）；实际只用到两层，但结构支持多层。
同文件还定义了两张多对多中间表：
    book_sources     图书 ↔ 来源（定义在这里只是就近放，被 Book / Sources 引用）
    book_categories  图书 ↔ 题材
中间表只有两个外键列、没有业务字段，所以能直接用 relationship(secondary=...)。
"""
from sqlalchemy import String,ForeignKey,Table,Column
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.database import base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.Book import Book

# 图书 ↔ 来源（多对多）
# 中间表只有两个外键列、没有业务字段 → 才能用 relationship(secondary=...)
book_sources=Table(
    "book_sources",base.metadata,
    Column("book_id",ForeignKey("books.id"),primary_key=True),      # 两列都设主键：同一组合天生不能重复
    Column("source_id",ForeignKey("sources.id"),primary_key=True),
)
# 图书 ↔ 题材（多对多，只挂子类）
book_categories=Table(
    "book_categories",base.metadata,
    Column("book_id",ForeignKey("books.id"),primary_key=True),
    Column("category_id",ForeignKey("categories.id"),primary_key=True),
)


class Category(base):
    """题材分类：自关联的树（现在两层：大类 → 小类；留多层，以后往下分不用改结构）。"""
    __tablename__="categories"
    id:Mapped[int]=mapped_column(primary_key=True)                           # 主键
    name:Mapped[str]=mapped_column(String(100),unique=True)                  # 分类名，唯一
    parent_id:Mapped[int | None]=mapped_column(ForeignKey("categories.id"))  # 父类 id；NULL = 顶层大类
    # 自关联：remote_side 告诉 SQLAlchemy「parent 是『一』的那头」，否则分不清谁是谁的父
    parent:Mapped["Category | None"]=relationship(back_populates="children", remote_side="Category.id")
    children:Mapped[list["Category"]]=relationship(back_populates="parent")  # 反向：这个分类下面的子分类
    books:Mapped[list["Book"]]=relationship(secondary=book_categories,back_populates="categories")  # ↔ Book.categories
