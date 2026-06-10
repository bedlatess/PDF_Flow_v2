# PDF-Flow 五大任务：方案与意见文档

> 🤖 **Agent 执行入口在仓库根目录 [`AGENTS.md`](../AGENTS.md)**（含可勾选任务看板 + 自动推进指令）。本文件是其背后的详细方案与护栏依据。
>
> 本文件是针对你提出的五个任务方向的**只读评审 + 详细方案**，用于决策与后续实施依据。
> 撰写时**未改动任何业务代码**（工作区保持干净）。
> 撰写日期：2026-06-10。本文若被采纳，相关结论将并入 `docs/PROJECT_MASTER.md`（见任务五）。

---

## 0. 我已核实的现状基线（事实，不是文档转述）

下面区分「我亲自读代码/配置确认的」与「仅文档声明、需实跑复核的」，避免再被过期文档误导。

### 0.1 已读材料
- `开发文档/`：v1.0 / v2.0 / v3.0 / v4.0 全部（通过同名 `.txt` 提取件）
- `docs/`：`PROJECT_MASTER.md`（626 行全文）、`OAUTH_SETUP.md`、`STAGING_DEPLOY_GUIDE.md`、`superpowers/specs/2026-06-09-npm-domain-deployment-design.md`
- 代码：`src/router/index.ts`、`src/services/api.ts`、`src/i18n.ts`、`src/locales/*`、`src/composables/{useDragSort,useWebSocket}.ts`、`src/utils/pdf/{merge,compress}.ts`、`vite.config.ts`；后端 `app/main.py`、`api/v1/__init__.py`、`models/user.py`、`endpoints/{auth,ai,enterprise,users}.py`、`core/database.py`；`nginx.conf`、`package.json`、`.gitignore`

### 0.2 已确认事实（读代码核实）
| # | 事实 | 证据 |
|---|------|------|
| F1 | **无任何 admin 后台端点**，但 `UserRole.ADMIN="admin"` 枚举已存在 | `backend/app/api/v1/__init__.py` 未挂载 admin 路由；`backend/app/models/user.py:19` |
| F2 | admin 目前仅在「配额」上被当 enterprise，无管理能力 | `backend/app/api/v1/endpoints/files.py:74` |
| F3 | **本地全栈开发断链**：前端同源 `''` baseURL，但 vite dev server 无 `/api` 代理 | `src/services/api.ts:8`；`vite.config.ts`（server 段无 proxy） |
| F4 | **dev 端口三处不一致**：config=3000、文档=5173、实际运行日志=4173→4175 | `vite.config.ts`；`README.md`/`PROJECT_MASTER.md §6`；`.tmp-vite-out.log:3` |
| F5 | **PROJECT_MASTER 的"技术债清单"已过期**：`merge.ts:55` 已加 `as Uint8Array` 修复，但 `compress.ts:63` 未修 | 读 `src/utils/pdf/merge.ts`、`compress.ts` |
| F6 | **zh.json 实为干净 UTF-8**，无 U+FFFD 乱码；所谓"locale 污染"至少已部分不成立 | Grep `\x{FFFD}` 命中 0；读 `src/locales/zh.json` |
| F7 | `src/locales/overrides.ts` 是 **1463 行的"影子翻译层"**，大量重复 base JSON 内容 | 读 `src/locales/overrides.ts`、`src/i18n.ts:31-34` |
| F8 | 前端默认语言为 **zh**（非浏览器英文） | `src/i18n.ts:21,29` |
| F9 | `PROJECT_MASTER.md:616` 有一整条 **changelog 乱码**（`??????????`） | 读 `docs/PROJECT_MASTER.md` |
| F10 | git 工作区干净；`dist/ test-results/ playwright-report/ .tmp/ *.log` 均已被 `.gitignore` 排除（属本地杂物，非入库冗余） | `.gitignore`；初始 git status |
| F11 | `.gitignore:41` 的 `*.txt` 误伤 `开发文档/*.txt`（提取件不入库，仅 `!backend/requirements.txt` 例外） | `.gitignore:40-44` |
| F12 | 后端认证依赖清晰：`get_current_user` / `get_current_user_optional` 在 `auth.py`；`require_pro_user`(在 ai.py/advanced.py 各定义一份)、`require_enterprise_user`(enterprise.py)；DB 用 `get_db` | Grep 结果 + 读 `auth.py:38-82`、`ai.py:30-39` |
| F13 | 前端 API 全部走 `/api/v1/...`；WS 为 `${host}/api/v1/ws/jobs/{id}?token=` | `src/services/api.ts`；`src/composables/useWebSocket.ts:47-52` |
| F14 | 生产部署：nginx 托管静态前端 + 反代 `/api`、`/health`、ws → `backend:8000`；外层 NPM 域名 + IP:5173 兜底 | `nginx.conf`；superpowers 部署稿 |

