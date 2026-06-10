# AGENTS.md · PDF-Flow 自动推进中枢

> 这是 agent 的**操作中枢**。人类只负责：复制下面的「自动推进指令」粘贴给 agent、做 `git add/commit/push`、在服务器 `git pull` 并（需要时）跑 smoke。
> agent 的**进度记忆在本文件的「任务看板」里，不在对话里**。每次推进一步并在看板勾选。
> 详细方案与护栏见 [`docs/TASKS_PLAN_AND_REVIEW.md`](docs/TASKS_PLAN_AND_REVIEW.md)；人类可读状态/变更日志见 [`docs/PROJECT_MASTER.md`](docs/PROJECT_MASTER.md)。

---

## 一、自动推进指令（人类每次原样粘贴这段即可）

```
【PDF-Flow 自动推进 · 原样粘贴】
你在全权开发 PDF-Flow（Vue3+TS 前端 / FastAPI+Celery 后端 / 单机 Docker）。你的记忆在仓库里不在对话里。每次收到本段都重新对齐后只推进一步，忽略之前对话里的跑偏。

第0步 对齐：读 AGENTS.md（含任务看板、规矩、地雷、已定决策）+ docs/TASKS_PLAN_AND_REVIEW.md（详细方案）。以代码现状为准；开发文档/ v1–v4 是愿景白皮书，WASM/K8s/双活等本轮不实现；PROJECT_MASTER 旧描述可能过期，存疑就用命令实测。
第1步 定位：在 AGENTS.md「任务看板」里按从上到下顺序找第一个未勾选 [ ] 的步骤（P2 标记“需凭据/服务器”的先跳过）。
第2步 执行：只做这一个步骤，改动尽量小；删任何代码前先全仓 grep 引用。
第3步 验证（完成的唯一标准）：跑该步验收命令并贴真实输出。前端 npx vue-tsc --noEmit ; npm run build ; npm run test:unit:ci；后端 cd backend && python -m pytest tests/ -q。绿了才算完成。
第4步 落账：把该步在 AGENTS.md 看板勾选为 [x]，并在 PROJECT_MASTER.md changelog 加一行（UTF-8，勿乱码）；保持工作区干净。不要执行 git commit/push（人类来做）。
第5步 交接：给我①一句 commit message；②是否此刻适合我提交并到服务器拉取测试。然后停下，等我下次再贴本段。

硬规矩：没有命令输出不许说“完成/应该可以了”；不实现愿景功能；不新建任何 *_REPORT/_SUMMARY 文档（进度只更新 AGENTS.md 看板 + PROJECT_MASTER changelog）；不误删有引用的代码。遇到需要凭据/服务器/我拍板的事别伪造——写进 AGENTS.md「待我处理」清单（附我要在服务器跑的命令），然后改做下一个能做的本地步骤。
地雷：bcrypt==4.0.1；SQLAlchemy 枚举存 .value 小写；Alembic 迁移单 head；FileManager 用 settings.UPLOAD_DIR；npm run build 用 esbuild 不查类型（类型问题要用 vue-tsc）。
现在执行第0–5步，做下一个最小步骤。
```

> 跑偏或变慢时：**开一个全新对话，再贴这段即可**——因为状态在仓库里，新会话会从看板重新对齐。

---

## 二、已定决策（agent 不必再问）
- 权威基线 = 代码 + PROJECT_MASTER；`开发文档/` 仅历史愿景，本轮不实现其 C 类内容。
- 运行/验证环境：人类会提供服务器与外部凭据（P2 实联调由人类在服务器执行）。
- 后台范围：用户管理 + 功能开关(Feature Flags) + 系统/任务监控；安全靠 `UserRole.ADMIN`+JWT，非 admin 接口返回 **404**。

