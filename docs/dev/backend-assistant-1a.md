# 1a 后端内核 + 小x 知识库（一次性开发文档）

**用完即删。** 按切片开发；A–D 全部点验通过后删除本文件。不要登记进 `AGENTS.md` / `docs/README.md`。不要当长期规范。

**当前切片：D — `/suggestion` + `/ask`**

A 已通过（2026-09-22）。B 已通过（2026-09-22）。C 已通过（2026-09-22）。不要重做 A。不要重做 B。不要重做 C。

新对话：先读本文件 → 只做当前切片 D → 停住等用户说「D 过了」。没过先修这一片。不要跳过 D 去改小程序或关 `useMock`。不要 git commit，除非用户点名提交。

以本文件为准。`.hermes/plans/2026-09-21_234353-backend-assistant-1a.md` 是旧稿（`chunk.text = body`、用缩短句做 overlap），不要照它写。

阶段：用户已批准从阶段 F 开这一刀（1a）。切片 A、B、C 已通过。下一片只做 D。合同不改，`useMock` 保持 true，小程序零 diff。`docs/framework/stack.md` 仍不改。进度和 handoff 只在用户要求更新文档时改。

---

## 怎么开发

一次只做「当前切片」。做完停住。

1. 只改该片「改哪些文件」列出的路径。该片「不做」里的一律留下一片。
2. `server/pyproject.toml` **只在 A 写全**。B/C/D 不准再加依赖。
3. 测试：先写测试 → 跑到红 → 最小实现 → 跑到绿。验收命令必须实际跑过。没跑过不准写「已验证」。
4. 本刀无 TypeScript 改动，不要用 `npm run typecheck` 当后端验收。
5. 交接写：范围 / 已改 / 契约 / 验证 / 风险 / 下一步。下一步只能是「等 A/B/C/D 过了」或「修点验问题」。
6. 代码切片在交点验之前，开一个独立子 agent 做 code review（只看该片 diff）。安全问题和逻辑错误先修再交。不要为 review 去 commit。

必读（按顺序）：[AGENTS.md](../../AGENTS.md) → 本文件 → [backend/README.md](../backend/README.md) → [api/contract.md](../api/contract.md) 的 auth / assistant 段 → [handoff.md](../handoff.md) 的环境变量。写代码时再读 [framework/code-standards.md](../framework/code-standards.md)。助手边界：[product/expansion.md](../product/expansion.md)。

分层：`router → service → repository`。Session 只在 repository。`deps` 把 repository 注入 service。service **不收** Session。router 返回 `DataEnvelope[T]`。依赖一律 `Annotated[..., Depends(...)]`。模块之间不准 import 对方的 `models` / `repository` / `router`。assistant 鉴权用 `app.core.security.require_user_id`，不准 import `auth.models`。

---

## 目标

第一次跑起 FastAPI + Docker Postgres（pgvector）。`POST /api/v1/assistant/ask` 对「夏天怎么给狗降温」返回合同信封里的 `knowledge`。

不接 LLM。不改小程序。不关 `useMock`。

```
小程序（不动，继续 mock）
        │
HTTP / pytest
        ▼
FastAPI  :8000
  GET /health                          ← A
  POST /api/v1/auth/login              ← B
  GET  /api/v1/assistant/suggestion    ← D
  POST /api/v1/assistant/ask           ← D
        │
  main.py 扫描 modules/*/router，前缀 /api/v1/<目录名>
        │
  router → service → repository
        │
Postgres 16 + pgvector
  users                                ← B
  knowledge_article / knowledge_chunk  ← C
  conversation                         ← D
```

`/ask` 本刀顺序（D 才写）：

1. `question` 去空白为空 → `VALIDATION`
2. 保证 `conversation_id`（null 则建；有 id 则必须属于当前用户，否则 `NOT_FOUND`）
3. 命中拒答词 → 固定拒答文案，`source=generated`，citations `[]`
4. embedding → top-8
5. 丢掉 `distance > 1 - EMBEDDING_MIN_COSINE` 的段落
6. 仍有过线 → `knowledge`，answer=`article.body`，citations=`id/title/snippet`
7. 否则 → 占位 `generated`（短文案）
8. `related_posts` 永远 `[]`。本刀没有 `search`

---

## 已定