### 0.3 仅文档声明、需实跑复核（本机 bash 工具链当前不可用，未亲测）
| # | 待复核命题 | 复核命令 |
|---|------------|----------|
| V1 | `npm run build`（esbuild，不做类型检查）通过 | `npm run build` |
| V2 | `build:check`（`vue-tsc`）失败、错误集中在 enterprise/history/api/pdf | `npx vue-tsc --noEmit` |
| V3 | 前端单测 108 通过 | `npm run test:unit:ci` |
| V4 | E2E 24/28（`test-results/` 内有 merge 失败截图，疑似过期） | `npm run test:e2e` |
| V5 | 后端 35 pytest 通过（SQLite+stub） | `cd backend && python -m pytest tests/ -q` |

> **结论性提醒**：F5/F6 已证明 PROJECT_MASTER 的债务/状态描述**不可全信**。任务二的修复**必须以实跑 `vue-tsc`/测试输出为准**，不能照债务清单逐条改。

---

## 任务一：开发文档梳理与冲突归类

### 1.1 定性（最重要的一条意见）
`开发文档/` 的 v1–v4 是**层层加码的"愿景白皮书"，不是"现状规格"**。四版之间本身在演进/打架，越往后越宏大且大量未落地。**不要把它们当成"要让代码逐条对齐的规格"**，否则会凭空造出一份巨大的虚假差距清单（WASM、K8s、双活、Tus…）。

四版主张演进对照：

| 维度 | v1 | v2 | v3 | v4 |
|------|----|----|----|----|
| 认证 | Supabase/Firebase | 同 v1 | 自建数据模型 | JWT 自建 |
| PDF 引擎 | 纯 JS 库 | 纯 JS 库 | **WASM(C++)+多线程** | WASM + Tus 分片 |
| 部署 | Vercel | Vercel 首发 | Docker | **Swarm→K8s HPA + 东京/新加坡双活** |
| 监控 | 无 | PostHog | **Sentry+Prometheus+Grafana** | 全套 + Chatwoot |
| 支付 | 微信/支付宝+Stripe | Stripe | Stripe | Stripe 三档 |

### 1.2 冲突归类（PDF 愿景 ↔ 实际代码/PROJECT_MASTER）

**A 类 — 直接矛盾**
1. **认证**：v1 说用 Supabase/Firebase；实际是自建 FastAPI JWT+bcrypt+authlib。PROJECT_MASTER 写"PostgreSQL 15 (Supabase)"，但代码只是普通 SQLAlchemy/Alembic，**未用 Supabase**。
2. **WASM**：v3/v4 把 WASM(C++)+多线程当核心；实际纯 JS（pdf-lib/pdfjs/jspdf），**无 WASM**。`PROJECT_MASTER §9` 仍残留"WASM 延迟初始化"措辞。
3. **部署口径**：`README.md` 主推 Vercel/Netlify/Cloudflare Pages + 演示链接 `pdf-flow.vercel.app`；真实是**单服务器 Docker + nginx + NPM 域名**。前端已依赖同源 `/api`，纯静态托管没有后端 → README 误导。
4. **分支策略**：`PROJECT_MASTER §10` 写 Git Flow（main←develop←feature）；`§6.1` 写 staging→main；实际仓库只有 `main`。**文档内部自相矛盾**。

**B 类 — 计费/限额数字打架**
5. 免费额度：v1="注册送 10 次/月"；v4="20MB、3 次/天"（PROJECT_MASTER 采用 v4）。
6. 企业计费：v4 文档=`$0.05/基础、$0.12/OCR`；代码/PROJECT_MASTER=`100K 免费、超出 $0.10/1K`。**两套并存**。

**C 类 — 愿景未落地（属正常"未来项"，不是 bug）**
7. K8s HPA、双活容灾、Tus 分片、Prometheus/Grafana、ClamAV、Cloudflare WAF、Chatwoot、A/B、微信/支付宝——**均未实现**，对当前阶段属过度设计。`k8s/` 目录大概率是空架子。

**D 类 — 文档治理与质量**
8. PROJECT_MASTER 自称"唯一权威、勿新建报告"，但 README 又重复维护"项目状态"，且 backend/README、EMAIL_SERVICE.md、OAUTH_SETUP、STAGING_DEPLOY、superpowers 稿并存——**"单一事实源"已被自己破坏**。
9. 编码乱码：`PROJECT_MASTER.md:616`（见 F9）。
10. **完成度灌水**：Phase 2=100%、Phase 3=78%，但 Stripe/OAuth/Resend/Gemini/OCR/Office **全部"代码完成但从未对真实服务验证"**（文档自己也写"需凭据/Docker"）。

