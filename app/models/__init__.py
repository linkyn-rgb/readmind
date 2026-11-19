# 模型必须在这里显式导出：不 import 的模型不会进 Base.metadata，建表时会被漏掉
# 当前切片：第 1 步 User + 第 2 步 Book；其余模型随步骤并入
from app.models.User import User
from app.models.Book import Book
