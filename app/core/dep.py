"""鉴权依赖：从请求头取出 JWT → 验签 → 查库 → 拿到当前用户。

路由里写 user: User = Depends(get_current_user) 就表示「这个接口必须登录」。
失败一律 401，不区分 token 无效 / 过期 / 用户不存在 —— 前端不需要这些差别。
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.core.security import decode_payload
from app.core.redis import get_redis
from redis.exceptions import RedisError
import jwt
import logging
logger = logging.getLogger(__name__)   # 降级时用它记：logger.warning("Redis 不可用，黑名单未校验，放行")

# Bearer 方案：从请求头 Authorization: Bearer <token> 里取出 token。
# tokenUrl 只是给 Swagger 文档的 Authorize 按钮用，指向登录接口
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")
def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    """登录校验依赖：解析 token → 查黑名单 → 查库 → 返回当前 User。

    任何接口写 user: User = Depends(get_current_user) 就自动要求登录。
    """
    # 所有失败情况统一返回同一个 401：token 无效 / 过期 / 用户不存在，前端不用分辨
    credentials_error=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="登录状态无效或已过期",
                                    headers={"WWW-Authenticate": "Bearer"})
    try:
        payload=decode_payload(token)   # 一次验签拿全 claims：sub 和 jti 都要用
        user_id=int(payload["sub"])
    except jwt.PyJWTError:
        raise credentials_error

    # 黑名单检查：验签通过只证明 token 没被改、没过期，不代表没登出过
    # 降级口径 = fail-open：try 只包住 Redis 这一次调用，
    # 挂了就记一行日志放行，不能让 Redis 故障把所有人挡在门外
    jti=payload.get("jti")
    try:
        # 命中即说明这张 token 已登出，返回和验签失败同一个 401
        if jti and get_redis().exists(f"blacklist:{jti}"):
            raise credentials_error
    except RedisError:
        logger.warning("Redis 不可用，黑名单未校验，放行 jti=%s",jti)

    user=db.get(User,user_id)         # token 里有 user_id，但用户可能已经被删了
    if user is None:
        raise credentials_error
    return user
# 管理员依赖暂时注释掉：User 模型上还没有 is_admin 字段（相关取舍见 FastAPI 学习进度）
# def get_current_admin(user: User = Depends(get_current_user)):
#     if not user.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="需要管理员权限",
#         )
#     return user