### 1.3 建议处置
- 以 **代码 + PROJECT_MASTER** 为现状准绳；PDF 仅历史输入。
- A 类：以代码为准，反向把文档措辞改对（认证不是 Supabase Auth、无 WASM、部署是单机 Docker、分支是 staging→main）。
- B 类：二选一锁定一套计费口径（建议采用代码里的 `100K+$0.10/1K`，因为它已落到 enterprise 端点）。
- C 类：进"未来可扩展线路"附录，本轮不实现。
- D 类：并入任务五一并收口。

---

## 任务二：代码架构与问题清单 + 修复方案

### 2.1 架构速览
- **前端**：Vue3+TS+Vite+Pinia+vue-router+vue-i18n。纯前端工具（pdf-lib/pdfjs/jspdf）+ 云端工具页（OCR/Office/AI/水印/表单/注释）。同源 `''` baseURL + JWT 拦截器 + 401 自动刷新。
- **后端**：FastAPI + SQLAlchemy/Alembic(PostgreSQL) + Redis + Celery。模块齐全（auth/oauth/users/files/ws/payment/enterprise/ai/advanced/health/monitoring 中间件）。
- **部署**：单服务器 docker-compose；nginx 静态前端 + 反代后端；外层 NPM 域名 + IP 兜底。

### 2.2 问题清单（按严重度；每条含 现象/根因/定位/建议修法/验证）

#### 🔴 P0 —— 影响"能否正常开发/运行"

**P0-1 本地全栈开发断链**
- 现象：`npm run dev` 时前端调用 `/api/v1/*` 全部 404，云端功能无法本地联调。
- 根因：`src/services/api.ts:8` 用同源 `''`，但 `vite.config.ts` 的 dev server 无 proxy（生产靠 nginx 反代，开发态没有等价物）。
- 修法：vite `server.proxy` 增加 `/api`（`ws:true`）与 `/health` → `http://localhost:8000`，目标用 env 可覆盖。
- 验证：起后端后 `npm run dev`，登录/上传链路通。

**P0-2 dev 端口不一致**
- 现象：config=3000，文档/部署口径=5173，实跑=4173。
- 修法：统一为 5173（与文档、`NPM→:5173` 部署口径一致），README/PROJECT_MASTER 对齐。
- 验证：`npm run dev` 监听 5173。

**P0-3 `build:check` 失败（待 V2 复核）**
- 现象：`npm run build` 用 esbuild 不做类型检查可过；`build:check`(vue-tsc) 据称失败 → **类型系统形同虚设**。
- 根因（部分已知，但债务清单过期 F5）：Vue `ref<T[]>` 泛型 `UnwrapRefSimple` 不匹配（`useDragSort.ts`）；`Uint8Array→BlobPart` 收窄（`compress.ts:63` 等未加 `as Uint8Array`）；enterprise/history/api 模块若干。
- 修法：**先实跑 `npx vue-tsc --noEmit` 拿到真实错误清单**，按文件分批修；典型修法：`new Blob([bytes as Uint8Array], …)`、`ref<T[]>([]) as Ref<T[]>` 或显式泛型、清理未使用变量。**不要照过期债务清单盲改**。
- 验证：`npx vue-tsc --noEmit` 0 error；`npm run build:check` 通过。

#### 🟠 P1 —— 真实可用性风险（需任务四阶段用服务器+凭据验证）

**P1-1 一堆"完成但没跑过"**
- 涉及：Stripe / OAuth(Google,GitHub) / Resend / Gemini / Sentry / PostHog / Tesseract OCR / LibreOffice Office。
- 风险：全依赖外部凭据或系统二进制，零真实验证，上线即高概率 500/启动崩。
- 修法：逐条用真实凭据/容器联调（顺序见执行计划 P2）；并确认缺凭据时**优雅降级而非崩**（尤其 monitoring 中间件在 `main.py` 无条件注入）。
- 验证：各自 smoke 脚本（仓库已有 business/ocr/office smoke）逐条过。

**P1-2 任务状态可能丢**
- 现象：`get_job_status` 靠 Celery `AsyncResult`，结果过期即丢；`ProcessingJob` 表与 Redis job 键疑似双真相源。
- 修法：任务成功后主动 `setex` 回写 `job:` 键；统一以 Redis job 键为查询真相源（DB 表作审计）。
- 验证：合并/OCR 任务完成后延迟查询仍返回 completed。

