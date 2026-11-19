"""图书主表（第 2 步）。

books 表只存元数据；正文在 chapters 表（随第 7 步并入），
题材 / 来源 / 标签走三张多对多中间表（随第 3、4 步并入）。

当前是第 2 步的切片：只有 books 表本身，不 import 其他模型。
categories / sources / tags / shelves / borrow_records / chapters / reviews
这些关系在对应模块并入时再补回来（补的代码以完整工程为准）。
"""
from sqlalchemy import String,Text
from sqlalchemy.orm import Mapped,mapped_column
from app.database import base


class Book(base):
    """图书本体：只存元数据。"""
    __tablename__="books"
    id:Mapped[int]=mapped_column(primary_key=True)               # 主键
    title:Mapped[str]=mapped_column(String(200),index=True)      # 书名；搜索按它查，所以建索引
    author:Mapped[str]=mapped_column(String(200))                # 作者
    isbn:Mapped[str | None]=mapped_column(String(200))           # ISBN，可能没有
    desc:Mapped[String | None]=mapped_column(Text)               # 简介
    cover:Mapped[String | None]=mapped_column(Text)              # 封面路径 / URL
    author_bio:Mapped[String| None]=mapped_column(Text)          # 作者简介
