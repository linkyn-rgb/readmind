"""标签出参（第 2 步）：只有 id + name，嵌套在 bookout 里。"""
from pydantic import BaseModel,ConfigDict
class tagsout(BaseModel):
    """标签输出：只有 id + 名称，嵌套在 bookout 里。"""
    model_config = ConfigDict(from_attributes=True)
    id:int      # 标签 id
    name:str    # 标签名（自由词，只喂推荐，不做筛选入口）