**P1-3 i18n 影子层冗余（与任务四/五交叉）**
- 现象：`overrides.ts`(1463 行) 重复 base JSON；F6 显示 base zh.json 其实干净。
- 风险：两份文案易漂移；新增文案不知该改哪。
- 修法（择一）：① 把 overrides 合并回 JSON、删 overrides（彻底）；② 明确 overrides 为唯一可写源、把 base JSON 瘦身为占位（折中）。建议①，但需逐 key 比对 en/es 是否真有损坏。
- 验证：切 zh/en/es，关键页面无乱码、无中英混杂、无 key 回退。

#### 🟡 P2 —— 工程整洁度（任务四主战场）
- **P2-1 半拆除残骸**：Service Worker 被 `index.html` 主动注销；router 有 chunk 失败重载 hack；CSP 历史引用过 `/wasm/pdfjs.worker.js`。→ 决定"留还是彻底拆"，别留半套。
- **P2-2 死配置**：`k8s/`、根与 `backend/` 两个 docker-compose 可能漂移。
- **P2-3 本地杂物**（F10）：已 gitignore，不在库中；清理是"删本地目录"而非"删入库代码"。
- **P2-4 .gitignore 误伤**（F11）：`*.txt` 排除了 `开发文档/*.txt`。

### 2.3 如何复核本节结论（任何会话/你本人均可跑）
```bash
npx vue-tsc --noEmit         # 真实类型错误清单（驱动 P0-3）
npm run build                # 确认 esbuild 构建通过
npm run test:unit:ci         # 单测
npm run lint                 # ESLint
cd backend && python -m pytest tests/ -q   # 后端 35 用例
```

---

## 任务三：隐藏后台（Admin）设计方案（可逐级实现的详规）

范围（你已确认）：**用户管理 + 功能开关(Feature Flags) + 系统/任务监控**。

### 3.1 安全模型（核心意见）
- **"后缀/保密 URL ≠ 安全"**。若后台是 SPA 路由，路径会进 JS 包、可被搜出。
- **安全必须压在 `UserRole.ADMIN` + JWT 上**：所有 admin 端点用 `require_admin` 依赖；**对非 admin 一律返回 404**（而非 403），使接口"隐形"。
- URL 用不显眼前缀（如 `/api/v1/__ctrl/*`）只作"低调入口"，非安全边界。
- 可选加固（后续）：admin 接口叠加 IP allowlist；或把后台做成**独立构建/独立子域**，使主站 JS 包里完全不含后台路径。第一版默认"未挂导航的 SPA 路由 + admin-JWT + 404"。

### 3.2 后端设计

**(a) 鉴权依赖**（新增到一个公共位置，避免每个文件重复定义）
```python
# backend/app/api/v1/endpoints/admin.py（或 core/deps.py）
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        # 关键：返回 404 而非 403，使后台对非 admin 隐形
        raise HTTPException(status_code=404, detail="Not Found")
    return current_user
```

**(b) Feature Flags 数据模型**（新增表 + Alembic 迁移，注意迁移链单头，参考 `add_webhook_model.py` 的 `down_revision`）
```python
class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)     # 如 tool.ocr / cloud.enabled / site.maintenance
    enabled = Column(Boolean, default=True, nullable=False)
    description = Column(String, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
```
建议初始 flags：`site.maintenance`、`cloud.enabled`、按工具 `tool.ocr/office/ai/watermark/fillForm/annotate`。

