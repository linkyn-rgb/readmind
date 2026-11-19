# 模型必须在这里显式导出：不 import 的模型不会进 Base.metadata，建表时会被漏掉
from app.models.Book import Book
from app.models.User import User
from app.models.Category import Category,book_categories,book_sources
from app.models.Sources import Source
from app.models.Tags import Tags,book_tags
from app.models.Shelf import user_book,Readinglogs
from app.models.BorrowRecord import BorrowRecord
from app.models.Chapter import Chapter
from app.models.Review import Review
