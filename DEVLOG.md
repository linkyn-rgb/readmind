# 开发日志

按施工顺序记录每个模块的收尾状态。设计文档负责「要做成什么样」，这里只记「已经做到哪」。

## 2026-11-19 · 第 2 步：图书（部分并入）

**books 表、校验与路由**

- 建 `books` 表：`title`（带索引，搜索用）/ `author` / `isbn` / `desc` / `cover` / `author_bio`
- 并入五个接口：
  - `GET /books/` — 分页列表
  - `GET /books/search?q=` — 按书名或作者模糊搜索
  - `GET /books/{id}` — 详情，不存在返回 404
  - `POST /books/` — 新增（`title` / `author` 必填）
  - `GET /books/ranking` — 榜单占位（第 9 步才做真实榜单）
- 校验：`bookcreate` / `bookupdate` 开 `extra="forbid"`，书名作者 `min_length=1`；分页响应用 `{items, total}` 包装
- 本切片**不含**依赖其他表的部分，等对应模块并入时再补回来（以完整工程为准）：
  - 按题材 / 来源筛选 — 依赖第 3 步
  - 新增时的分类 / 来源校验 — 依赖第 3 步
  - `status` 借阅状态（在架 / 借走了）— 依赖第 6 步
  - `rating` 平均评分 — 依赖第 8 步
- `models/__init__.py` 与 `Schemas/__init__.py` 只导出已并入的 User / Book；`main.py` 挂 `/auth` 与 `/books` 两组路由

本切片已实测：列表 / 详情 / 404 / 搜索 / 新增（测试数据已清）。

未完待续。

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

## 2026-11-26

**认证模块收尾并入仓库**

- 注册的账号唯一性补成两道：先预查 `account` 给友好提示，并发下漏过的由唯一索引兜底，`IntegrityError` 同样转 400 —— 预查只是提示，唯一索引才是正确性保证
- 登出补上降级：写黑名单失败（Redis 连不上）时记 warning 并按 fail-open 放行，不再让登出 500。降级口径与 `dep.py` 查黑名单处保持一致
- 登出保持幂等：鉴权用 `oauth2_scheme` 只验签、不查黑名单，否则「登出过一次就再也登不出去」
- 三个接口（注册 / 登录 / 登出）验收通过，README 的接口表与原则段落同步更新

本轮验收：注册重名 400、登录成功拿到 JWT、登出后旧 token 访问 401、重复登出仍 200、Redis 停机时登出仍 200。

未完待续。