**(c) 端点清单**（前缀 `/api/v1/__ctrl`，全部 `Depends(require_admin)`，除公开只读那个）

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/__ctrl/users` | 用户列表（分页、搜索 email、按 role 过滤） |
| PATCH | `/__ctrl/users/{id}` | 改 role（free/pro/enterprise/admin）、is_active（封禁/启用） |
| GET | `/__ctrl/usage` | 用量/计费聚合（复用 enterprise 聚合逻辑，全站维度） |
| GET | `/__ctrl/jobs` | 近期 ProcessingJob / Celery 队列概览 |
| GET | `/__ctrl/system` | 健康、外部服务连通性（Redis/DB/Stripe/Gemini/Resend 探活）、错误概览 |
| GET | `/__ctrl/flags` | 列出所有 feature flags（admin 视角） |
| PATCH | `/__ctrl/flags/{key}` | 开关某 flag |
| **GET** | **`/api/v1/flags`（公开只读）** | 前端启动时读取**生效中的**开关，无需 admin（只回 key→enabled，不泄露内部信息） |

**(d) 首个 admin 引导**（避免"先有鸡还是先有蛋"）
- 方案：启动时若不存在 admin，且配置了 `INITIAL_ADMIN_EMAIL`，则把该邮箱用户升为 admin；或提供一次性 CLI/脚本 `scripts/make-admin.sh <email>`（走容器内 `python -m ...`）。**不要**做"公开注册即 admin"。

### 3.3 前端设计
- **路由**：`/__ctrl`（或你指定的后缀）下挂 `AdminLayout` + 子页，`beforeEnter: adminGuard`（检查 `userStore.isAdmin`）。**不在 Header/Footer/任何导航出现**。
- **adminGuard**：未登录或非 admin → `next('/')`（或 404 视图），不暴露存在性。
- **UI 三块**：
  1. 用户管理：表格（email/role/状态/注册时间）+ 搜索 + 改 role/封禁。
  2. Feature Flags：开关列表（key/描述/状态/最后修改）。
  3. 系统/任务监控：健康卡片 + 外部服务探活 + 近期任务表 + 错误概览。
- **全站消费开关**：`App.vue`/路由守卫启动时拉 `GET /api/v1/flags`，据此隐藏被关的工具卡片、或对 `site.maintenance` 显示维护页。

### 3.4 逐级实现清单（实施时按序）
1. 后端：`require_admin`（404 策略）+ `FeatureFlag` 模型 + Alembic 迁移（**核对迁移链单头**）。
2. 后端：`admin.py` 端点（users/usage/jobs/system/flags）+ 公开 `GET /flags`。
3. 后端：`config.py` 加 `INITIAL_ADMIN_EMAIL` + bootstrap 逻辑/脚本。
4. 后端：pytest 覆盖（非 admin 访问得 404、admin 改 role 生效、flags 读写）。
5. 前端：`api.ts` 加 `adminAPI` + `flagsAPI`；`stores/user.ts` 加 `isAdmin`。
6. 前端：`adminGuard` + 路由 + 3 个页面 + 全站开关消费。
7. 验证：`vue-tsc`/build/单测；后端 pytest；真实环境点验。

---

## 任务四：确保运行 + 清理冗余 方案

### 4.1 先定义"正常运行"（分三层，逐层验收）
| 层级 | 含义 | 验收 |
|------|------|------|
| L1 本地前端 | `npm run dev`/`build` 起得来、纯前端工具可用 | build 通过 + 手点 6 个本地工具 |
| L2 本地全栈 | + 后端 Docker + dev 代理（P0-1），云端链路可联调 | 合并/OCR/Office smoke |
| L3 服务器全栈 | 真实域名 + 外部凭据，对外可用 | 任务二 P1 各条 + 人工页面验收 |

### 4.2 清理三分类（**先验证再删**）
- **真死代码**：无引用的文件/导出/组件。删前 `grep` 全仓引用 + 构建。
- **半拆除残骸**（P2-1）：先决策"留/彻底拆"，再统一处理，别留半套。
- **本地杂物**（P2-3）：`dist/ test-results/ playwright-report/ .tmp/ *.log`——已 gitignore，清理=删本地目录，不影响仓库。
- **死配置**（P2-2）：`k8s/`、重复 compose——确认是否真用，不用则删/标注。

### 4.3 删除前标准流程（写成纪律）
```
1. grep 全仓引用（含动态 import、router、i18n key、模板）
2. npm run build + npx vue-tsc --noEmit + 单测（前端）
3. pytest（后端）
4. 删除后再跑一遍 2/3，绿了才提交
```

### 4.4 README 口径纠正
- 删/改 Vercel/Netlify 作为主部署的说法（与单机 Docker 现实冲突）；演示链接 `pdf-flow.vercel.app` 若无效则移除。
- "项目状态"区与 PROJECT_MASTER 去重（README 只留门面 + 指向 PROJECT_MASTER）。

---

## 任务五：文档收口方案

### 5.1 PROJECT_MASTER 重构建议（结构）
当前 626 行、changelog 占大半且含乱码（F9）。建议拆为清晰分区：
1. **元信息 + 现状真值**（去掉灌水百分比，改"已实现/已验证/未验证"三态）
2. **架构现状**（前端/后端/部署，含真实事实，纠正 A 类措辞）
3. **可扩展线路（路线图）**：把 C 类愿景列为**附录**，标注"未实现/未来项"，并写**逐级实现步骤**（对应你"详细内容逐级实现"的要求）
4. **当前任务看板**（P0–P4，可勾选）
5. **变更日志（Changelog）**：从主文档**拆到文末或单独区块**，避免拖垮可读性；**修掉 `:616` 乱码**

### 5.2 文档保留/合并/删除清单
| 文档 | 处置 | 理由 |
|------|------|------|
| `docs/PROJECT_MASTER.md` | **保留**（重构为唯一状态+架构+路线源） | 单一事实源 |
| `docs/OAUTH_SETUP.md` | 保留（操作手册） | runbook，不重复状态 |
| `docs/STAGING_DEPLOY_GUIDE.md` | 保留（部署手册） | runbook |
| `backend/docs/EMAIL_SERVICE.md` | 保留或并入附录 | 外部服务配置说明 |
| `backend/README.md` | 保留（精简，指向 PROJECT_MASTER） | 后端运行说明 |
| `README.md` | **精简去重**（门面 + 纠正部署口径） | 与 PROJECT_MASTER 状态去重 |
| `docs/superpowers/specs/*.md` | 归档或并入路线附录 | 一次性设计稿 |
| 本文件 `TASKS_PLAN_AND_REVIEW.md` | 采纳后并入 PROJECT_MASTER，再删 | 避免长期并存 |
| 各类历史 `*_REPORT/_SUMMARY/_COMPLETE.md` | 若有则删 | 治理规则已禁止 |

### 5.3 文档治理规则（沿用并强化）
- 唯一状态源 = PROJECT_MASTER；新增文档须满足"操作手册/部署指南/外部服务配置"之一且不重复状态。
- 每完成一小步即更新 PROJECT_MASTER（§现状 + §看板 + §changelog）。
- 统一 UTF-8，禁止再引入乱码。

---

## 附：建议执行顺序与验收门禁（P0–P4）

| 阶段 | 内容 | 验收门禁 |
|------|------|----------|
| **P0** 本地正确性 | P0-1 dev 代理/端口；P0-3 vue-tsc 清零；i18n 影子层决策 | `vue-tsc`/`build`/单测/lint 全绿 |
| **P1** 任务三后台 | require_admin(404)+FeatureFlag+admin 端点+前端守卫/UI | 后端 pytest（非admin→404）+ 前端 build |
| **P2** 真实联调 | 核心链路→OAuth→Stripe→Gemini→Resend→监控 | 各 smoke 脚本逐条过 + 缺凭据不崩 |
| **P3** 清理冗余 | 死代码/半拆除残骸/死配置/README 口径 | 删前删后双跑门禁 |
| **P4** 文档收口 | 重构 PROJECT_MASTER、修乱码、愿景作附录、去重 | 链接有效、无乱码、状态三态化 |

**顺序逻辑**：P0 让本地"能跑能验证"→ P1 纯新增风险低 → P2 用服务器逐条点亮真实能力 → P3 在代码已稳前提下清理 → P4 定稿文档。每步可验证，删代码有绿门禁兜底。

---

## 需要你确认/提供的事项
1. **后台入口后缀**：用 `/__ctrl` 还是你指定的字符串？后台 UI 第一版是"未挂导航的 SPA 路由"还是要"独立子域/独立构建"（更彻底但更重）？
2. **首个 admin**：用 `INITIAL_ADMIN_EMAIL` 自动提升，还是脚本 `make-admin <email>`？
3. **外部凭据可提供范围**：Stripe 测试 key / Google·GitHub OAuth / Gemini / Resend / Sentry·PostHog —— 哪些现在能给（决定 P2 能点亮到哪）。
4. **计费口径**：锁定 `100K+$0.10/1K`（代码现状）还是 v4 文档的 `$0.05/$0.12`？
5. **i18n**：是否同意"合并 overrides 回 JSON 并删除 overrides"（彻底）方案？

---

# 附录 B：用 Agent 驱动执行本项目的操作手册

> 目标：让你能把任务拆给（一个或多个）AI agent 去做，而本文件 + `PROJECT_MASTER.md` 作为它们的"事实来源 + 护栏"。

## B.0 可行性结论
**可行**，但要分清"agent 擅长 / 需要你兜底"的部分：

| 阶段 | 适配度 | 说明 |
|------|:---:|------|
| P0 本地正确性 | ⭐⭐⭐ 很适合 | 机械、可本地验证（vue-tsc/build/单测），agent 能闭环 |
| P1 后台（新增） | ⭐⭐⭐ 适合 | 纯新增 + 有 pytest 兜底；需严格给定 404 鉴权与 flag 约定 |
| P2 真实联调 | ⭐ 需你兜底 | **agent 给不了外部凭据/服务器**；只能写脚本、读日志、改 bug，密钥与服务器由你提供 |
| P3 清理冗余 | ⭐⭐ 适合但高危 | agent 爱"误删"；必须强制"先 grep 引用 + 双跑门禁"纪律 |
| P4 文档收口 | ⭐⭐⭐ 很适合 | 文本整理，agent 强项 |

**核心风险（本仓库特有，必须提前告知 agent）**：
1. **PROJECT_MASTER 状态/债务描述已过期**（见 §0 F5/F6）——agent 若全信会改错地方。**必须先实跑命令建立基线，再动手**。
2. **开发文档/ 的 v1–v4 是愿景白皮书**——agent 可能去实现 WASM/K8s/双活。**明确告知本轮不实现**。
3. **本仓库历史上大量"✅ 构建通过"掩盖了运行期崩溃**（启动 ImportError、枚举大小写、迁移分叉、上传路径下划线等）。**agent 不许只凭"构建过"宣布完成**，必须贴真实命令输出。
4. **已知地雷**：`bcrypt==4.0.1`（4.1+ 与 passlib 不兼容）、SQLAlchemy 枚举须存 `.value`（小写）、Alembic 迁移链须单 head、`FileManager` 路径须用 `settings.UPLOAD_DIR`、`build` 用 esbuild 不做类型检查（类型问题只有 `vue-tsc` 才暴露）。

## B.1 交给 agent 的「八条铁律」（护栏）
1. **先基线后动手**：任何修改前，先跑验证命令并把**真实输出**贴出来；不准凭文档下结论。
2. **以代码为准**：冲突时信代码，不信 PROJECT_MASTER 的完成度/债务描述。
3. **不实现愿景**：`开发文档/` 的 WASM、K8s、双活、Prometheus、Tus、ClamAV、Chatwoot 等一律不做。
4. **不假装完成**：完成的唯一标准是对应"验收门禁"命令绿，并贴出输出；缺凭据/缺服务器的步骤如实标"待你提供"，不得伪造。
5. **删除先验证**：删任何代码前先全仓 `grep` 引用（含动态 import / router / i18n key / 模板），删后再跑门禁。
6. **小步交付**：一次只做一个阶段/一个问题，产出 diff + 命令输出，等你确认再继续。
7. **不新建状态文档**：不准新增 `*_REPORT/_SUMMARY/_COMPLETE.md`；进度只更新 `PROJECT_MASTER.md`。
8. **尊重地雷**：遵守 B.0 第 4 条已知地雷，改这些处要额外说明理由。

## B.2 每次会话开头必贴的「全局上下文块」（直接复制）
```
你在协助开发 PDF-Flow（Vue3+TS 前端 / FastAPI+Celery 后端 / 单服务器 Docker 部署）。
事实来源与护栏：先读 docs/TASKS_PLAN_AND_REVIEW.md 和 docs/PROJECT_MASTER.md。

铁律（务必遵守）：
1) 先基线后动手：改动前先跑验证命令并贴真实输出，不要只信文档——PROJECT_MASTER 的完成度/债务清单已被证实过期。
2) 以代码为准；开发文档/ 的 v1–v4 是愿景白皮书，WASM/K8s/双活/Prometheus/Tus 等本轮一律不实现。
3) 完成的唯一标准 = 对应验收命令绿 + 贴出输出；缺凭据/服务器的步骤如实标注，不得伪造"已完成"。
4) 删代码前先全仓 grep 引用，删后再跑门禁。
5) 一次只做一个阶段/一个问题，产出 diff + 命令输出，停下等我确认。
6) 不新建任何 *_REPORT/_SUMMARY 文档；进度只更新 PROJECT_MASTER.md。
已知地雷：bcrypt==4.0.1；SQLAlchemy 枚举存 .value（小写）；Alembic 迁移单 head；
FileManager 用 settings.UPLOAD_DIR；npm run build 用 esbuild 不做类型检查，类型问题要用 vue-tsc 才能看到。

先别改任何东西。第一步：运行下面命令并把输出贴给我，确认当前基线：
  npx vue-tsc --noEmit ; npm run build ; npm run test:unit:ci ; npm run lint
  cd backend && python -m pytest tests/ -q
```

## B.3 分阶段「任务提示词」模板（每段都先贴 B.2，再贴对应任务）

**P0-1 dev 联调 + 端口**
```
任务：修复本地全栈开发断链。在 vite.config.ts 的 server 段加 proxy：
/api（changeOrigin、ws:true）和 /health → http://localhost:8000（目标用 env VITE_DEV_API_PROXY 可覆盖），
并把 dev 端口统一为 5173；同步 README/PROJECT_MASTER 里的端口口径。
验收：起后端后 npm run dev 监听 5173，前端 /api/v1/* 不再 404（贴一次成功的登录或 /health 请求）。
```

**P0-3 vue-tsc 类型清零**
```
任务：让 npm run build:check 通过。先跑 npx vue-tsc --noEmit 拿到真实错误清单（按文件分组贴给我），
不要照 PROJECT_MASTER 的旧债务清单改——已证实过期（merge.ts 已修、compress.ts 未修）。
逐文件修复：典型有 new Blob([bytes as Uint8Array],…)、ref<T[]> 泛型、未使用变量。
验收：npx vue-tsc --noEmit 0 error 且 npm run test:unit:ci 仍全绿（贴输出）。
```

**P1 后台-后端**
```
任务：实现隐藏 admin 后台后端（范围：用户管理 + Feature Flags + 系统/任务监控）。
照 docs/TASKS_PLAN_AND_REVIEW.md 任务三：require_admin 对非 admin 返回 404（不是 403）；
新增 FeatureFlag 表 + Alembic 迁移（务必核对迁移链单 head）；端点挂在 /api/v1/__ctrl/*；
另加公开只读 GET /api/v1/flags；首个 admin 用 INITIAL_ADMIN_EMAIL 引导。
验收：pytest 覆盖"非 admin 访问得 404 / admin 改 role 生效 / flags 读写"，并贴 pytest 输出。
```

**P1 后台-前端**
```
任务：实现后台前端。adminGuard（非 admin → 跳首页，不暴露存在性）；路由挂在不显眼前缀且不出现在任何导航；
三块 UI：用户管理表格(改 role/封禁)、Feature Flags 开关、系统/任务监控；
App 启动读 GET /api/v1/flags 控制工具卡片显隐与维护页。
验收：npx vue-tsc --noEmit 与 npm run build 通过（贴输出）；普通用户访问后台路由不可见。
```

**P3 清理冗余**
```
任务：清理冗余。候选见任务四（半拆除的 Service Worker/WASM 引用、k8s/、重复 compose、README 部署口径）。
每删一项前先全仓 grep 引用并贴出，确认无引用再删；删完跑 build + vue-tsc + 单测 + 后端 pytest。
本地杂物(dist/test-results/playwright-report/.tmp/*.log)已 gitignore，不要当代码删、也不要提交。
验收：删前删后两次门禁均绿（贴输出）。
```

**P4 文档收口**
```
任务：按任务五重构 PROJECT_MASTER（现状三态化、架构纠正 A 类措辞、愿景作附录并写逐级步骤、changelog 拆到文末、修 :616 乱码），
README 精简去重并纠正部署口径（删 Vercel 主部署说法）。
验收：全文 UTF-8 无乱码、内部链接有效；不新建任何文档。
```

## B.4 如何验收 agent 的产出（防"嘴上完成"）
- **只认证据**：要求每个完成都附"命令 + 真实输出 + diff"。没有输出的"已完成"一律打回。
- **自己抽查门禁**：关键节点你本人跑一遍 §2.3 的命令，对比 agent 贴的输出是否一致。
- **看 git diff**：`git diff --stat` 看改动范围是否超纲；后台/清理类尤其要核对没动到无关文件。
- **红旗信号**：出现"应该可以了/构建通过即完成/我无法运行所以假设…"等措辞，立即要求实跑验证。

## B.5 多 Agent 协作的工程纪律
- **一阶段一分支一 PR**：每个 agent 任务开独立分支，你 review 合并后再开下一个，避免互相踩。
- **约定先行**：后台后缀、flag key 命名、admin 404 策略、计费口径——在 B.2 里固定好，多个 agent 才不会各写各的。
- **串行依赖**：P0 → P1 → P3/P4 尽量串行（P1 依赖 P0 的类型门禁；P3 依赖代码已稳）。P2 任何时候都要你提供凭据。
- **状态同步靠你**：agent 之间不共享记忆，**你是集成者**；每阶段合并后由你（或让 agent）更新 PROJECT_MASTER 的看板与 changelog。
- **并行只在无依赖时**：例如 P4 文档整理可与 P1 后台并行，但不要让两个 agent 同时改同一批文件。

## B.6 常见失败模式 → 对策
| 失败模式 | 对策 |
|---------|------|
| 信了过期文档改错地方 | 铁律 1/2；强制先实跑基线 |
| 跑去实现 WASM/K8s 愿景 | 铁律 3；全局块明确点名 |
| "构建过=完成"（掩盖运行崩溃） | 铁律 4；P1/P2 必须 pytest/真实请求 |
| 误删有引用的代码 | 铁律 5；删前 grep + 删后双跑门禁 |
| 一次性想做完五大任务、改得失控 | 铁律 6；一阶段一 PR |
| 又新建一堆总结/报告文档 | 铁律 7；只更新 PROJECT_MASTER |
| 踩 bcrypt/枚举/迁移/路径地雷 | 铁律 8；全局块已列明 |
| 缺凭据时伪造联调通过 | 铁律 4；P2 凭据由你提供，缺则标"待提供" |

