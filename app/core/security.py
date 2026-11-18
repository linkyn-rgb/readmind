"""密码哈希与 JWT 签发 / 校验（认证的最底层工具，不含任何路由逻辑）。

    hash_password / verify_password   bcrypt，注册 / 登录用
    create_token                      签发 HS256 JWT，payload 带 sub / iat / exp / jti
    decode_token                      验签 + 验过期，只返回 user_id

这些函数是纯工具：不查库、不抛 HTTPException —— 转 401 的活由 dep.py 做。
"""
import bcrypt
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings
def hash_password(raw:str):
    """明文 → bcrypt 哈希（注册时用）。"""
    # bcrypt 只认前 72 字节，超了会静默截断（等于两个长密码可能一样），所以显式报错
    if len(raw.encode("utf-8"))>72:
        raise ValueError("密码太长,要求72字节以内")
    return bcrypt.hashpw(raw.encode("utf-8"),bcrypt.gensalt()).decode("utf-8")
def verify_password(raw:str,hashed:str):
    """登录时校验：明文 + 库里的哈希 → True/False。"""
    return bcrypt.checkpw(raw.encode("utf-8"),hashed.encode("utf-8"))
def create_token(user_id:int)-> str:
    """签发 JWT。"""
    now=datetime.now(timezone.utc)
    payload={
        "sub":str(user_id),   # subject：JWT 规范要求字符串，所以 int 要转
        "iat":now,            # 签发时间
        "exp":now+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),  # 过期时间
        "jti":str(uuid4())    # 唯一编号：登出时拿它进 Redis 黑名单
    }
    return jwt.encode(payload,settings.SECRET_KEY,algorithm="HS256")
def decode_payload(token:str)->dict:
    """验签 + 校验过期，返回完整 claims（`sub` / `iat` / `exp` / `jti`）。

    失败抛 jwt.PyJWTError，由调用方统一转 401。
    单独留这个入口，是因为登出需要 `jti`（黑名单的 key）和 `exp`（算 TTL），
    而只查用户的地方只要 `sub` —— 两处共用一次验签，不重复解。
    """
    return jwt.decode(token,settings.SECRET_KEY,algorithms=["HS256"])
def decode_token(token:str):
    """只要 user_id 的场景用它；返回 int，失败同样抛 jwt.PyJWTError。"""
    return int(decode_payload(token)["sub"])