| 项 | 决定 |
|---|---|
| 停在 | D：`/suggestion` + `/ask` |
| 库 | 同一 Postgres + pgvector。Compose **只** Postgres。FastAPI 本机 `http://127.0.0.1:8000` |
| 顺序 | A→B→C→D 串行 |
| 依赖 | 见下方 `pyproject.toml`，只在 A 写 |
| 环境变量 | 跟 handoff：`APP_ENV`、`DATABASE_URL`、`JWT_SECRET`、`JWT_ALGORITHM=HS256`、`JWT_EXPIRE_SECONDS=604800`、`WECHAT_APPID=wxe7c6ce42979250cd`、`WECHAT_SECRET`、`MEDIA_ROOT`、`API_PREFIX` |
| 本刀新增 | `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` / `EMBEDDING_MODEL` / `EMBEDDING_DIM=1024` / `EMBEDDING_MIN_COSINE=0.25` |
| 列上不读 | `MEDIA_ROOT`、`API_PREFIX` 必须在 Settings 里。业务不读。路由前缀在 `main.py` 写死 `/api/v1` |
| `.env` 路径 | `Path(__file__).resolve().parents[2] / ".env"`，相对 `server/app/core/settings.py`，即 `server/.env`。禁止 `env_file=".env"` 依赖 cwd |
| 假登录 | 仅 `APP_ENV=local` **且**未配 `WECHAT_SECRET` → `local:{code}`。staging/prod 缺密钥 → `WECHAT_LOGIN_FAILED`。`session_key` 不下发、不入库 |
| code2session | `server/app/core/wechat.py`。用户表和 JWT 在 `auth`。不准在 `core` 建 User |
| 信封 | A 就做。成功 `{data}`，失败 `{error:{code,message}}`。禁止裸 `{ok:true}`，禁止 FastAPI 默认 `detail` |
| 注册积分 +100 | **不做**。login 只 upsert 用户 + JWT |
| 假向量 | 字符 2/3-gram + sha256 分桶 + L2。不用 Python `hash()` |
| 嵌入文本 | `title + "\n" + body`。`chunk.text` 存这段。`article.body` 仍是 mock 原文（回答用 body） |
| 阈值 | `distance <= 1 - EMBEDDING_MIN_COSINE`。默认 0.25。阈值只来自环境变量 |
| 实测 | 问句「夏天怎么给狗降温」vs body 全文余弦 **0.167**（过不了 0.25）。vs `title+body` 余弦 **0.277**（能过）。`hash_embed` 会去掉全部空白，所以 `title+"\n"+body` 与 `title+body` 是同一向量。缩短句「夏天给狗降温，先避开正午出门…」余弦约 0.315，**禁止**拿它当 overlap 或 D 的代理 |
| 检索单测 | 插入已知向量再查同一向量，distance ≈ 0 |
| `similar_chunks` | 只查 `status='published'`，`joinedload(article)`，`cosine_distance`（`<=>`）升序，k=8。归档不进 top-8 |
| citations | frontmatter 的 `title` / `snippet`。正文当 `body`（= 回答） |
| 拒答 | 词先拦，再检索。词表与 mock 逐字相同 |
| 相近帖 | 恒 `[]` |
| 测试库 | pytest 用 **`app_pet_test`**。手工 alembic / ingest / curl 用 **`app_pet`**。每个测试后 `TRUNCATE … CASCADE` |
| 小程序 | 零 diff。`useMock` 必须 true（真登录会打 `GET /me`，本刀没有） |

expansion 的完整流水（证据门 → 改写 → LLM + 工具）本刀用距离门占位。E/F 再换。不要写空的 LLM 函数。

---

## 实现时直接按这些做

