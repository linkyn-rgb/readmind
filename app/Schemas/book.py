"""图书相关 Schema（第 2 步）：新增 / 部分更新 / 列表出参 / 简版出参。

四个类各司其职：
    bookcreate   POST /books 的请求体（title/author 必填）
    bookupdate   PATCH 用，全字段可选（接口还没写）
    bookout      列表项 / 详情出参
    book_brief   被借阅、书架、阅读日志复用的「简版书」：只有 id/title/author/cover
    listbook     分页包装 {items, total}

当前是第 2 步的切片：只含 books 表本身的字段。
categories / sources / tags（第 3、4 步）、rating（第 8 步）、status（第 6 步借阅）
这些跨表字段在对应模块并入时再补回来（补的代码以完整工程为准）。
"""
from pydantic import BaseModel,ConfigDict,Field


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

class bookcreate(BaseModel):
    """新增图书（请求）。"""
    model_config = ConfigDict(extra="forbid")   # 多余字段 422；isbn/desc 这类可选字段要显式传
    title: str = Field(min_length=1,max_length=200)   # 书名，必填
    author: str = Field(min_length=1,max_length=200)  # 作者，必填
    isbn:str | None=None                              # ISBN，可不传
    desc:str | None=None                              # 简介，可不传

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
