"""注册请求体（第 3 步的早期版本，已被 auth.py 里的 RegisterBody 取代）。"""
from pydantic import BaseModel,ConfigDict,Field
class RegisterBody(BaseModel):
    """注册请求体。注意字段含义错位：username 实际存进 nickname，account 才是登录账号。"""
    model_config = ConfigDict(extra="forbid")   # 多余字段 422，避免客户端把 id / goal 之类塞进来
    username:str = Field(min_length=3,max_length=50)   # 昵称
    password:str = Field(min_length=6,max_length=72)   # bcrypt 上限 72 字节，正好当上限
    account:str=Field(min_length=6,max_length=72)      # 登录账号
    phone:str=Field(min_length=6,max_length=72)
    email:str=Field(min_length=6,max_length=72)