| 条 | 做法 |
|---|---|
| 测试库何时建 | **A 就建** `app_pet_test`。init SQL 只在空 volume 时跑。volume 已存在时用下面的 `CREATE DATABASE` |
| conftest | **import `app.core.db` 之前** 把进程环境变量 `DATABASE_URL` 写成 test 库（用赋值，不要 `setdefault`，否则 `.env` 里的 `app_pet` 会赢），并 `get_settings.cache_clear()`。engine 在 import 时创建，写晚了会打到 `app_pet` |
| 两套库 | 手工 `alembic upgrade` / `python -m app.modules.assistant.ingest` / curl → `app_pet`。pytest → `app_pet_test`：`CREATE EXTENSION IF NOT EXISTS vector` + `Base.metadata.create_all`。D 的降温测试在 **test 库** ingest 同一批种子 |
| truncate | 每个测试后 `TRUNCATE <表> CASCADE`。B 起至少 `users`；C 加上 `knowledge_chunk`、`knowledge_article`；D 加上 `conversation` |
| ingest 状态 | 写入 `status='published'`。`content_hash = sha256(title + "|" + snippet + "|" + body)`。hash 不变 skip；变了删旧 chunk 再重嵌 |
| `register_vector` | A 的 `db.py` 就做。`pgvector.asyncpg.register_vector` 是 async，在 connect 事件里 `dbapi_connection.run_async(register_vector)` |
| 测 prod | 先 `get_settings.cache_clear()`，再把 `APP_ENV` 改成 `prod`。测完再清缓存，避免污染后面的测试 |
| A 的 curl | 先起 `uvicorn`。agent 验以 `pytest tests/core` 为准 |
| PageQuery | `page >= 1`，`page_size` 默认 20、下限 1。不要 `le=50` |
| users | B 就加可空 `nickname`、`avatar_url`。不加积分字段。不做 `/me` |

---

## 明确不做

- 改合同、改 `miniprogram/**`、关 `useMock`
- `/me`、积分流水、相册 / 广场 / 视频真库
- LLM、问法改写、联网搜、`consult` / `experience`
- LangChain、第二向量库、Redis、队列
- 知识库管理 HTTP
- 空的 LLM 函数占位
- C 写 `router.py` / `service.py` / `schemas.py` / `deps.py`（留给 D）
- C 的 `__init__.py` 导出 `router`（空路由会被挂上）

---

## 切片 A — 内核

**状态：已通过（2026-09-22）。** `uv run pytest tests/core -q` 为 17 passed。主库 `alembic upgrade head` 到 `0001_vector_extension`：有 `vector` 0.8.6，公共表只有 `alembic_version`。`app_pet_test` 当时无表。`GET /health` 为 `{"data":{"ok":true}}`。未知路径为 `{"error":{"code":"NOT_FOUND","message":"Resource not found"}}`。

**做完标准：** 下面验收命令跑过，pytest 绿，curl 为 `{"data":{"ok":true}}`。用户说「A 过了」。

**做：** Compose、uv、settings、信封、`wechat.py`、JWT 工具、`register_vector`、Alembic `0001` 只 `CREATE EXTENSION vector`、`GET /health`。无业务表。

**改哪些文件：**

- `docker-compose.yml`（仓库根）
- `server/docker/initdb/01-test-db.sql`
- `server/pyproject.toml`
- `server/.env.example`
- `server/.env`（gitignore，从 example 复制）
- `server/app/__init__.py`、`server/app/modules/__init__.py`（空）
- `server/app/main.py`
- `server/app/core/settings.py` `db.py` `exceptions.py` `envelope.py` `security.py` `wechat.py` `pagination.py`
- `server/alembic/` + `versions/0001_vector_extension.py`
- `server/tests/conftest.py`
- `server/tests/core/test_health.py` `test_envelope.py`

保留现有 `server/README.md`、`server/app/core/README.md`、`server/app/modules/README.md`。

**不做：** 业务表、`auth`、`assistant`、`/me`、积分。

### Compose

镜像 `pgvector/pgvector:pg16`。用户 / 密码 / 库都是 `app_pet`。端口 `5432:5432`。不要把 FastAPI 放进 Compose。

`server/docker/initdb/01-test-db.sql`：

```sql
CREATE DATABASE app_pet_test;
```

挂到容器 `/docker-entrypoint-initdb.d/01-test-db.sql`。

volume 已经存在、init 没跑时：

```bash
docker compose exec postgres psql -U app_pet -d postgres -c 'CREATE DATABASE app_pet_test'
```

本机 5432 被占用：改宿主端口并同步 `DATABASE_URL`。这是环境问题。

### `pyproject.toml`（只此一次）

