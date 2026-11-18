# 开发日志

按施工顺序记录每个模块的收尾状态。设计文档负责「要做成什么样」，这里只记「已经做到哪」。

## 2026-11-19

**用户表 + 接口初步实现**

- 建 `users` 表：`account` 唯一且作为登录账号，`password` 只存 bcrypt 哈希，`nickname` 仅用于展示、允许重名
- 完成三个接口的初步实现：
  - `POST /auth/register` — 注册，账号重复返回 400
  - `POST /auth/login` — 登录，返回 `access_token` + `token_type`
  - `POST /auth/logout` — 登出，把 token 的 `jti` 写入 Redis 黑名单，TTL 等于剩余有效期
- 鉴权链路打通：`security.py` 负责签发 / 校验，`dep.py` 负责「验签 → 查黑名单 → 查库」拿到当前用户
- 首次并入仓库：`main.py`、`database.py`、`core/` 四件、`User` 模型、`auth` 路由、依赖清单
- 连接串改为从环境变量 / `.env` 读取，仓库附 `.env.example`

已知待办：注册的 `account` 重复目前走 400，还要改成捕获唯一索引冲突；登出在 Redis 不可用时尚未兜底。

未完待续。
