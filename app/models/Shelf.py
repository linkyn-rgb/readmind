"""书架与阅读日志两张表（第 5、7 步）。

    user_books  一行 = 一个用户 × 一本书；身兼书架成员 / 试读凭证 / 阅读进度三职
    Readinglogs 一次阅读上报 = 一行；只做统计，不参与「在不在书架」的判断

两张表都挂在 users / books 上，是典型的一对多。
"""
from sqlalchemy import ForeignKey,Integer,DateTime,Float,Boolean,UniqueConstraint,Index
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.database import base
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.Book import Book
    from app.models.User import User


class user_book(base):
    """用户书架：一行 = 一个用户 × 一本书，永不删。

    一张表身兼三职（见设计文档 §user_books）：
        1. 书架成员 —— in_shelf=True 的才显示在书架里
        2. 试读凭证 —— trial_started_at 有值 = 这本书的试读已经用过了（每本只有一次）
        3. 阅读进度 —— 跟着「书」走，还了再借不清零

    ⚠️ 类名仍是小写 user_book（不是 UserBook），表名已按设计文档改成 user_books。
    改类名要先把 routers/user.py、models/Book.py、models/User.py 里引用它的地方一起改。
    """
    __tablename__="user_books"
    # 一个用户对一本书只能有一行：重复加入书架 = 更新这一行，而不是再插一行
    __table_args__ = (
    UniqueConstraint("user_id", "book_id", name="uq_user_book_user_book"),
    Index("ix_user_books_user_in_shelf", "user_id", "in_shelf"),   # 查「我的书架」：user_id + in_shelf
)
    id:Mapped[int]=mapped_column(Integer,primary_key=True)                    # 主键
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)      # 谁的书架；按用户查书架走这个索引
    book_id:Mapped[int]=mapped_column(ForeignKey("books.id"),index=True)      # 哪本书
    added_at:Mapped[datetime | None ]=mapped_column(DateTime(timezone=True))                     # 加入书架的时刻（「想读」区按它排序）
    trial_started_at:Mapped[datetime | None]=mapped_column(DateTime)          # 第一次点开试读的时刻；NULL = 从没试读过
    progress_seq:Mapped[int]=mapped_column(Integer,default=0)                           # 连续读过的最大章节序号（只增不减，跳着读不推进）
    progress_ratio:Mapped[float]=mapped_column(Float,default=0)                         # 当前这一章读到哪儿，0~1；和 seq 合起来 = 「读到 50.5%」
    in_shelf:Mapped[bool]=mapped_column(Boolean,default=False)                # 在不在书架里；试读过的行留在表里，但不在书架
    # 关系（不占数据库列）：多对一，一条书架记录只对应一个用户 / 一本书
    user:Mapped["User"]=relationship(back_populates="shelves")                # ↔ User.shelves
    book:Mapped["Book"]=relationship(back_populates="shelves")                # ↔ Book.shelves

class Readinglogs(base):
    """阅读日志：一次「开始读 → 结束读」的上报 = 一行，只用于统计阅读时长。

    和书架行的区别：
        - user_book 是「状态」（当前进度、在不在书架），每本书只有一行；
        - Readinglogs 是「流水」（历史记录），同一本书可以有无数行。
    所以这里不能加 (user_id, book_id) 唯一约束。
    """
    __tablename__="reading_logs"
    # 统计「我的阅读时长」时按 user_id + 时间范围扫，走这个联合索引
    __table_args__ = (
    Index("ix_reading_logs_user_started", "user_id", "started_at"),
)
    id:Mapped[int]=mapped_column(Integer,primary_key=True) # 主键
    # 两个外键：谁读的、读的哪本书 —— 和 users / books 建立多对一关系
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)   # 谁读的
    book_id:Mapped[int]=mapped_column(ForeignKey("books.id"),index=True)   # 读的哪本书
    started_at:Mapped[datetime ]=mapped_column(DateTime) # 这次阅读的开始时刻
    ended_at:Mapped[datetime ]=mapped_column(DateTime) # 这次阅读的结束时刻
    seconds:Mapped[int]=mapped_column(Integer) # 这次阅读的时长（秒）；由结束减开始得出
    # 关系（不占数据库列）：反向分别在 User.readinglogs / Book.readinglogs
    user:Mapped["User"]=relationship("User",back_populates="readinglogs")   # ↔ User.readinglogs
    book:Mapped["Book"]=relationship("Book",back_populates="readinglogs")   # ↔ Book.readinglogs
