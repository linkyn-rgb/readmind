"""注册请求体（第 3 步的早期版本，已被 auth.py 里的 RegisterBody 取代）。"""
from pydantic import BaseModel,ConfigDict,Field,field_validator
class RegisterBody(BaseModel):
    """注册请求体。注意字段含义错位：username 实际存进 nickname，account 才是登录账号。"""
    model_config = ConfigDict(extra="forbid")   # 多余字段 422，避免客户端把 id / goal 之类塞进来
    username:str = Field(min_length=3,max_length=50)   # 昵称
    password:str = Field(min_length=6,max_length=72)   # 字符数上限；真正的 72 字节上限见下面的校验

    @field_validator("password")
    @classmethod
    def check_bcrypt_bytes(cls, v: str) -> str:
        """bcrypt 5.x 按【字节】限 72，超过直接抛 ValueError（→ 500）。

        上面的 max_length 数的是字符：25 个汉字只有 25 个字符，却是 75 字节。
        所以必须再按编码后的长度卡一道，让它在 422 层就被拒掉。
        """
        if len(v.encode("utf-8")) > 72:
            raise ValueError("密码超过 72 字节（一个汉字算 3 个字节），请缩短")
        return v
    account:str=Field(min_length=6,max_length=72)      # 登录账号
    phone:str=Field(min_length=6,max_length=72)
    email:str=Field(min_length=6,max_length=72)
