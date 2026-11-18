"""认证接口（第 3 步）：登录 / 注册 / 登出。

挂载方式见 main.py：同一个 router 被挂了两次（/user 和 /auth），
所以 /auth/login 和 /user/login 都能用，接前端时最好只留一套。
"""
from fastapi import APIRouter,Depends,HTTPException,status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.core.security import verify_password,create_token,decode_payload
from pydantic import BaseModel, ConfigDict, Field
from app.core.security import hash_password
from app.core.dep import get_current_user
from app.core.redis import get_redis
from app.core.dep import oauth2_scheme
from app.Schemas.register import RegisterBody
import jwt
import time
router=APIRouter()

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """登录：表单的 username 字段拿来查 account 列，成功返回 JWT。

    为什么用 OAuth2PasswordRequestForm：Swagger 右上角 Authorize 按钮
    就是按 OAuth2 密码流发请求的，用它才能在 /docs 里直接点着登录。
    注意表单字段叫 username，但库里对应用的是 account（不是 nickname）。
    """
    user=db.scalar(select(User).where(User.account==form.username))
    if user is None or not verify_password(form.password,user.password):
        # 账号不存在和密码错误返回同一句：不暴露「这个账号存在」
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="用户名或密码错误")
    # 出参是 OAuth2 规范形状：access_token + token_type
    return {"access_token": create_token(user.id), "token_type": "bearer"}


@router.post("/register",status_code=201)
def register(body:RegisterBody,db:Session=Depends(get_db)):
    """注册：昵称查重；account 的重复交给数据库唯一索引（撞了会 500，后面要改成 400）。

    这里查重查的是 nickname，不是 account —— 因为 nickname 展示用、允许重名本来是设计，
    但代码当前把它当唯一名用了。等做「账号唯一」时，这里要改成查 account，
    并且捕获 IntegrityError 转成 400，别让唯一索引冲突冒成 500。
    """
    exists=db.scalar(select(User).where(User.account==body.username))
    if exists is not None:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    # 密码只存哈希，绝不存明文
    user=User(nickname=body.username, password=hash_password(body.password),account=body.account,phone=body.phone,email=body.email)
    db.add(user)
    db.commit()      # 写库
    db.refresh(user) # commit 后重新读一次，拿到自增 id
    return {"id": user.id, "username": user.nickname,"phone":user.phone,"email":user.email}
# 登出：把 jti 存进 Redis 黑名单，TTL = token 剩余有效期
# （Redis 写法见桌面「FastAPI教程/Redis语法速查.md」§12）
@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    """登出：把这个 token 的 jti 记进黑名单，之后再拿它请求就是 401。

    为什么依赖用 oauth2_scheme 而不是 get_current_user：
      get_current_user 马上也要查黑名单，拿它做登出会变成「登出过一次就
      再也登不出去」——第二次直接被自己的黑名单挡成 401。这里只验签，
      不查库、不查黑名单，重复登出要能成功（幂等）。

    步骤：
      1. decode_payload(token) → 完整 claims（sub / iat / exp / jti）
         （decode_token 只返回 int，这里不能用）
      2. ttl = exp - 当前时间戳；ttl <= 0 说明 token 本来就过期了，不用写黑名单
      3. 把 jti 写进 blacklist:<jti>，TTL 用第 2 步的值，一次带上
      4. 返回

    两个点你定：
      - 状态码：草稿里的 201 是「创建了资源」的意思，登出不合适；
        200 带 body 还是 204 不带，你拍。
      - token 无效 / 已过期时 decode_payload 会抛 jwt.PyJWTError，
        不接住就是 500 —— 接成 401 还是直接也算登出成功，你拍。
      - Redis 不可用时怎么办：跟 dep.py 那边的降级口径保持一致
        （fail-open 还是报错），拍完在两个文件里写成同一句话。
    """
    credentials_error = HTTPException(status_code=401, detail="登录状态无效或已过期", headers={"WWW-Authenticate": "Bearer"})
    try:
      payload = decode_payload(token)

    except jwt.PyJWTError:
        raise credentials_error

    ttl = payload["exp"] - int(time.time())

    if ttl>0:
        get_redis().set(f"blacklist:{payload['jti']}", 1, ex=ttl)

    return {"detail": "已登出"}