## 三、待我处理（人类待办 / 阻塞项；agent 把新阻塞追加到这里，勿删历史）
- [ ] 决策：后台入口后缀用 `/__ctrl` 还是其它？后台 UI 是“未挂导航 SPA 路由”还是“独立子域/构建”？
- [ ] 决策：首个 admin 用 `INITIAL_ADMIN_EMAIL` 自动提升 or 脚本 `make-admin <email>`？
- [ ] 决策：计费口径锁 `100K+$0.10/1K`(代码现状) 还是 v4 文档 `$0.05/$0.12`？
- [ ] 决策：i18n 是否“合并 overrides 回 JSON 并删 overrides”？
- [ ] 凭据：Stripe 测试 key / Google·GitHub OAuth / Gemini / Resend / Sentry·PostHog —— 哪些可提供。
- [ ] 服务器：P2 各 smoke 需人类在服务器执行（脚本：`scripts/smoke-test.sh`、`business-smoke-test.sh`、`ocr-smoke-test.sh`、`office-smoke-test.sh`）。

> 决策未定时：agent 对该项**采用文档里的默认建议**继续（后缀默认 `/__ctrl`、首个 admin 默认 `INITIAL_ADMIN_EMAIL`、计费默认沿用代码现状、i18n 默认先只评估不删），并在交接时提示“此项用了默认值，可随时改”。

---

## 四、任务看板（agent 按从上到下顺序推进，完成即把 [ ] 改 [x]）

详细做法/验收见 `docs/TASKS_PLAN_AND_REVIEW.md` 对应编号。

### P0 本地正确性（不需服务器）
- [ ] **P0-1** vite `server.proxy` 加 `/api`(`ws:true`)与 `/health` → `http://localhost:8000`（env `VITE_DEV_API_PROXY` 可覆盖）；dev 端口统一 5173；同步 README/PROJECT_MASTER 端口口径。〔验收：后端起后 `npm run dev` 监听 5173，前端 `/api/v1/*` 不再 404，贴一次 `/health` 或登录请求成功〕
- [ ] **P0-3a** 跑 `npx vue-tsc --noEmit`，把真实错误**按文件分组**记到本步下方；并**为每个未被 3b/3c 覆盖的文件，在本节追加一个 `[ ] P0-3x <文件>` 工单**，再逐个修（拆到文件级）。
- [ ] **P0-3b** 修 `src/utils/pdf/*` 的 `Uint8Array→BlobPart`（如 `compress.ts:63` 加 `as Uint8Array`；`merge.ts` 已修勿动）。
- [ ] **P0-3c** 修 `src/composables/useDragSort.ts` 的 `ref<T[]>` 泛型不匹配。
- [ ] **P0-3d** 修 `src/views/enterprise/*`、`src/components/enterprise/*` 类型错误。
- [ ] **P0-3e** 修 `src/utils/history-manager.ts`、`src/services/api.ts` 类型错误。
- [ ] **P0-3f** 清剩余未使用变量等 → `npx vue-tsc --noEmit` 0 error 且 `npm run build:check` 通过。〔验收：贴 vue-tsc 与 test:unit:ci 输出〕
- [ ] **P0-4** i18n 评估：对比 `en/es` base JSON 与 `overrides.ts` 是否真有损坏/缺失，把结论记录到本步；**仅评估不改**（删 overrides 是单独决策项）。

### P1 隐藏后台 · 后端逐文件工单（按顺序；每个工单改前先读对应文件确认现状）

> 依赖关系：B1→B2（模型先于迁移）；B3/B4 先于 B5/B6（依赖先于端点）；B5/B6 先于 B7（先有 router 才注册）；全部完成后 B10 测试。

