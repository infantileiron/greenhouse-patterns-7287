# 南岭温室 · 病征组合筛查

将逐株温室病征调查转为可复现的关联证据，再由农艺师提交、站长批准独立复查清单。React18 / TypeScript + Python FastAPI，PostgreSQL16、Redis 与独立 worker 五服务。

> 当前交付状态为 **partial**：Compose 配置、本地算法、SQLite 模式下的 ASGI API 与独立 worker 流程已验证；Docker socket 与本地监听端口被当前环境拒绝，尚未完成五容器、PostgreSQL/Redis 集成和四张真实截图验收。细节见批次 `test-artifacts/gb-2105/TESTING.md`。

## 真实工作流

模拟客户南岭育苗研究站，16 人负责 8 个温室。现有 `symptom_checks_202611.csv` 逐株记病征，人工在 Excel 中查组合：只看次数不看基线，稀有规则过拟合，多重比较造成偶然显著。该应用替代“调查导出→筛查→农艺复查”中间分析环节，输出供站长安排独立植株复查，不承担诊断或种植干预决策。

核心实体贯穿数据库、Python model/schema/service/controller/route 与前端 API/store/page：

| 实体 | 数据表 | 主要页面 | 行为 |
|---|---|---|---|
| SymptomDataset | datasets | 调查样本 | CSV 导入、校验、分页观察、校验和 |
| MiningStudy | studies | 挖掘配置 | 配置支持度、置信度、置换次数与固定种子 |
| MiningRun | runs | 研究总览、关联证据 | 真实排队执行、状态、结果、失败原因 |
| RuleReview | reviews | 关联证据、复查归档 | 选择规则、提交说明、批准或退回 |
| Report | reports | 复查归档 | 审批产生 CSV，鉴权下载 |

### 账号与权限

统一演示密码 `Nanling!2611`。三个账号是 `admin@nanling.test`、`analyst@nanling.test`、`viewer@nanling.test`。

| role | 使用者 | 主要页面 | 服务端权限 |
|---|---|---|---|
| admin | 林站长 | 全部、复查归档 | 所有研究写入、批准/退回、读取审计 |
| analyst | 周农艺师 | 调查样本、配置、证据、复查 | 导入、建研究、运行、提交复查；不能审批 |
| viewer | 陈观察员 | 全部只读页面 | 查询、下载已批准报告；写接口均403 |

八步剧本：14:00 农艺师登录 → 核查 800 株/10种病征/8温室 → 创建“11月病征组合复查” → 支持度0.12、置信度0.65、999次置换 → worker 计算 → 依据支持数、lift、q值选择规则 → 填写独立复查说明 → 站长批准并下载 CSV。初始化包含两个研究、一条完成运行、一条待审复查和一份已批准报告。

## 快速启动

```sh
cp .env.example .env
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose exec -T backend python -m scripts.seed_demo
```

前端 `http://localhost:18204`，后端文档 `http://localhost:19204/docs`，PostgreSQL 宿主端口 `17704`。初始化 seed 自动随 backend 启动；重复执行基于固定自然ID只插入不存在记录，保留用户修改和既有结果。

批量运行须先获取上层批次脚本的槽位，最多3栈；结束执行 `docker compose down -v --remove-orphans`。后者会删除此项目数据库和导出卷。

## 算法与解释口径

1. **Apriori**：完整植株数为 N，包括未记录病征者。支持度 `count(A∪B)/N`；置信度 `count(A∪B)/count(A)`；提升度 `confidence / (count(B)/N)`。按频繁子集剪枝，最大项集3，单症状后件。
2. **温室内置换与 BH**：每个温室内固定后件发生数量，随机置换后件位置。以“共同出现次数不小于观察值”为单侧统计量，`p=(1+超越次数)/(1+置换次数)`。预先枚举1或2项前件、单项后件的完整规则族，先对全部 p 值做 BH，再按支持度与置信度展示，避免先筛选再缩小检验族。

固定 seed261105、样本 SHA256 和完整参数保存在每次结果中。BH 的标准 FDR 保证依赖独立或正相关等条件；病征规则互相依赖，q值只用于探索性复查排序。温室内置换可控制场地分层，但其他混杂仍可能存在。相关不代表因果，需独立植株验证。

失败态：20–5000株，症状2–12种、名称最长30字，重复植株拒绝；CSV最大1.5MB；支持度0.02–0.8、置信度0.1–1、置换99–1999；活跃运行最多3个。无规则时返回真实空结果。Redis不可达返回503并保存失败状态，可恢复后新建运行。所有统计与持久化在后端完成，前端图形按真实结果渲染。

