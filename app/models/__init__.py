# 模型必须在这里显式导出：不 import 的模型不会进 base.metadata，建表时会被漏掉
# 开端切片：当前只有 User，其余模型随第 2–8 步并入
from app.models.User import User