- [ ] **P1-B1 模型** `backend/app/models/user.py`：文件末尾追加 `FeatureFlag` 模型（表 `feature_flags`），字段 `id / key(String,unique,非空) / enabled(Boolean,默认True,非空) / description(String,可空) / updated_by(FK users.id,可空) / updated_at(DateTime,onupdate)`。复用文件顶部已 import 的类型与 `datetime`。〔验收：`cd backend && python -c "import app.models.user"` 无错〕
- [ ] **P1-B2 迁移** `backend/alembic/versions/0xx_add_feature_flags.py`（新建）：建 `feature_flags` 表。**先读 `add_webhook_model.py` 取它的 `revision` 字符串作为本迁移 `down_revision`**（保持单链）；本迁移 `revision` 取新串。〔验收：`alembic heads` 只有 1 个 head；能 `python -c` 导入该迁移文件；有 Docker 则 `alembic upgrade head` 通过〕
- [ ] **P1-B3 鉴权依赖** `backend/app/api/v1/endpoints/admin.py`（新建）顶部定义 `require_admin`：`current_user.role != UserRole.ADMIN` → `raise HTTPException(status_code=404, detail="Not Found")`（**返回 404 不是 403**，使后台隐形）；写法模仿 `enterprise.py` 的 `require_enterprise_user`（同文件内定义）。
- [ ] **P1-B4 schemas** `backend/app/schemas/admin.py`（新建）：`UserAdminItem`(id/email/role/is_active/created_at)、`UserListResponse`(items/total/page)、`UserRoleUpdate`(role + 可选 is_active)、`FeatureFlagItem`、`FeatureFlagUpdate`(enabled)、`JobItem`、`SystemStatus`、`UsageSummary`。
- [ ] **P1-B5 admin 端点** `backend/app/api/v1/endpoints/admin.py`：`router = APIRouter(prefix="/__ctrl", tags=["admin"])`，所有端点 `Depends(require_admin)`：`GET /users`(分页+`q`搜 email+`role`过滤)、`PATCH /users/{id}`(改 role/is_active；**禁止把自己降级或删掉最后一个 admin**)、`GET /usage`(复用 enterprise 聚合·全站维度)、`GET /jobs`(近期 `ProcessingJob`)、`GET /system`(DB/Redis/外部服务探活+错误概览)、`GET /flags`、`PATCH /flags/{key}`(写时记 `updated_by`/`updated_at`)。
- [ ] **P1-B6 公开开关端点** `backend/app/api/v1/endpoints/flags.py`（新建）：`GET /flags` 公开只读，返回 `{key: enabled}`，**无鉴权、不泄露内部字段**。
- [ ] **P1-B7 路由注册** `backend/app/api/v1/__init__.py`：`include_router(admin.router)` 与 `include_router(flags.router)`，确认最终路径为 `/api/v1/__ctrl/*` 与 `/api/v1/flags`，**勿重复拼前缀**（参考 changelog 里 enterprise/ai/advanced 曾重复 `/api/v1` 的坑）。
- [ ] **P1-B8 配置+引导** `backend/app/core/config.py` 加 `INITIAL_ADMIN_EMAIL: Optional[str] = None`；`backend/app/main.py` 加 startup 事件：若设置且该 email 用户存在则升为 admin（**幂等**）。另建 `scripts/make-admin.sh <email>`（容器内 `python -m`）兜底；`backend/.env.example` 补该项。
- [ ] **P1-B9 flag 播种** 启动（或迁移后）确保基础 flags 存在，缺则插入默认 `enabled=True`：`site.maintenance`、`cloud.enabled`、`tool.ocr`、`tool.office`、`tool.ai`、`tool.watermark`、`tool.fillForm`、`tool.annotate`。
- [ ] **P1-B10 测试** `backend/tests/test_admin.py`（新建，仿 `test_files.py`/`test_auth.py` 的 conftest 夹具与建用户/发 token 方式）：① 非 admin 访问 `/__ctrl/*` 得 404；② admin `PATCH /users/{id}` 改 role 落库生效；③ `PATCH /flags/{key}` 后 `GET /__ctrl/flags` 反映变化；④ 公开 `GET /api/v1/flags` 无需鉴权可读。〔验收：`cd backend && python -m pytest tests/test_admin.py -q` 通过并贴输出〕

### P1 隐藏后台 · 前端逐文件工单（后端 B1–B10 完成后做；admin 内部页文案可只用中文，不强制三语）

> 依赖：F1/F2/F3 是基础（store/api/guard），F4 路由依赖 F3+F5，F5 外壳先于 F6–F8，F9 依赖 F2 的 flagsAPI。

