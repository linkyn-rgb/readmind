"""用户表（第 3 步）。

一行 = 一个账号。登录、借阅、书架、阅读日志都通过 user_id 挂在这儿。
account 才是登录账号；nickname 只用于展示。
"""
from sqlalchemy import String,Integer,Boolean,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.database import base
from app.models.Shelf import user_book,Readinglogs
from app.models.BorrowRecord import BorrowRecord
from app.models.Review import Review

class User(base):
    """账号与个人资料。登录、借阅、书架、统计都挂在这个 id 上。"""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)                # 主键；借阅 / 书架 / 评价都挂在它上面
    account:Mapped[str]=mapped_column(String(200),unique=True)       # 登录账号，唯一；登录用它，不是 nickname
    password:Mapped[str]=mapped_column(String(500))                  # 密码哈希（bcrypt），不存明文
    nickname:Mapped[str]=mapped_column(String(200))                  # 昵称；展示用，允许重名
    bio:Mapped[str | None]=mapped_column(String(200))                # 个性签名
    email:Mapped[str]=mapped_column(String(200))                     # 邮箱
    phone:Mapped[str]=mapped_column(String(500))                     # 手机号
    avatar:Mapped[str | None]=mapped_column(String(200))     # 头像路径；可空性由 Mapped[... | None] 推导，不用再传 None
    goal:Mapped[int | None]=mapped_column(Integer)              # 阅读目标（设计文档口径：整数；库里已 ALTER 成 INT NULL）
    remind:Mapped[bool]=mapped_column(Boolean,default=False)         # 阅读提醒开关
    notify:Mapped[bool]=mapped_column(Boolean,default=False)         # 系统通知开关
    # 反向关系（不占数据库列）：一个用户有多条书架记录，所以是 list
    shelves:Mapped[list["user_book"]]=relationship(back_populates="user")   # ↔ user_book.user
    readinglogs:Mapped[list["Readinglogs"]]=relationship(back_populates="user")   # ↔ Readinglogs.user
    borrow_records:Mapped[list["BorrowRecord"]]=relationship(back_populates="user")   # ↔ BorrowRecord.user
    reviews:Mapped[list["Review"]]=relationship(back_populates="user")                # ↔ Review.user；这个人写过的全部评价
