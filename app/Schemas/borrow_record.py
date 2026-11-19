"""借阅接口的入参 / 出参（第 6 步）。

契约正本 = 设计文档 §三 借阅。四个接口里只有前两个需要 schema：

    POST /borrows            借书   → borrowrecord_create（入参）/ borrowrecord_out（出参）
    GET  /borrows            流水   → borrowrecord_out
    POST /borrows/{id}/renew 续借   → 无入参、无出参
    POST /borrows/{id}/return 还书  → 无入参、无出参

⚠️ 留给路由的业务判断（这里不实现）：
    - 续借：renew_count < 3、已还不能续、逾期超过 12 小时不能续 → 409；
    - 还书：已经还过 → 409；提前归还只影响派生字段 is_early_return，天数照给；
    - 借阅不存在或不是自己的 → 404。
"""
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.Schemas.book import book_brief


class borrowstatus(StrEnum):
    """借阅状态：不存库，按 returned_at / due_at 现算（设计文档 §二 borrows）。"""
    BORROWING = "borrowing"   # 未还，且 现在 < due_at
    OVERDUE = "overdue"       # 未还，且 现在 >= due_at
    RETURNED = "returned"     # returned_at 有值


class borrowrecord_create(BaseModel):
    """POST /borrows 入参。

    user_id / borrowed_at / due_at / renew_count 全部由服务端生成，客户端传不进来。
    """
    model_config = ConfigDict(extra="forbid")   # 传 user_id / due_at 之类的字段直接 422，不给越权留缝
    book_id: int = Field(gt=0)                  # 书号必须是正整数（0 / 负数查不到书，进路由前就挡掉）
    # 借期只有四档（10-10 定）。用 Literal 让 FastAPI 在进路由前就 422，
    # 业务层不用再判 —— 契约里写的「其他值 → 422」就是靠这一行挡下的。
    days: Literal[3, 7, 14, 30]


class borrowrecord_out(BaseModel):
    """GET /borrows 单条，也是 POST /borrows 的出参。前六个是库里的列，后三个现算。"""
    model_config = ConfigDict(from_attributes=True)   # 直接读 ORM 对象的属性

    id: int                         # 借阅流水 id（续借 / 还书的路径参数就是它）
    book: book_brief                # 嵌套书籍简版（id / title / author / cover），不是 book_id
    borrowed_at: datetime           # 借出时刻；服务端写
    due_at: datetime                # 应还时刻；服务端算 = borrowed_at + 借期天数
    returned_at: datetime | None = None   # 空 = 还没还（库里唯一可空的时间列）
    renew_count: int                # 已续借次数

    # ── 下面三个是派生字段：库里没有列，路由算完再赋值 ──────────────────────
    # 契约要求出参一定有值；这里留 None 默认值，是因为路由的写法是
    # 「先 model_validate(ORM 行)、再补这三个字段」—— 字段写成必填会在 validate 那一步
    # 当场 500（ORM 行上根本没有这些属性）。等值补上之后，响应里就不是 null 了。
    days_borrowed: int | None = None       # 借了几天：已还 = returned_at − borrowed_at，未还 = 现在 − borrowed_at（不足一天算 1）
    is_early_return: bool | None = None    # returned_at 有值且早于 due_at
    status: borrowstatus | None = None     # borrowing / overdue / returned