- [ ] **P1-F1 store** `src/stores/user.ts`：加 `isAdmin` computed（`user?.role === 'admin'`）。〔验收：vue-tsc 通过〕
- [ ] **P1-F2 API** `src/services/api.ts`：加 `adminAPI`（users 列表/改 role·封禁、usage、jobs、system、flags 读写）+ `flagsAPI.getPublicFlags()`；路径对齐后端 `/api/v1/__ctrl/*` 与 `/api/v1/flags`；仿已有 `enterpriseAPI` 的写法与类型。
- [ ] **P1-F3 守卫** `src/router/guards.ts`：加 `adminGuard`（未登录或非 admin → `next('/')`，不暴露后台存在性），仿同文件 `enterpriseGuard`。
- [ ] **P1-F4 路由** `src/router/index.ts`：新增**不挂任何导航**的后台路由（前缀按「待我处理」决策，默认 `/__ctrl`），`beforeEnter: adminGuard`，懒加载 `@/views/admin/AdminLayout.vue`。
- [ ] **P1-F5 外壳** `src/views/admin/AdminLayout.vue`（新建）：仿 `src/views/enterprise/Dashboard.vue` 的多 Tab 外壳，三 Tab：用户 / 开关 / 监控。
- [ ] **P1-F6 用户管理** `src/views/admin/UsersPanel.vue`（新建）：用户表格（email/role/状态/注册时间）+ 搜索 + 改 role/封禁，调 `adminAPI`。
- [ ] **P1-F7 开关管理** `src/views/admin/FlagsPanel.vue`（新建）：flag 列表 + toggle，调 `adminAPI` flags 读写。
- [ ] **P1-F8 系统监控** `src/views/admin/SystemPanel.vue`（新建）：健康 / 外部服务探活 / 近期任务 / 错误概览，调 `adminAPI` system+jobs。
- [ ] **P1-F9 全站开关消费** `src/App.vue`（或 `main.ts`/全局守卫）启动调 `flagsAPI.getPublicFlags()` 存入 store；`src/views/Home.vue` 据 `tool.*` flag 隐藏被关工具卡片；`site.maintenance` 开时显示维护页。〔验收：关掉某 `tool.*` 后首页对应卡片消失；普通用户访问 `/__ctrl` 不可见；贴 vue-tsc/build〕

### P2 真实联调（标「需凭据/服务器」的默认跳过并写进「待我处理」；agent 先做能做的本地 prep）
- [ ] **P2-prep1** 缺凭据不崩（本地可验/可修）：检查 `backend/app/main.py` 的 `MonitoringMiddleware` + `monitoring_service` 在无 `SENTRY_DSN`/`POSTHOG_KEY` 时优雅降级；修到 `cd backend && python -c "import app.main"` 成功。
- [ ] **P2-prep2** 本地校验 4 个 smoke 脚本（`scripts/smoke-test.sh`、`business-smoke-test.sh`、`ocr-smoke-test.sh`、`office-smoke-test.sh`）的端点/参数与当前代码一致，可一键跑。
- [ ] **P2-1** 核心链路（合并/OCR/Office）—— **需服务器**。命令：`bash scripts/business-smoke-test.sh` / `ocr-smoke-test.sh` / `office-smoke-test.sh`。〔人类在服务器执行并回贴结果〕
- [ ] **P2-2** OAuth（Google/GitHub）—— **需 client id/secret + 回调**（见 `docs/OAUTH_SETUP.md`）。
- [ ] **P2-3** Stripe —— **需测试 key + webhook secret**；本地可先核 `payment.py` 端点与 webhook 签名逻辑。
- [ ] **P2-4** Gemini —— **需 `GEMINI_API_KEY`**；跑 AI summarize/ask/extract。
- [ ] **P2-5** Resend —— **需 `RESEND_API_KEY`**；发欢迎/密码重置邮件验证。
- [ ] **P2-6** 监控 Sentry+PostHog —— **需 DSN/key**；验证事件上报。

