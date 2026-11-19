# ReadMind

基于 **FastAPI** 的图书阅读平台后端。AI 推荐是主线之一（第 10 步）：模型只负责「把用户的话翻译成库里的标签和分类」，挑书始终由自己的数据完成——不做给大模型套壳的事。

**这是项目的开端，未完待续。** 仓库当前包含第 1 步「用户认证」和第 2 步「图书」（部分），其余模块按设计好的施工顺序逐步并入。

## 当前进度

| 步骤 | 模块 | 状态 |
| --- | --- | --- |
| 1 | 用户表 + 认证（注册 / 登录 / 登出） | 本仓库 |
| 2 | 图书（列表 / 详情 / 搜索） | 本仓库（部分，见 [DEVLOG](DEVLOG.md)） |
| 3 | 分类与来源 | 待并入 |
| 4 | 标签 | 待并入 |
| 5 | 书架 / 试读 / 阅读进度 | 待并入 |
| 6 | 借阅（借 / 还 / 续） | 待并入 |
| 7 | 章节正文与进度上报 | 待并入 |
| 8 | 评价 | 待并入 |
| 9 | Redis：登出黑名单 / 热搜 / 借阅榜 | 进行中 |
| 10 | 推荐 | 待开始 |
| 11 | 统计 | 待开始 |

## 技术栈

- **FastAPI** + Uvicorn
- **SQLAlchemy 2.0**（ORM）+ MySQL（PyMySQL 驱动）
- **Pydantic v2** / pydantic-settings（入参校验与配置）
- **JWT**（PyJWT，HS256）+ **bcrypt**（密码哈希）
- **Redis**（登出黑名单，随第 9 步接入）

## 已实现接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/auth/register` | 注册，返回新用户信息 |
| POST | `/auth/login` | 登录，返回 JWT（`access_token` + `token_type`） |
| POST | `/auth/logout` | 登出，把该 token 的 `jti` 写入 Redis 黑名单 |
| GET | `/books/` | 图书列表（分页，`?page=&size=`） |
| GET | `/books/search?q=` | 按书名或作者模糊搜索 |
| GET | `/books/{id}` | 图书详情，不存在返回 404 |
| POST | `/books/` | 新增图书（`title` / `author` 必填） |
| GET | `/books/ranking` | 榜单占位，第 9 步才做真实榜单 |

## 本地运行

```bash
# 1. 建库
mysql -uroot -p -e "CREATE DATABASE library_stream DEFAULT CHARSET utf8mb4;"

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置：复制 app/.env.example 为 app/.env，填自己的数据库密码和 SECRET_KEY
#    环境变量优先级高于 .env 文件

# 4. 启动
uvicorn main:app --reload
```

启动后打开 <http://127.0.0.1:8000/docs>，右上角 Authorize 按钮可直接走 OAuth2 密码流登录。

> 登出接口依赖 Redis；本地没起 Redis 时只有登出会失败，注册与登录不受影响。

## 几条已经定下来的原则

- **认证 / 授权 / 数据隔离三分**：401 是「没身份」，403 是「有身份没资格」，404 是「不是你的，我不告诉你它存在」。
- **密码只存 bcrypt 哈希**，不存明文；bcrypt 上限 72 字节，超出显式报错而不是静默截断。
- **登录失败不区分原因**：账号不存在与密码错误返回同一句提示，不给攻击者反馈。
- **`user_id` 永远从 token 里取**，不接受客户端传入。
- **JWT 带 `jti`**：登出时把编号写进黑名单，TTL 等于该 token 的剩余有效期——设长了白占内存，设短了黑名单先过期、token 又活了。

## 目录

```
DEVLOG.md               开发日志：按模块记录已经做到哪
main.py                 入口：创建应用、挂载路由、建表
app/
  database.py           引擎 / Session / 基类 / get_db 依赖
  core/
    config.py           全局配置（环境变量 > .env > 默认值）
    security.py         bcrypt 哈希、JWT 签发与校验
    dep.py              鉴权依赖 get_current_user（含黑名单检查）
    redis.py            Redis 连接池（懒加载 + 健康检查）
  models/
    User.py             用户表
    Book.py             图书表（只含表本身，关系随模块并入）
  routers/
    auth.py             注册 / 登录 / 登出
    book.py             图书列表 / 搜索 / 详情 / 新增 / 榜单占位
  Schemas/
    register.py         注册请求体
    book.py             图书入参与出参
```

## 说明

本仓库是逐步并入的切片，不是完整工程。`app/models/__init__.py` 与各模块的挂载点会随步骤推进持续增加；如果你现在全局搜索，会发现目前只有认证链路和图书本身的增删查是通的，这是预期内的状态。

第 2 步目前是**部分并入**：题材 / 来源筛选、新增时的分类校验依赖第 3 步的分类与来源表，`status` 借阅状态依赖第 6 步的借阅表，`rating` 依赖第 8 步的评价表——这些字段和逻辑会在对应模块并入时补回 `Book` 与 `book` 路由（以完整工程为准）。

## 未完待续

第 2 步起（图书、分类与来源、标签、书架与试读、借阅、正文与进度、评价、Redis、推荐、统计）按施工顺序继续并入。每个模块收尾时在 [DEVLOG.md](DEVLOG.md) 记一笔，README 的进度表跟着更新。
