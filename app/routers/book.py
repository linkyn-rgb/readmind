"""图书接口（第 2 步）：列表 / 搜索 / 榜单占位 / 详情 / 新增（删除待做）。

挂载前缀 = /books。路由顺序有讲究：固定的 /search、/ranking 必须写在 /{book_id} 前面，
否则 "search" 会被当成 book_id 去解析。

当前是第 2 步的切片：只含 books 表本身的读写。
- 按题材 / 来源筛选（依赖第 3 步的分类与来源表）
- 新增时的分类 / 来源校验（同上）
- status 借阅状态（依赖第 6 步的 borrows 表）
这三块在对应模块并入时再补回来（补的代码以完整工程为准）。
"""
from fastapi import APIRouter,HTTPException,Depends,status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.Book import Book
from app.Schemas.book import bookout,bookcreate,listbook
from sqlalchemy import func
router=APIRouter()

@router.get("/",response_model=listbook)
def list_book(page:int=1,size:int=20,db:Session=Depends(get_db)):
    """图书列表：分页。"""
    stmt = select(Book)
    num = db.scalar(select(func.count()).select_from(stmt.subquery()))   # 总数单独查（分页要用）
    book = db.scalars(stmt.order_by(Book.id).limit(size).offset((page-1)*size)).all()
    return {"items":book,"total":num}

@router.get("/search")
def search_book(q:str,db:Session=Depends(get_db)):
    """按书名或作者模糊搜索（contains → LIKE '%q%'）。没分页，做搜索页时再补。"""
    book=db.scalars(select(Book).where(Book.title.contains(q) | Book.author.contains(q))).all()
    return book

# 固定的 /search、/ranking 必须写在 /{book_id} 前面；反过来写的话 "search" 会被当成 book_id
@router.get("/ranking")
def ranking(page:int=1,size:int=20,db:Session=Depends(get_db)):
    """榜单占位（第 9 步才做真实榜单）,TODO offset(page) 应为 (page-1)*size；而且现在没 return。"""
    # ⚠️ 查出来了却没有 return → 这个接口现在实际返回 null。
    #    补榜单时记得 return book；顺带把「按什么排序」定下来（现在只是按 id）。
    book=db.scalars(select(Book).order_by(Book.id).limit(size).offset((page-1)*size)).all()

@router.get("/{book_id}",response_model=bookout)
def get_book(book_id:int,db:Session=Depends(get_db)):
    """图书详情；不存在返回 404。"""
    books=db.get(Book,book_id)
    if books is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,detail="不存在此书")
    return books

@router.post("/",response_model=bookout)
def create_book(data:bookcreate,db:Session=Depends(get_db)):
    """新增图书：books 表本体的字段。"""
    book=Book(**data.model_dump())   # 只构造对象，还没进数据库；此时 book.id 是 None
    db.add(book)      # 把对象放进 session，等 commit 一起写
    db.commit()       # 落库
    db.refresh(book)  # commit 会过期化对象，重新读一遍拿到数据库生成/刷新的值（id 等）
    return book
