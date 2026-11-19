"""题材出参（第 2 步）：自嵌套的树节点，嵌套在 bookout 里。"""
from pydantic import BaseModel,ConfigDict
class Categoryout(BaseModel):
      """题材树节点：children 是同样结构的列表，能无限往下套（现在只用到两层）。"""
      model_config = ConfigDict(from_attributes=True)
      id: int                              # 分类 id
      name: str                            # 分类名
      parent_id:int | None=None            # 父分类 id；None = 顶层大类
      children:list["Categoryout"]=[]      # 子分类；字符串前向引用：类还没定义完，引用自己只能写字符串
