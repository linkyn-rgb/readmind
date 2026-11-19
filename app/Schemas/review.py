"""评价接口的入参 / 出参（第 8 步）。

契约正本 = 设计文档 §三 评价：

    POST /reviews              → ReviewCreate（入参）；出参设计文档写「—」，由路由决定
    GET  /books/{id}/reviews   → ReviewList（分页：items + total）

这里只卡 Pydantic 能卡的：rating ∈ [1, 5]、content 非空、拒绝多余字段。
留给路由的判断（schema 管不了）：
    - 半本书 → 400 `BOOK_NO_CONTENT`；
    - 进度 < 50% → 403 `NOT_READ_ENOUGH`（必须调 core 的 progress_fraction()，别在路由里另写公式）；
    - 同一本书第二次评价 → 409 `REVIEW_EXISTS`
      （应用层先查一次给友好提示，DB 唯一约束兜底并捕获 IntegrityError）。
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    """POST /reviews 的请求体。

    user_id / created_at 由服务端生成，客户端传不进来（extra="forbid" 直接 422）。
    """
    # str_strip_whitespace：所有字符串先去掉首尾空白再校验，
    # 这样「只敲几个空格」的 content 会在 min_length 那关被挡下，而不是存一堆空白进库
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    book_id: int = Field(gt=0)          # 评哪本书；0 / 负数进路由前就 422
    rating: int = Field(ge=1, le=5)     # 评分 1~5；和表上的 CHECK 约束同一口径
    content: str = Field(min_length=1, max_length=2000)  # 评价正文；2000 是防灌水的服务端上限（设计文档未规定，嫌紧调这一个数）


class ReviewerBrief(BaseModel):
    """评价人简版：列表里只显示昵称和头像，不把整个 User 吐出去。

    ⚠️ 查询评价列表时记得 selectinload(Review.user)，否则每行再查一次用户 → N+1。
    """
    model_config = ConfigDict(from_attributes=True)
    id: int                          # 评价人 id（前端以后要做「点进主页」时用）
    nickname: str                    # 昵称；展示用
    avatar: str | None = None        # 头像路径；没上传时是 None，前端给默认头像


class ReviewOut(BaseModel):
    """GET /books/{id}/reviews 列表里的一条。

    不含 book_id：这个列表本来就是「某本书的评价」，书是路径参数，重复一遍没意义。
    也不含 user_id：需要的话用 user.id。
    """
    model_config = ConfigDict(from_attributes=True)
    id: int                          # 评价 id，前端当列表 key
    user: ReviewerBrief              # 评价人（昵称 + 头像）
    rating: int                      # 1~5 星
    content: str                     # 评价正文
    created_at: datetime             # 评价时间


class ReviewList(BaseModel):
    """分页包装：items = 这一页的评价，total = 总条数（前端算「共几页」用）。

    和图书列表的 listbook 同一个形状，前端分页组件可以复用。
    """
    items: list[ReviewOut]           # 这一页的数据
    total: int                       # 满足条件的总条数（不是这一页的条数）