```toml
[project]
name = "app-pet-server"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "sqlalchemy[asyncio]>=2.0.36",
  "asyncpg>=0.30",
  "alembic>=1.14",
  "pydantic-settings>=2.6",
  "pgvector>=0.3",
  "httpx>=0.27",
  "PyJWT>=2.9",
]

[dependency-groups]
dev = [
  "pytest>=8.3",
  "pytest-asyncio>=0.24",
]

[tool.fastapi]
entrypoint = "app.main:app"

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

### `server/.env.example`

```
APP_ENV=local
DATABASE_URL=postgresql+asyncpg://app_pet:app_pet@127.0.0.1:5432/app_pet
JWT_SECRET=local-dev-only-change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_SECONDS=604800
WECHAT_APPID=wxe7c6ce42979250cd
WECHAT_SECRET=
MEDIA_ROOT=server/var/media
API_PREFIX=/api/v1
EMBEDDING_BASE_URL=
EMBEDDING_API_KEY=
EMBEDDING_MODEL=
EMBEDDING_DIM=1024
EMBEDDING_MIN_COSINE=0.25
```

复制为 `server/.env`。pytest **不要**用这份 URL，见 conftest。

### Settings / DB / 信封

- `Settings` 字段覆盖 handoff 全表 + 五个 `EMBEDDING_*`。`EMBEDDING_MIN_COSINE` 默认 `0.25`。
- `env_file` 用上面的绝对路径。
- `is_local_fake_wechat()`：`APP_ENV == "local" and not WECHAT_SECRET`。
- `get_settings` 用 `lru_cache`。
- `db.py`：async engine，`pool_pre_ping=True`。connect 时 `register_vector`。`get_session` 成功 commit、异常 rollback。**import 时不要连数据库**（创建 engine 可以，执行 SQL 不行）。
- Alembic 走 asyncio + `asyncpg`，url 保持 `postgresql+asyncpg://`。不要为迁移再加 psycopg。`env.py` 从 settings 读 URL，自动 import `app.modules.*.models`（A 时尚无 models）。
- `0001_vector_extension`：`down_revision = None`。upgrade 只 `CREATE EXTENSION IF NOT EXISTS vector`。不准建业务表。
- `main.py`：`create_app()`，`pkgutil` 发现含 `router` 的包，`prefix=f"/api/v1/{目录名}"`。禁止为 auth/assistant 写 `if`。`GET /health` 挂在内核，返回类型 `DataEnvelope[...]`，JSON 为 `{"data":{"ok":true}}`。
- 未知路径和校验失败走 `{error:{code,message}}`。处理 `StarletteHTTPException`（404 → `NOT_FOUND`）和 `RequestValidationError`（400 → `VALIDATION`）。稳定 code：`UNAUTHORIZED` `FORBIDDEN` `NOT_FOUND` `VALIDATION` `CONFLICT` `WECHAT_LOGIN_FAILED` `POINTS_NOT_ENOUGH` `INTERNAL`。
- `wechat.py`：`code` 去空白为空 → `VALIDATION`。local 无 secret → `local:{code}`。staging/prod 无 secret → `WECHAT_LOGIN_FAILED`。有 secret 才打 `https://api.weixin.qq.com/sns/jscode2session`。只返回 openid。
- `security.py`：签发 / 校验 JWT，`sub` 是用户 id 字符串。`require_user_id`：无 Bearer → `UNAUTHORIZED`。不引用 User。
- `pagination.py`：`PageQuery`，`page` 默认 1 且 `>= 1`，`page_size` 默认 20 且 `>= 1`。不要上限 50。
- A 的 `conftest.py`：在任何 `app` import 之前设置

```text
DATABASE_URL=postgresql+asyncpg://app_pet:app_pet@127.0.0.1:5432/app_pet_test
```

并准备好 `get_settings.cache_clear()`。A 的 health 测试可以不建表。

### 验收

```bash
docker compose up -d
# volume 已存在时补：docker compose exec postgres psql -U app_pet -d postgres -c 'CREATE DATABASE app_pet_test'
cd server && uv sync && uv run alembic upgrade head
cd server && uv run pytest tests/core -q
cd server && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
# 另一终端
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/no-such-route
```

期望：pytest 绿。health 为 `{"data":{"ok":true}}`。未知路径是 `{error:{code,message}}`。

**已通过。** 停在这里的条件已满足。随后的 B 也已通过。当前切片见文首。

---

