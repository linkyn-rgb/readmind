"""图书相关 Schema（第 2 步）：新增 / 部分更新 / 列表出参 / 简版出参。

四个类各司其职：
    bookcreate   POST /books 的请求体（title/author 必填，分类来源传 id 列表）
    bookupdate   PATCH 用，全字段可选（接口还没写）
    bookout      列表项 / 详情出参（嵌套 categories / sources / tags）
    book_brief   被借阅、书架、阅读日志复用的「简版书」：只有 id/title/author/cover
    listbook     分页包装 {items, total}
"""
from pydantic import BaseModel,ConfigDict,Field
from app.Schemas.categoryout import Categoryout
from app.Schemas.sources import Sources
from app.Schemas.tags import tagsout


# 模型类（models）管「怎么存库」，Schema 管「接口收什么、返回什么」
class bookupdate(BaseModel):
    """部分更新用：所有字段可选，只传要改的。"""
    model_config = ConfigDict(extra="forbid")   # 传了没定义的字段直接 422，避免「以为改了其实没改」
    title: str | None = Field(default=None,min_length=1,max_length=200)    # 书名；不传 = 不改
    author: str | None = Field(default=None,min_length=1,max_length=200)   # 作者；不传 = 不改

class bookout(BaseModel):
    """图书列表项 / 详情（响应）。"""
    model_config = ConfigDict(from_attributes=True)   # 允许直接读 ORM 对象的属性（book.title），不用先转 dict
    id:int                                     # 书号
    title:str                                  # 书名
    author:str                                 # 作者
    isbn:str | None=None                       # ISBN；可能没有
    desc:str | None=None                       # 简介
    categories:list[Categoryout] | None=None   # 嵌套题材（树节点，自带 children）
    sources:list[Sources] | None=None          # 嵌套来源
    tags:list[tagsout] | None=None             # 嵌套标签
    # 第 8 步新增：平均评分。库里不存，由详情路由从 reviews 表现算后填；
    # 没评价过的书是 None。列表接口不填，保持 None。
    rating:float | None=None

    # ── 第 9 步（接前端）新增：书的当前借阅状态 ────────────────────────────
    # 派生字段：books 表没有这一列，值是接口层查 borrows 表算出来的。
    #   'ok'  = 在架（没有任何未归还的借阅记录）
    #   'out' = 借走了（有人借着还没还；逾期未还也算 out —— 书在读者手里，不在架上）
    #
    # 为什么默认 None 而不是 'ok'：
    #   读 ORM 对象时对象上根本没有 status 这个属性，Pydantic 只能落默认值。
    #   如果默认成 'ok'，「忘了赋值」和「确实在架」就分不出来了。
    #   留 None = 接口没填，前端按「未知」处理，问题能暴露出来。
    #
    # 谁负责填：book.py 的 list_book / get_book / create_book 三个路由。
    #   列表和详情用 _borrowed_book_ids() 一次查集合再逐本打标；
    #   新建的书必然没有借阅记录，直接 'ok'。
    status:str | None=None

class bookcreate(BaseModel):
    """新增图书（请求）。"""
    model_config = ConfigDict(extra="forbid")   # 多余字段 422；isbn/desc 这类可选字段要显式传
    title: str = Field(min_length=1,max_length=200)   # 书名，必填
    author: str = Field(min_length=1,max_length=200)  # 作者，必填
    isbn:str | None=None                              # ISBN，可不传
    desc:str | None=None                              # 简介，可不传
    category_ids:list[int]=Field(default_factory=list)   # 传 id 列表；服务端查成 Category 对象再 append 到关系里
    source_ids:list[int]=Field(default_factory=list)     # 来源 id 列表；服务端查成 Source 对象再挂关系
class listbook(BaseModel):
    """分页包装：items = 这一页的数据，total = 总数（前端算「共几页」用）。"""
    items:list[bookout]   # 这一页的书
    total:int             # 符合条件的总数（不是这一页的条数）

class book_brief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int                    # 书号
    title:str                 # 书名
    author:str                # 作者
    cover:str | None = None   # 封面路径；库里的 cover 可空（还没上传封面的书），出参必须跟着放宽