## 技术与结构

| 部分 | 实现 |
|---|---|
| frontend | React18.3.1、TS5.7.3、Vite6.4.6、Nginx1.27 |
| backend | Python3.11、FastAPI0.115.14、psycopg3.2.3 |
| worker | 同一 Python 镜像，Redis BLPOP/RPUSH 队列，心跳健康检查 |
| db / redis | PostgreSQL16 / Redis7 AOF；三个命名持久卷 |
| 认证与横切 | PBKDF2密码、HS256 JWT8小时、角色校验、审计与错误处理中间件、运行配额 |

`frontend/src/{api,stores,types,components/common,hooks,pages,router,utils,constants}`；`backend/src/{routes,controllers,services,models,schemas,middlewares,utils,constants,config}`；`backend/scripts/seed_demo.py`；`backend/migrations/001_initial.sql`。

共享组件：Status、State、RuleTable、Specimen；RuleTable 同时服务运行结果与复查证据。共用 hooks 为 useResource/useRoute。UI 为陶土植物标本册，Noto Serif SC + IBM Plex Mono、oklch 色板、分层排版、1280/768/手机断点与减少动效支持。Google Fonts 需要外网；离线回退 serif/monospace。

共享枚举定义位于 `backend/src/constants/enums.py` 与 `frontend/src/constants/enums.ts`：Role (`admin/analyst/viewer`)、RunStatus (`queued/running/succeeded/failed`)、ReviewStatus (`pending/approved/rejected`)。权限引用 `utils/security.py`，状态引用 `services/run.py`；前端 `App.tsx`、`components/common/Status.tsx` 引用。ReviewDecision schema 只接受 approved/rejected。

Nginx `/api/` 剥除前缀代理至 backend，后端路由不含 `/api`。前端提供 SPA 回落，Redis不映射宿主端口。backend/worker依赖db/redis healthy，frontend依赖backend healthy，五服务都有真实healthcheck。

## 环境变量

| 变量 | 默认/说明 |
|---|---|
| COMPOSE_PROJECT_NAME | greenhouse-patterns，五服务容器名前缀 |
| FRONTEND_PORT / BACKEND_PORT / DB_PORT | 18204 / 19204 / 17704 |
| DB_PASSWORD | 演示数据库密码，发布前修改 |
| JWT_SECRET | 演示HS256密钥，发布前修改 |
| SEED_DEMO | true，初始化失败仅记录日志 |
| DATABASE_URL | Compose注入postgresql URL；本地可显式sqlite:///路径 |
| REDIS_URL / QUEUE_MODE | Compose为redis://redis:6379/0 / redis |
| ARTIFACT_DIR | Compose为/artifacts共享卷 |
| QUEUE_MODE=database | 仅本地测试，SQLite独立worker轮询，不代表Redis验收 |

## 本地开发与测试

Python3.11/3.12 新建隔离环境，`pip install -r backend/requirements.txt`；另安装pytest/httpx用于测试。前端 `npm install --prefix frontend && npm run dev --prefix frontend`。后端在backend目录执行：

```sh
export DATABASE_URL=sqlite:///./greenhouse.sqlite
export QUEUE_MODE=database
export SEED_DEMO=true
python -m uvicorn src.main:app --host 127.0.0.1 --port 19204
# 另一个终端，同样环境、同样backend工作目录
python -m src.worker
```

测试文件集中于批次 `test-artifacts/gb-2105/tests/`：test_mining.py、local_acceptance.py、docker_acceptance.py、screenshots.cjs。local_acceptance 使用 ASGI TestClient + 独立数据库队列worker，不伪装网络或容器测试；docker_acceptance 使用标准库HTTP等待真实worker，默认BASE_URL=http://127.0.0.1:19204。截图脚本需要可用Playwright，指定FRONTEND_URL/CHROME_PATH后可捕获4张1440×900页面。

## 已知差异

当前 React18 离线包不可用，本地构建临时借用可用 React19.3.1依赖完成类型与打包检查，交付package.json仍严格声明React18；React18安装/构建需在依赖可用环境复验。未测试容器实际healthy、PostgreSQL、Redis、浏览器交互/截图；没有伪造截图。worker不自动重放崩溃时的running任务，当前需保留失败记录后重新创建运行。审计异常不会阻塞业务，需要运营日志监控。数据库迁移当前为首版幂等DDL。

源码和测试产物分离；.env、node_modules、dist、数据库、日志、上传产物均忽略。MIT License。