## 切片 B — 鉴权

**状态：已通过（2026-09-22）。** `cd server && uv run pytest tests/core tests/modules/auth -q` 为 31 passed。主库 `app_pet` 的 alembic head 为 `0002_auth_users`。表 `users` 正好这些列：`id` uuid 主键、`openid` varchar(64) unique not null、`nickname` text null、`avatar_url` text null、`created_at` timestamptz not null。没有积分列。两次 curl `POST http://127.0.0.1:8000/api/v1/auth/login`，body `{"code":"test"}`：都是 HTTP 200，同一个 token `sub`，`expires_in` 为 604800，`users` 只有一行，`openid` 为 `local:test`。无密钥的 prod 由 auth 测试覆盖（502 `WECHAT_LOGIN_FAILED`，不插入）；没有另做手工 prod curl。注册 +100 未做。

**做完标准：** pytest 绿；curl login 有 token；同一 code 两次不 500；`APP_ENV=prod` 且无 secret → `WECHAT_LOGIN_FAILED`。用户说「B 过了」。

**改哪些文件：** 只 `server/app/modules/auth/` 六件套（`router.py` `schemas.py` `models.py` `repository.py` `service.py` `deps.py`）+ `__init__.py` 导出 `router` + 迁移 `0002_auth_users`（`down_revision = "0001_vector_extension"`）+ `server/tests/modules/auth/` + 扩展 `conftest.py`。不改 `main.py` 发现逻辑。

**不做：** 积分流水、`/me`、在 `core` 建 User。

表 `users`：

- `id` UUID 主键
- `openid` VARCHAR(64) UNIQUE NOT NULL
- `nickname` TEXT NULL
- `avatar_url` TEXT NULL
- `created_at` timestamptz NOT NULL，默认 now()

不加积分字段。

login：`code` 空 → `VALIDATION`；换 openid → upsert → 签发 JWT。响应：

```json
{ "data": { "token": "...", "expires_in": 604800 } }
```

`expires_in` 取 `JWT_EXPIRE_SECONDS`，整数。字段名 `token` / `expires_in`。

`deps` 构造 repository（内部持有 session）注入 service。service 函数签名里不要出现 `AsyncSession`。

测试库 schema：conftest 在 import models 之后，对 **app_pet_test** 执行 `CREATE EXTENSION IF NOT EXISTS vector` 和 `Base.metadata.create_all`。每个测试后 `TRUNCATE users CASCADE`。

测 prod：`get_settings.cache_clear()` 之后再改 `APP_ENV=prod`，无 `WECHAT_SECRET`，期望 `WECHAT_LOGIN_FAILED`。测完再 `cache_clear()`。

### 验收

```bash
cd server && uv run alembic upgrade head
cd server && uv run pytest tests/core tests/modules/auth -q
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' -d '{"code":"test"}'
```

`alembic` 打在 `app_pet`。pytest 打在 `app_pet_test`。curl 打在正在跑的本机 API（连 `app_pet`）。

**已通过。** 停在这里的条件已满足。下一片是 C。

---

## 切片 C — 知识库（无 HTTP）

**做完标准：** overlap 用种子全文 `title+"\n"+body` 且余弦 > 0.25；已知向量 distance ≈ 0；ingest 幂等。用户说「C 过了」。

**只写：**

- `server/app/modules/assistant/models.py`
- `repository.py`
- `ingest.py`
- `embeddings.py`
- `__init__.py`（**不**导出 `router`）
- `seed/*.md`
- 迁移 `0003_assistant_knowledge`（`down_revision = "0002_auth_users"`）
- `server/tests/modules/assistant/`

**不写：** `router.py` `service.py` `schemas.py` `deps.py`。`conversation` 本片不建。

### 表

`knowledge_article`：`id`，`title`，`body`，`snippet`，`status`（`published` | `archived`），`source_uri` UNIQUE，`content_hash`，`embedding_model`，`updated_at`。

`knowledge_chunk`：`id`，`article_id` FK CASCADE，`chunk_index`，`text`，`embedding vector(1024)`，`embedding_model`，`created_at`。UNIQUE `(article_id, chunk_index)`。

索引：

