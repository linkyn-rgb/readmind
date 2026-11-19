"""来源出参（第 2 步）：只有 id + name，既用于 /sources 列表，也嵌套在 bookout 里。"""
from pydantic import BaseModel,ConfigDict
class Sources(BaseModel):
    """来源输出：只有 id + 名称，嵌套在 bookout 里。"""
    model_config = ConfigDict(from_attributes=True)
    id:int      # 来源 id
    name:str    # 来源名（日本轻小说 / 中国轻小说 / 名著 / 中国长篇 / 中国短篇）
