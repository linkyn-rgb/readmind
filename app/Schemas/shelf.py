"""书架接口的入参 / 出参（第 5 步）。

    GET    /user/books          → list[user_book_out]
    POST   /user/books/{id}     → user_book_out
    DELETE /user/books/{id}     → 204，无出参

user_book_out 里的 section 是派生字段：库里没有这一列，
路由按阅读进度现算后再填进去（见 routers/user.py 的 classify）。
"""
from pydantic import BaseModel,ConfigDict,Field,model_validator
from datetime import datetime,timedelta
from app.Schemas.book import book_brief
from enum import StrEnum
class user_book_creat(BaseModel):
    """加入书架的请求体（目前路由只用路径参数 book_id，这个类暂时没用上）。"""
    model_config = ConfigDict(from_attributes=True,extra="forbid")
    book:book_brief   # 要加入书架的书（简版：id / title / author / cover）

class shelfsection(StrEnum):
    """书架四个分区。用途：GET /user/books?section=reading 这类过滤参数。"""
    WISH = "wish"          # 想读
    READING = "reading"    # 在读
    FINISHED = "finished"  # 已读完
    PAUSED = "paused"      # 读过但没读完

class user_book_out(BaseModel):
    """书架卡片：一本书在「我的书架」里要显示的信息。

    还缺书名、封面、作者 —— 书架页肯定要用，后面得补（要从 books 表 join 出来）。
    ⚠️ 这里已经通过 book: book_brief 把书名 / 作者 / 封面都带出来了，
    上面那句是早期备注，可以视为已解决。
    """
    model_config = ConfigDict(from_attributes=True)
    book:book_brief                     # 嵌套书的简版：书名 / 作者 / 封面
    id:int                              # user_books 行 id
    added_at:datetime  | None # 加入书架时间（「想读」区按它排）
    trial_started_at:datetime | None=None # 第一次试读时间；None = 没试读过
    progress_ratio:float | None=None # 当前这一章读到的位置 0~1（前端显示「全书 X%」还要配上 seq）
    progress_seq:int | None=None #页数
    section:shelfsection| None=None      # 属于哪个分区；库里不存，路由用 classify 现算后填

class progress_update(BaseModel):
    """PUT /books/{id}/progress 的请求体：当前所在章 + 这一章读到哪儿。

    book_id 走路径、user_id 走 token，都不进请求体（extra="forbid" 挡掉）。
    这里只卡 Pydantic 能卡的：seq ≥ 1、ratio ∈ [0, 1]。
    上半界（seq 不能超过全书章数）要查 chapters 表，留给路由；
    「只增不减」和「seq 变小时整个忽略」也是路由的事，schema 管不了。
    """
    model_config = ConfigDict(extra="forbid")
    seq: int = Field(ge=1)          # 当前所在章的序号，从 1 开始
    ratio: float = Field(ge=0, le=1)  # 这一章读到哪儿，0~1


class readinglogs_create(BaseModel):
    """POST /books/{id}/reading 的请求体：一次阅读的开始 / 结束时刻。

    book_id 走路径、user_id 走 token、seconds 服务端算 —— 三者都不进请求体。
    ended_at 早于 started_at、或单次超过 24h，都在 schema 层直接 422。
    """
    model_config = ConfigDict(extra="forbid")   # 传 user_id / book_id 之类直接 422
    started_at:datetime   # 这次阅读的开始时刻（客户端从阅读器带上来）
    ended_at:datetime     # 这次阅读的结束时刻

    @model_validator(mode="after")
    def check_window(self):
        span = self.ended_at - self.started_at
        if span < timedelta(0):
            raise ValueError("ended_at 不能早于 started_at")
        if span > timedelta(hours=24):
            raise ValueError("单次阅读上报不能超过 24 小时")
        return self

class readinglogs_out(BaseModel):
    """阅读记录出参：一条记录 + 它对应的书（book_brief）。"""
    model_config = ConfigDict(from_attributes=True)
    id:int                # 阅读日志 id
    book:book_brief       # 读的哪本书（简版）
    started_at:datetime   # 开始时刻
    ended_at:datetime     # 结束时刻
    seconds:int           # 时长（秒）；由 ended_at − started_at 服务端算