```sql
CREATE INDEX ix_knowledge_chunk_embedding
ON knowledge_chunk
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

维度 1024 写死。换维 = 新迁移 + 全量重嵌，不改旧文件。SQLAlchemy 用 `pgvector.sqlalchemy.Vector`。

### 种子

一篇一文一块。frontmatter 只有 `title` / `snippet`，手写拆 `---`，不要加 PyYAML。

1. `summer-dog-cooling.md` — 主路径。title / snippet / body 与 mock 逐字相同：

```markdown
---
title: 夏天给狗降温
snippet: 避开正午出门，室内通风，提供阴凉饮水和湿毛巾擦身，不要用冰水浇身。
---

夏天给狗降温，先避开正午出门，改在清晨或傍晚。屋里通风、留阴凉处，随时有干净凉水。可以用湿毛巾擦肚皮和脚垫散热，不要浇冰水、不要把狗关在停驶的车里。我是小x，这是说明书里的日常护理，不能代替兽医。
```

2. `leash-walk.md` — 出门拴绳。正文不要出现「降温」。
3. `cat-water.md` — 猫咪饮水。正文不要出现「发烧」「什么药」。

### 嵌入

```text
embed_text = title + "\n" + body
chunk.text = embed_text
article.body = body
article.title / article.snippet = frontmatter
article.status = "published"
```

无 key → HashEmbedder。`EMBEDDING_BASE_URL`、`EMBEDDING_API_KEY`、`EMBEDDING_MODEL` 三者齐 → HTTP `POST {base}/embeddings`，body `{"model","input"}`。维度必须等于 `EMBEDDING_DIM`，对不上直接失败。禁止加载 sentence-transformers。禁止 Python `hash()`。

`similar_chunks(embedding, k=8)`：`status='published'` + `joinedload(article)`，按 `cosine_distance` 升序。过线比较放在 D 的 service，repository 不过滤距离。

### 测试（三条，不能互相替代）

| 测试 | 文本 | 证明什么 |
|---|---|---|
| `hash_embed` 同文同向量 | 任意短句 | 函数稳定，L2 范数为 1 |
| overlap | **降温种子的 `title+"\n"+body`** | 问句余弦 > 0.25，且高于「今天上证指数多少」对同一段。禁止用缩短句 |
| repository | 插入 `hash_embed("alpha-unique-token-xyz")`，再用同一向量查 | distance < 1e-6。另查一个不同向量，若仍返回该行，distance > 0.5 |

测试库 truncate：`knowledge_chunk`、`knowledge_article`（CASCADE）。ingest 单测对临时目录跑，写 `app_pet_test`。

### 验收

```bash
cd server && uv run alembic upgrade head
cd server && uv run python -m app.modules.assistant.ingest
cd server && uv run pytest tests/modules/assistant -q
```

前两行写 **app_pet**。pytest 写 **app_pet_test**。还没有 `/ask`。

**状态：已通过（2026-09-22）。** `cd server && uv run pytest tests/modules/assistant -q` 为 8 passed。`cd server && uv run pytest tests/core tests/modules/auth -q` 仍为 31 passed。主库 `app_pet` 的 alembic head 为 `0003_assistant_knowledge`。`python -m app.modules.assistant.ingest` 连续两次后，`knowledge_article` 三行都是 `published`（`summer-dog-cooling.md`、`leash-walk.md`、`cat-water.md`），每行一块，`chunk.text` 为标题加换行再加 `body`。`embedding_model` 为 `hash`。HNSW 索引 `ix_knowledge_chunk_embedding` 在 `public.knowledge_chunk`，操作符类 `vector_cosine_ops`。没有 `router.py`，没有 `/ask`。合同未改，`useMock` 保持 true，小程序零 diff。

**已通过。** 停在这里的条件已满足。下一片是 D。

---

## 切片 D — `/suggestion` + `/ask`

**做完标准：** `uv run pytest -q` 全绿；curl 降温 = `knowledge`，用药 = 拒答原文。用户点验 HTTP。

**改哪些文件：** `assistant` 的 `schemas.py` `service.py` `router.py` `deps.py`，`__init__.py` 导出 `router`，迁移 `0004_assistant_conversation`（`down_revision` 接 `0003`），`server/tests/modules/assistant/test_ask.py`。建议问题可放 `suggestions.py`。

**不做：** messages 表、LLM、`search`、相近帖内容、`/me`、积分。

`conversation`：`id` UUID PK，`user_id` UUID NOT NULL → `users.id`，`created_at`。

### 推荐问题（uuid 与 mock 相同）

| id | question |
|---|---|
| `e1111111-1111-1111-1111-111111111111` | 夏天怎么给狗降温 |
| `e2222222-2222-2222-2222-222222222222` | 附近有没有靠谱的宠物医院 |
| `e3333333-3333-3333-3333-333333333333` | 为什么天空是蓝的 |
| `e4444444-4444-4444-4444-444444444444` | 猫咪发烧该吃什么药 |

`GET /suggestion?page=&page_size=` 列表信封 `{items,total,page,page_size}`。四条写死，内存分页。

### 文案（与 mock 逐字相同）

拒答词：`发烧` `吃药` `用药` `开药` `剂量` `诊断` `拉肚子` `什么药`（子串）。

拒答：

```text
我是小x。知识库里没有足够依据回答看病或用药的问题。请带毛孩子去医院，不要自行用药。我不会编诊断、药名或剂量。
```

占位 generated：

```text
我是小x。这是常识说明，仅供参考，不能代替专业意见。
```

医院、天空本刀都走这条短 generated。不要返回 mock 的 `SEARCH_ANSWER` / `SKY_ANSWER`。`source` 只有 `knowledge` 或 `generated`。

### `/ask`

鉴权：无 token → `UNAUTHORIZED`。

service 顺序见上文「目标」。过线：`distance <= 1 - settings.EMBEDDING_MIN_COSINE`。有过线：`source=knowledge`，`answer=article.body`，citations 用 article 的 `id/title/snippet`。`related_posts=[]`。不要 import community。

属主：`conversation_id` 存在但不属于当前用户 → `NOT_FOUND`。

D 的降温测试必须把与 C 相同的三篇种子 ingest 进 **app_pet_test**，再问「夏天怎么给狗降温」，期望 `knowledge`，title 为「夏天给狗降温」，snippet 与 frontmatter 相同，answer 等于种子 body。这是 0.277 那条路径。

「今天上证指数多少」必须是 `generated`，不得 `knowledge`。降温若变不成 `knowledge`，打印 top-1 的 `1 - distance`，只调环境变量 `EMBEDDING_MIN_COSINE`，不准把断言改成「有返回行」。

truncate 加上 `conversation`。

### HTTP 验收

| 请求 | 期望 |
|---|---|
| 无 token 打 suggestion | `UNAUTHORIZED` |
| suggestion | 4 条，信封带 items/total/page/page_size |
| ask 空问题 | `VALIDATION` |
| 猫咪发烧该吃什么药 | `generated` + 拒答原文，citations `[]`，related `[]` |
| 夏天怎么给狗降温（test 库已 ingest） | `knowledge` + title/snippet/body 对齐种子 |
| 今天上证指数多少 | `generated`，不得 knowledge |
| 附近医院 / 天空为什么蓝 | 短 `generated` |
| conversation_id null 再回传 | 第二次与第一次相同 |

```bash
cd server && uv run alembic upgrade head
cd server && uv run python -m app.modules.assistant.ingest
cd server && uv run pytest -q
```

再 curl 降温 / 用药（API 连 `app_pet`，所以 curl 前 ingest 必须打在 `app_pet`）。pytest 自己 ingest 进 `app_pet_test`。

整刀停。用户点验 HTTP。不要改 `docs/progress.md`，除非用户说整理。

---

## 与 mock 的已知差异（关 useMock 前再补，本刀不补）

| | mock | 本刀 |
|---|---|---|
| 附近医院 | `search` | 短 `generated` |
| 天空为什么蓝 | 长常识 | 短 generated |
| 相近帖 | 最多 2 条已发布帖 | `[]` |
| 注册积分 | 合同要首次 +100 | 未入账 |
| 启动 | login + `GET /me` | 无 `/me`，不能关 mock |

## 缺口（禁止假装已做）

`GET/PATCH /me`；注册 +100；证据门与问法改写；LLM / 工具 / `search`；相近帖；`pg_trgm`；知识库管理 HTTP；关 `useMock`。

关 mock 之前至少还要 `/me`（`miniprogram/core/auth.ts` 启动必打）和注册积分（合同原文）。
