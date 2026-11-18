"""用户表（第 1 步）。

一行 = 一个账号。登录、借阅、书架、阅读日志都通过 user_id 挂在这儿。
account 才是登录账号；nickname 只用于展示。

开端切片说明：完整版的 User 还有 shelves / readinglogs / borrow_records / reviews
四个反向关系（分别指向书架、阅读流水、借阅、评价记录），随第 5–8 步一起并入；
这里只留账号本体，避免引用尚未存在的表。
"""
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import base


class User(base):
    """账号与个人资料。登录、借阅、书架、统计都挂在这个 id 上。"""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)                # 主键；借阅 / 书架 / 评价都挂在它上面
    account: Mapped[str] = mapped_column(String(200), unique=True)  # 登录账号，唯一；登录用它，不是 nickname
    password: Mapped[str] = mapped_column(String(500))              # 密码哈希（bcrypt），不存明文
    nickname: Mapped[str] = mapped_column(String(200))              # 昵称；展示用，允许重名
    bio: Mapped[str | None] = mapped_column(String(200))            # 个性签名
    email: Mapped[str] = mapped_column(String(200))                 # 邮箱
    phone: Mapped[str] = mapped_column(String(500))                 # 手机号
    avatar: Mapped[str | None] = mapped_column(String(200))         # 头像路径；可空性由 Mapped[... | None] 推导，不用再传 None
    goal: Mapped[int | None] = mapped_column(Integer)               # 阅读目标（设计文档口径：整数）
    remind: Mapped[bool] = mapped_column(Boolean, default=False)    # 阅读提醒开关
    notify: Mapped[bool] = mapped_column(Boolean, default=False)    # 系统通知开关