### P3 清理冗余（**先 grep 引用再删，删后双跑门禁**）
- [ ] **P3-1a** Service Worker 去留决策（默认：彻底拆——已被 `index.html` 主动注销且引发过空白页）。
- [ ] **P3-1b** 若拆：全仓 grep `serviceWorker`/`sw.js`/`pdf-flow:reload`/`pdf-flow-*` 引用 → 删 `public/sw.js`、删 `index.html` 的 sw 注册/注销逻辑、评估 `src/router/index.ts` 的 chunk 失败重载 hack 是否还需要。〔删后 build+vue-tsc+单测〕
- [ ] **P3-2** 全仓 grep `wasm`/`pdfjs.worker`/`WebAssembly`；清 `nginx.conf` CSP 及代码/文档里过时 WASM 措辞（实际无 WASM）。
- [ ] **P3-3a** grep 部署脚本/compose 是否引用 `k8s/`；未用则删或在路线附录标「未来项」。
- [ ] **P3-3b** 比对根 `docker-compose.yml` 与 `backend/docker-compose.yml` 差异，合并或在文档明确分工。
- [ ] **P3-4** `README.md`：删/改 Vercel·Netlify 主部署说法（与单机 Docker 冲突）、移除失效演示链接；「项目状态」区与 PROJECT_MASTER 去重（与 P4-2 协同，勿冲突）。
- [ ] **P3-5** `.gitignore`：让 `*.txt` 不再误伤 `开发文档/*.txt`（加 `!开发文档/*.txt` 例外或收窄规则）。
- [ ] **P3-6** 死代码扫描：对 `src/` 疑似无引用的组件/工具/导出，逐个全仓 grep（含动态 import、router、模板、i18n key）确认无引用再删；每删一批跑 build+vue-tsc+单测+pytest。〔验收：删前删后双跑门禁均绿〕

### P4 文档收口（逐文件）
- [ ] **P4-1a** `docs/PROJECT_MASTER.md` §0/§2：完成度改「已实现 / 已验证 / 未验证」三态，去掉灌水百分比。
- [ ] **P4-1b** 同文件 架构章节：按 `TASKS §1.2` A 类纠正措辞（认证非 Supabase Auth、无 WASM、部署单机 Docker、分支 staging→main）。
- [ ] **P4-1c** 同文件：把 C 类愿景移入「未来可扩展线路」附录，每条写逐级实现步骤，标「未实现/未来项」。
- [ ] **P4-1d** 同文件：changelog 整体移到文末独立区块；**修 `:616` 行乱码**；全文统一 UTF-8。
- [ ] **P4-2** `README.md` 精简为门面 + 指向 PROJECT_MASTER（与 P3-4 协同，勿冲突）。
- [ ] **P4-3** 按 `TASKS §5.2` 执行文档保留/合并/删除（删历史 `*_REPORT/_SUMMARY` 若有；`docs/superpowers/` 稿归档或并入附录）。
- [ ] **P4-4** 将 `docs/TASKS_PLAN_AND_REVIEW.md` 关键内容并入 PROJECT_MASTER 后删除该计划文档；`AGENTS.md` **保留**但把看板重置为「全部完成 / 维护模式」（不要删 AGENTS.md）。〔**最后一步**，确认看板其余项全 `[x]` 后再做〕

---

## 五、验收门禁速查（每步至少跑相关项并贴输出）
```bash
# 前端
npx vue-tsc --noEmit
npm run build
npm run test:unit:ci
npm run lint
# 后端（本地无需 Docker）
cd backend && python -m pytest tests/ -q
```
完成定义：相关门禁绿 + 输出已贴 + 看板已勾 + PROJECT_MASTER changelog 已加一行 + 工作区干净。

## 六、留痕约定（三处对齐，可追溯）
- **每完成 1 个工单 = 1 次提交**（由人类执行）。commit message 建议带工单号，如 `feat(P1-B1): add FeatureFlag model`。
- changelog 一行也带工单号；看板勾选 `[x]` 同步。→ **git log ↔ PROJECT_MASTER changelog ↔ 本看板** 三处按工单号对齐，任何时候都能回溯"哪一步、改了什么、何时验的、输出是什么"。
- agent 在「第5步交接」给出该工单的 commit message；人类提交后再贴话术推进下一个工单。
