"""借阅流水（第 6 步）—— 每次借 / 还 / 续都落在这张表上。

契约正本 = 设计文档 §二 borrows。字段归属（谁写、能不能空）：

    id            服务端自增
    user_id       服务端从 token 取（客户端不能传）
    book_id       客户端传（借哪一本）
    borrowed_at   服务端 datetime.now()
    due_at        服务端算 = borrowed_at + 借期天数，客户端不能传
    returned_at   还书时服务端填，可空
    renew_count   建行时 0，续借 +1

⚠️ 这些是**业务规则**，不属于建表，写在路由里：
    - due_at 必须服务端算（让客户端传到期日 = 用户可以自己借十年）；
    - renew_count 上限 3；
    - 逾期 12 小时内仍可续；
    - 借阅 + 书架 in_shelf=True 必须同一个事务提交。
  表上只存数字，不存「借阅中 / 逾期 / 已还」—— 那是按 returned_at / due_at 现算的。
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import base

# 只给类型检查用。运行时 import 会成环：User.py / Book.py 对这里是运行时 import，
# 三个文件必须只有一个方向的运行时引用（样板是 Shelf.py）。
if TYPE_CHECKING:
    from app.models.Book import Book
    from app.models.User import User


class BorrowRecord(base):
    __tablename__ = "borrows"
    # 权限判断每次都按「我 + 这本书 + 还没还」查，这两条联合索引专供那条查询
    __table_args__ = (
        Index("ix_borrows_user_returned", "user_id", "returned_at"),
        Index("ix_borrows_user_book_returned", "user_id", "book_id", "returned_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)               # 主键

    # 外键：谁借的、借的哪本
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))            # 借阅人；从 token 取
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))            # 借的哪本书

    # 时间三件套：只有 returned_at 可空（NULL = 还没还）
    borrowed_at: Mapped[datetime] = mapped_column(DateTime)                 # 借出时刻（服务端写）
    due_at: Mapped[datetime] = mapped_column(DateTime)                      # 应还时刻（服务端算，不可空）
    returned_at: Mapped[datetime | None] = mapped_column(DateTime)          # 归还时刻（还书时填）

    # 续借次数：建行时 0；「上限 3」是路由里的判断，不建成数据库约束
    renew_count: Mapped[int] = mapped_column(Integer, default=0)            # 已续借次数（上限 3 由路由判断）

    # 关系（不占数据库列）：一条借阅 ↔ 一个用户 / 一本书
    # 反向在 User.borrow_records / Book.borrow_records，名字必须成对，单复数错了 mapper 直接起不来
    user: Mapped["User"] = relationship(back_populates="borrow_records")   # ↔ User.borrow_records
    book: Mapped["Book"] = relationship(back_populates="borrow_records")   # ↔ Book.borrow_records
