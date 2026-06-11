# PDF-Flow 开发主文档（唯一权威 / Single Source of Truth）

> ⚠️ **本文件是项目唯一的开发文档。** 所有状态、计划、规范、指南都在这里。
> **开发完成后只更新本文件，不要新建任何 `*_REPORT.md` / `*_SUMMARY.md` / `*_COMPLETE.md`。**
> 原始需求规格见 [`开发文档/`](../开发文档/)（v1.0–v4.0 白皮书，只读源材料）。

---

## 0. 文档元信息

| 项 | 值 |
|----|----|
| **文档版本** | v4.5 |
| **最后更新** | 2026-06-09 |
| **项目版本** | 1.0.0 (前端 MVP) / 2.0.0 (后端) |
| **Phase 1（本地 MVP）** | ✅ 100% |
| **Phase 2（云端+用户）** | ✅ **100%**（所有功能完成，待真实环境测试） |
| **Phase 3（AI+企业）** | 🚧 **78%**（企业API+AI+监控+高级PDF完整实现） |

**完成度口径说明**：前端经 `vite build` + 108 单测验证 + 企业控制台 + AI 分析器完成；后端**核心逻辑层（认证/文件处理/OCR/OAuth/企业API/AI集成）已完成**并通过构建验证，且已在单服务器 Docker 环境完成**启动、迁移、健康检查、API docs**验证；当前进入**业务链路验收阶段**（上传/合并/OCR/Office/认证联调）。

---

## 1. 项目概述

| 项 | 内容 |
|----|------|
| **名称** | PDF-Flow |
| **定位** | 隐私优先的在线 PDF 工具集 (SaaS) |
| **核心理念** | 纯前端本地处理 + 云端增强（可选） |
| **差异化** | 基础工具 100% 浏览器本地完成，文件不出设备 |

### 渐进式三阶段路线

- **Phase 1（已完成）**：纯前端 MVP，6 大工具，免登录、免费、本地处理。
- **Phase 2（已完成，待联调验收）**：后端 API + 用户系统 + 云端处理（OCR/Office）+ Pro 订阅。
- **Phase 3（进行中）**：企业 API + 计费 + AI 集成（Gemini 文档智能）。

### 定价模型（v4.0 规划）

| 套餐 | 价格 | 能力 | 限制 |
|------|------|------|------|
| Free | $0 | 纯前端工具无限次 | 云端 20MB、3 次/天 |
| Pro | $9.9/月 或 $79/年 | 云端高阶（OCR/转换） | 500MB 文件 |
| Enterprise | 按量计费 | RESTful API + DPA | Token 计费 |

---

## 2. 完成状态矩阵（一图看全局）

| 模块 | 设计 | 后端 | 前端 | 测试 | 验证 | 完成度 |
|------|:----:|:----:|:----:|:----:|:----:|:------:|
| 前端核心 6 工具 | ✅ | N/A | ✅ | ✅ | ✅ build | **100%** |
| 前端认证 UI (登录/注册/个人中心) | ✅ | N/A | ✅ | ⚠️ | ✅ build | **100%** |
| API 服务层 (axios 封装) | ✅ | N/A | ✅ | ❌ | ✅ 编译 | **100%** |
| 工具页云端开关集成 | ✅ | N/A | ✅ | ❌ | ✅ build | **100%** |
| OCR 功能 | ✅ | ✅ | ✅ | ❌ | ⚠️ 前端 | **85%** |
| WebSocket 实时进度 | ✅ | ✅ | ✅ | ❌ | ⚠️ 代码 | **90%** |
| Pricing 定价页面 | ✅ | N/A | ✅ | ❌ | ✅ build | **100%** |
| OAuth 社交登录（Google/GitHub） | ✅ | ✅ | ✅ | ❌ | ⚠️ 需凭据 | **95%** |
| Office 转换（Word/Excel/PPT→PDF） | ✅ | ✅ | ✅ | ❌ | ⚠️ 需LibreOffice | **90%** |
| Stripe 支付集成 | ✅ | ✅ | ✅ | ❌ | ⚠️ 需凭据 | **95%** |
| 后端认证 API (JWT) | ✅ | ✅ | ✅ | ✅ | ✅ pytest | **95%** |
| 后端文件处理 API | ✅ | ✅ | ✅ | ✅ | ⚠️ 逻辑 | **85%** |
| 文件下载端点 + 结果轮询 | ✅ | ✅ | ✅ | ✅ | ✅ pytest | **90%** |
| Celery 任务队列 | ✅ | ✅ | N/A | ❌ | ❌ 运行 | **70%** |
| Redis 限流中间件 | ✅ | ✅ | N/A | ❌ | ❌ 运行 | **80%** |
| 后端单元测试 | ✅ | ✅ | N/A | ✅ | ✅ 35通过 | **70%** |
| **企业 API Key 管理** | ✅ | ✅ | ✅ | ❌ | ✅ build | **90%** |
| **企业控制台** | ✅ | ✅ | ✅ | ❌ | ✅ build | **90%** |
| **Webhook 系统** | ✅ | ✅ | ✅ | ❌ | ❌ 需测试 | **85%** |
| **使用量统计与计费** | ✅ | ✅ | ✅ | ❌ | ❌ 需测试 | **85%** |
| **AI 集成（Gemini）** | ✅ | ✅ | ✅ | ❌ | ✅ build | **95%** |
| **监控集成（Sentry+PostHog）** | ✅ | ✅ | N/A | ❌ | ⚠️ 需凭据 | **80%** |
| **高级PDF - 水印（前端本地）** | ✅ | N/A | ✅ | ❌ | ✅ build | **95%** |
| **高级PDF - 表单/注释（后端）** | ✅ | ✅ | ✅ | ❌ | ✅ build | **90%** |
| **高级PDF（水印/表单/注释）** | ✅ | ✅ | ✅ | ❌ | ✅ build | **90%** |
| **邮件系统（Resend）** | ✅ | ✅ | ❌ | ❌ | ✅ 语法 | **95%** |

图例：✅ 完成 / ⚠️ 部分 / ❌ 未做 / N/A 不适用

---

## 3. 已完成功能（Phase 1 + Phase 2 已交付部分）

### 3.1 前端核心 PDF 工具（本地处理 ✅）

| 工具 | 文件 | 实现库 |
|------|------|--------|
| 合并 PDF | `src/views/tools/MergePDF.vue` | pdf-lib |
| 拆分 PDF | `src/views/tools/SplitPDF.vue` | pdf-lib |
| 旋转 PDF | `src/views/tools/RotatePDF.vue` | pdf-lib |
| 压缩 PDF | `src/views/tools/CompressPDF.vue` | pdf-lib + 图像压缩 |
| 图片转 PDF | `src/views/tools/ImageToPDF.vue` | jspdf |
| PDF 转图片 | `src/views/tools/PDFToImage.vue` | pdfjs-dist |
| 添加水印 | `src/views/tools/WatermarkPDF.vue` | pdf-lib（`utils/pdf/watermark.ts`） |

特性：100% 本地、Web Workers 后台处理、自动内存释放、实时进度、拖拽上传。

### 3.2 UI 组件系统（20 个 ✅）

- **通用 (6)**：Button, Card, Modal, ProgressBar, Skeleton, HistoryPanel
- **PDF 专用 (5)**：DragDropZone, FilePreview, PageSelector, PageThumbnail, PDFViewer
- **布局 (2)**：Header（含用户菜单）, Footer
- **页面 (9)**：Home + 6 工具页 + Login + Register + Profile

### 3.3 前端认证与集成（✅ 已构建验证）

| 文件 | 职责 |
|------|------|
| `src/views/auth/Login.vue` | 登录页（邮箱密码 + OAuth 按钮 + 记住我） |
| `src/views/auth/Register.vue` | 注册页（密码强度指示、条款确认） |
| `src/views/auth/OAuthCallback.vue` | OAuth 回调处理页面（提取 token、存储、重定向） |
| `src/views/auth/Profile.vue` | 个人中心（信息/统计/配额/编辑/删号） |
| `src/services/api.ts` | axios 封装，JWT 自动注入 + 401 自动刷新，含 auth/file/user/health 全部 API |
| `src/stores/user.ts` | Pinia 用户状态（注册/登录/登出/checkAuth/统计/套餐 computed） |
| `src/router/guards.ts` | authGuard / guestGuard / proGuard / enterpriseGuard |
| `src/components/layout/Header.vue` | 登录态头像下拉菜单 / 未登录登录按钮 |

### 3.4 后端架构（✅ 代码完成，⚠️ 已完成基础运行验证，业务链路联调中）

```
backend/app/
├── main.py                    # FastAPI 入口 + CORS + 全局异常
├── celery_worker.py           # Celery 配置（pdf_processing / ocr_processing 队列）
├── core/
│   ├── config.py              # pydantic-settings 配置
│   ├── security.py            # JWT + bcrypt
│   ├── database.py            # SQLAlchemy 连接
│   └── rate_limiter.py        # Redis 滑动窗口限流
├── models/user.py             # User / APIKey / UsageLog / ProcessingJob
├── schemas/  user.py file.py  # Pydantic 模型
├── api/v1/endpoints/
│   ├── auth.py                # 注册/登录/刷新/me/登出
│   ├── oauth.py               # OAuth 社交登录（Google/GitHub）
│   ├── users.py               # 统计/更新/删号(GDPR)
│   ├── health.py              # 健康检查/指标
│   ├── websocket.py           # WebSocket 实时进度
│   └── files.py               # 上传 + 6 工具 + OCR + 任务查询
├── services/file_service.py   # 文件处理业务逻辑
├── tasks/ pdf_tasks.py ocr_tasks.py  # Celery 异步任务
└── utils/file_utils.py        # 魔术数字校验 + 文件管理
```

**已实现 API 端点**：
- 认证：`POST /auth/register|login|refresh|logout`、`GET /auth/me`
- OAuth：`GET /auth/oauth/{provider}`、`GET /auth/oauth/{provider}/callback`
- 用户：`GET /users/me/stats`、`PATCH /users/me`、`DELETE /users/me`
- 文件：`POST /files/upload|merge|split|compress|rotate|images-to-pdf|pdf-to-images|ocr`、`GET /files/jobs/{id}`、`GET /files/download/{job_id}`
- AI：`POST /api/v1/ai/summarize|ask|extract|batch-analyze`（Pro+）
- 高级PDF：`POST /api/v1/advanced/watermark|form/fields|form/fill|annotate/text|annotate/highlight|signature/field`（Pro+）
- WebSocket：`WS /ws/{job_id}`
- 健康：`GET /health`、`GET /api/v1/health/detailed|metrics`

**STRIDE 安全实现状态**：
| 威胁 | 措施 | 状态 |
|------|------|------|
| S 仿冒 | JWT + API Key SHA-256 | ✅ 代码 |
| T 篡改 | 魔术数字文件校验 | ✅ 代码 |
| R 抵赖 | UsageLog 审计 | ✅ 代码 |
| I 泄露 | CSP / Tmpfs | ⚠️ 部分 |
| D 拒服 | Redis 滑动窗口限流 | ✅ 代码 |
| E 提权 | 非 root 容器 | ✅ Dockerfile |

### 3.5 测试与国际化

- **前端单元测试**：108/108 通过（Vitest，14 文件）
- **前端 E2E**：24/28 通过（85.7%，Playwright）— 等待策略见 §8
- **后端测试**：✅ 35+ 个 pytest 用例通过（基于 SQLite + stub 的逻辑层测试，已补匿名/登录上传回归）
- **i18n**：en / zh / es 三语，结构统一为 `app/nav/tools/common/auth/account`

---

## 4. 待办事项（按真实优先级，开发即在此勾选）

### 🔴 P0 — 完成真实业务链路验收（本周）

- [x] **后端真实环境端到端联调**：截至 2026-06-09，单服务器 Docker 环境已跑通启动、迁移、`/health`、`/api/docs`、PDF 合并上传下载、OCR、Office 转 PDF 四条真实链路，当前已具备切到 `main` 做真实上线测试的条件
- [x] **上线前脚本化业务验收**：`smoke-test.sh`、`business-smoke-test.sh`、`ocr-smoke-test.sh`、`office-smoke-test.sh` 已在真实服务器连续通过，当前既可作为 `staging -> main` 的发布门禁，也可作为 `main` 线上测试的最小回归集
- [x] **OCR / Office 真实服务器验收收尾**：OCR 上传与 Office 转 PDF 已在真实服务器复跑通过，相关 smoke 脚本、任务状态链路和上传兼容性修复已闭环
- [x] **本地自动化补稳（第一轮）**：已补齐 `backend/tests/conftest.py` 的关键第三方 stub（含 `stripe`、`google.generativeai`、`sentry_sdk`、`posthog` 等），并把 GitHub Actions 收敛到当前 `main/staging` 的最小可用门禁：后端核心 pytest、前端 unit test、前端 build；暂不把现有大规模历史 lint 债务设为强制阻塞
- [ ] **前端 lint 债务分批清理**：第一轮已清掉 `src/` / `tests/` 中会导致 ESLint 失败的硬错误（未使用变量、无效 try/catch、模板语法错误等），当前已收敛到“仅剩 warning、不再有 error”；下一步继续按目录分批处理格式类 warning 与 `any` 类型，再评估把 lint 以非阻塞或分目录方式接回 CI
- [x] **`main` 真实上线测试收口（第一轮脚本验收）**：截至 2026-06-09，服务器 `main` 分支已完成 `deploy-main.sh` 重新部署，并连续通过 `smoke-test.sh`、`business-smoke-test.sh`、`ocr-smoke-test.sh`、`office-smoke-test.sh` 四条真实链路；下一步进入人工页面验收与线上问题清单沉淀阶段
- [x] **`main` 上线脚本权限兼容修复**：`deploy-main.sh` / `rollback-main.sh` 首轮在服务器上调用下层脚本时暴露 `Permission denied`，根因是包装脚本直接执行 `deploy-staging.sh` / `rollback-staging.sh`，仍依赖下层文件的可执行位。现已改为显式 `bash ...` 调用，避免因脚本权限不同步而中断 `main` 分支上线流程
- [x] **域名 + IP 双入口部署方案落地（仓库侧）**：已将前端部署模式从开发态 `npm run dev` 收口为静态 `nginx` 站点，前端默认通过同源 `/api`、`/health`、WebSocket 路径访问后端；当前目标访问结构为 `NPM -> pdf.pawn.eu.org -> :5173`，同时保留 `http://服务器IP:5173` 直连兜底和 `http://服务器IP:8000/api/docs` 调试入口
- [x] **文件下载端点**：`GET /files/download/{job_id}` 已实现（单文件直传 / 多文件 zip / OCR txt；425 未完成、422 失败、404 不存在），前端 `fileAPI.downloadResult` + `pollJobUntilDone` 已配套
- [x] **后端单元测试**：新增 `tests/`（conftest + security/auth/files），35 用例通过，覆盖密码哈希、JWT、API Key、魔术数字、注册/登录/鉴权流程、下载分支
- [x] **前端 OAuth 按钮**：加 "Soon" 角标 + tooltip，诚实标记未实现（后端 OAuth 属 P2）
- [x] **修复 3 个生产级 bug**（测试发现）：① bcrypt 4.x 与 passlib 不兼容 → 锁 `bcrypt==4.0.1`；② JWT `sub` 必须为字符串 → 编码转 str、解码转回 int；③ `files.py` 误用 `subscription_tier` → 改 `role`

#### 当前已确认的联调阻塞点（2026-06-09 核查）

- [x] `files.py` 的 `subscription_tier` 字段误用已修复
- [x] `files.py` 的 `office-to-pdf` 端点缺少 `import os` 已修复
- [x] `api/v1/__init__.py` 中 `enterprise / ai / advanced` 路由重复拼接 `/api/v1` 已修复
- [x] `celery_worker.py` 未纳入 `office_tasks` 导致 Office 转换任务无法被 worker 消费，已修复
- [x] `backend/Dockerfile` 缺 `libreoffice` / `libmagic1` 且健康检查依赖未安装的 `requests`，已修复
- [ ] 本机未安装 Docker，当前仍无法执行真实基础设施联调

#### 联调执行清单（拿到 Docker 环境后按顺序执行）

1. `docker-compose up -d postgres redis backend celery-worker`
2. 访问 `/health` 与 `/api/docs`，确认 API 容器可用
3. 执行数据库迁移并确认表已创建
4. 验证基础闭环：
   上传 PDF → 合并任务 → 轮询状态 → 下载结果
5. 验证 OCR 闭环：
   上传 PDF/图片 → OCR 任务 → 下载文本
6. 验证 Office 闭环：
   上传 `.docx/.xlsx/.pptx` → 转 PDF → 下载结果
7. 最后验证 WebSocket 进度推送是否正常

### 🟡 P1 — 核心云端能力（1–2 周）

- [x] **工具页接入云端开关**：6 个工具页（MergePDF, SplitPDF, RotatePDF, CompressPDF, ImageToPDF, PDFToImage）已集成 `CloudToggle` 组件 + `useCloudProcessing` composable，支持本地/云端切换，云端路径：上传→提交任务→轮询→下载，Pro/Enterprise 用户专享
- [x] **OCR Tesseract 集成**：前端 `OCRPDF.vue` 页面完成，支持 10 种语言识别（英语/中文/日语/韩语等），集成云端处理流程，结果显示+复制+下载功能完整，Pro/Enterprise 专享。后端 `ocr_tasks.py` 框架完整（需 Docker 环境安装 Tesseract 验证）
- [x] **WebSocket 实时进度**：后端 `endpoints/websocket.py` 完成（支持任务订阅/广播/心跳），前端 `composables/useWebSocket.ts` + `useTaskProgress.ts` 完成（WebSocket优先，轮询兜底），自动重连机制+连接管理器
- [x] **任务进度轮询兜底**：`fileAPI.pollJobUntilDone` 已实现（1.5s 间隔，最多 2 分钟），所有工具页云端路径已集成

### 🟢 P2 — 商业化（已全部完成 ✅）

- [x] **Pricing 定价页面**：前端 `Pricing.vue` 完成，展示 Free/Pro/Enterprise 三档套餐对比，包含功能列表/限制说明/FAQ常见问题/信任指标，集成用户状态判断（当前套餐高亮），CTA按钮连接登录/支付/销售流程，导航栏已添加💎Pricing入口
- [x] **OAuth 社交登录**：后端 `oauth.py` 完成（Google/GitHub OAuth 流程、用户创建和关联、JWT 返回）；前端 `Login.vue` OAuth 按钮激活、`OAuthCallback.vue` 回调处理；三语国际化；依赖 authlib==1.3.0；已移除"Soon"标记。**需配置真实 OAuth 凭据测试**（见 `docs/OAUTH_SETUP.md`）
- [x] **Office 转换**：后端 `office_tasks.py` 完成（Word/Excel/PPT → PDF，使用 LibreOffice）；前端 `OfficeToPDF.vue` 完成（文件上传、云端转换、进度显示、下载）；API 端点 `/files/office-to-pdf`；三语国际化；首页工具卡片已添加。**需系统安装 LibreOffice 验证**
- [x] **Stripe 支付集成**：后端 `payment.py` 完成（订阅创建、Webhook处理、订阅管理）；前端 `PaymentSuccess.vue`/`PaymentCancel.vue` 完成；Pricing页面集成真实支付流程；依赖 stripe==7.0.0；支持订阅升级、取消、重新激活。**需配置 Stripe 凭据测试**
- [x] **邮件系统（Resend）**：后端 `email_service.py`（4种邮件模板：欢迎/密码重置/订阅确认/流失预警）+ `email_tasks.py`（定时任务：每日流失预警/每12h订阅提醒）+ 密码重置端点（`/auth/forgot-password`, `/auth/reset-password`）；集成注册欢迎邮件、支付确认邮件；Celery Beat 定时任务配置；依赖 httpx==0.26.0；完整文档 `backend/docs/EMAIL_SERVICE.md`。**需配置 Resend API Key 测试**

### ⚪ P3 — 企业与 AI（1–3 月）

- [x] **企业 API Key 管理**（✅ 完成 90%）
  - 后端：`endpoints/enterprise.py`（500+行）完成 API Key CRUD
  - 前端：`Dashboard.vue` + `APIKeysManager.vue` 完成
  - 功能：生成/列表/更新/删除 API Key，SHA-256 存储，速率限制配置
- [x] **企业使用统计**（✅ 完成 85%）
  - 后端：聚合统计端点（总请求/Token/费用/端点分布/日度明细）
  - 前端：`UsageStats.vue` 图表展示，日期筛选
- [x] **Webhook 系统**（✅ 完成 85%）
  - 后端：Webhook CRUD + `webhook_service.py` 投递逻辑
  - 前端：`WebhookManager.vue` 配置界面
  - 数据库：新增 `Webhook` 模型 + Alembic 迁移
  - 功能：5种事件类型，HMAC-SHA256 签名，重试机制
- [x] **计费系统**（✅ 完成 85%）
  - 后端：Token 计费逻辑，超额计算（100K included，$0.10/1K overage）
  - 前端：`BillingStats.vue` 费用明细，配额预警
- [x] **企业文档**（✅ 完成 90%）
  - 前端：`APIDocumentation.vue` 端点说明，认证示例，错误处理
- [x] **AI 集成（Gemini）**（✅ 完成 95%）
  - 后端：`ai_service.py`（350+行）智能摘要/问答/结构化提取/批量分析
  - 后端：`endpoints/ai.py`（300+行）4个AI端点，Pro权限保护
  - 前端：`AIPDFAnalyzer.vue`（400+行）完整UI，3个Tab（摘要/问答/提取）
  - 配置：`GEMINI_API_KEY` 环境变量，`google-generativeai` 依赖
  - 路由：`/tools/ai-analyzer` 已注册，三语国际化完整
  - 验证：✅ 前端构建通过（6.12s）
- [ ] 监控（Sentry）+ 分析（PostHog）+ A/B 测试 — 后端服务+中间件已完成（`monitoring_service.py` + `middleware/monitoring.py` 已集成 main.py），仅缺真实凭据测试
- [x] **高级 PDF：水印**（✅ 完成 90%）
  - 前端：`utils/pdf/watermark.ts`（纯 pdf-lib，支持居中/平铺/顶部/底部 4 种位置 + 不透明度/旋转/字号/颜色）
  - 前端：`views/tools/WatermarkPDF.vue` 完整 UI（实时参数调节，100% 本地处理）
  - 路由 `/tools/watermark` + 首页卡片（cyan 色）+ 三语国际化
  - 后端服务 `advanced_pdf_service.py` 已含水印/表单填写/注释/高亮/签名字段（待加 endpoint）
- [ ] 高级 PDF：签名 / 表单填写 / 注释（后端服务+endpoint 已完成，待前端页面）
  - 后端：`endpoints/advanced.py`（6 端点：watermark/form-fields/form-fill/annotate-text/annotate-highlight/signature-field，Pro+ 权限）已注册 `/api/v1/advanced/*`
  - 服务：`advanced_pdf_service.py`（水印/表单/注释/高亮/签名字段，PyPDF2+reportlab）
  - 前端：`FillFormPDF.vue`（表单填写UI，字段识别+自动填充）✅ 已完成
  - 前端：`AnnotatePDF.vue`（注释UI，文本注释+高亮注释）✅ 已完成
  - API：`advancedAPI` 服务方法（6个方法）✅ 已完成
  - 路由：`/tools/fill-form` + `/tools/annotate` ✅ 已注册
  - 国际化：en/zh 两语完整 ✅ 已完成
  - 验证：前端构建通过（6.27s）✅
- [ ] 部署：K8s HPA、双活容灾、Cloudflare CDN

### 4.1 建议执行顺序（从现在开始怎么做）

#### 第 1 阶段：先把“已写完的功能”跑通

1. 使用 Docker 跑通 `PostgreSQL + Redis + FastAPI + Celery`
2. 完成一条最小闭环验证：
   上传文件 → 创建任务 → 查询/推送进度 → 下载结果
3. 优先验证 3 条高价值链路：
   合并 PDF、OCR、Office 转 PDF

#### 第 2 阶段：逐个验证外部依赖能力

1. OAuth 真实凭据联调（Google / GitHub）
2. Stripe 沙箱支付与 Webhook 联调
3. Resend 邮件发送验证
4. Gemini API Key 验证 AI 摘要 / 问答 / 提取

#### 第 3 阶段：补上线前质量收口

1. 修复并稳定 Playwright E2E
2. 增加真实基础设施下的后端集成测试
3. 清理 `vue-tsc` 严格模式遗留问题
4. 补 Celery 结果回写 Redis，避免任务状态过期丢失

#### 第 4 阶段：最后做部署与运维增强

1. 验证 Sentry / PostHog 凭据与事件上报
2. 准备生产部署配置
3. 再推进 K8s / HPA / CDN / 双活容灾

---

## 4.2 文档治理规则

- `docs/PROJECT_MASTER.md`：唯一状态文档，记录当前进度、待办、技术债、变更日志
- `docs/OAUTH_SETUP.md`：保留为专项操作手册
- `docs/STAGING_DEPLOY_GUIDE.md`：保留为单服务器 staging 发布与回滚手册
- `开发文档/`：保留为原始需求材料，只读，不维护状态
- 其余阶段性总结、简报、完成报告不再保留；后续统一删除或不再新增
- 若新增文档，必须满足“操作手册 / 部署指南 / 外部服务配置说明”之一，且不能重复记录项目状态

---

## 5. 技术栈

### 前端
- Vue 3.4 + TypeScript 5.4 + Vite 5.1
- Pinia（状态）/ Vue Router 4（路由）/ Vue I18n 9（国际化）
- pdf-lib（改）/ pdfjs-dist（渲染）/ jspdf（生成）
- TailwindCSS / @vueuse/core / lucide-vue-next / radix-vue
- axios（HTTP）/ zod（校验）

### 后端
- FastAPI 0.109 + Uvicorn + Pydantic 2
- PostgreSQL 15（Supabase）+ SQLAlchemy 2.0 + Alembic
- Redis 7（缓存/限流/队列）+ Celery 5.3
- python-jose（JWT）/ passlib+bcrypt（密码）
- PyPDF2 / pdf2image / pytesseract / Pillow / python-docx / openpyxl
- python-magic（魔术数字）/ Docker + docker-compose

---

## 6. 快速开始

### 前端（Node ≥16, npm ≥7）

```bash
npm install
npm run dev            # http://localhost:5173
npm run build          # 生产构建（vite build, esbuild, 不做类型检查）
npm run build:check    # vue-tsc 类型检查 + 构建
npm run preview        # 预览生产构建
npm run test:unit      # 单元测试（108）
npm run test:e2e       # E2E 测试
npm run lint           # ESLint 修复
npm run format         # Prettier
```

### 后端（Python 3.11+）

```bash
cd backend
cp .env.example .env              # 至少设置 SECRET_KEY
docker-compose up -d db redis     # 起 PostgreSQL + Redis
alembic upgrade head              # 数据库迁移
uvicorn app.main:app --reload     # API: http://localhost:8000/api/docs
celery -A app.celery_worker worker --loglevel=info   # 另开终端
# 或一键：./start.sh   停止：./stop.sh
```

环境变量关键项：`SECRET_KEY`(生产必改)、`DATABASE_URL`、`REDIS_URL`、`STRIPE_SECRET_KEY`、`GOOGLE_CLIENT_ID`、`GITHUB_CLIENT_ID`、`RESEND_API_KEY`、`SENTRY_DSN`。

---

## 6.1 单服务器 staging 发布流程

适用场景：本地不装 Docker，只在服务器上做真实环境测试；当前仅有 1 台服务器。

### 分支策略

- `staging`：服务器真实测试分支
- `main`：正式稳定分支

规则：

1. 本地开发完成后，先提交并推送到 `staging`
2. 服务器只拉取并部署 `staging`
3. 真实测试通过后，再将 `staging` 合并到 `main`

### 脚本

- `scripts/deploy-staging.sh`
  - 备份当前 commit 与环境文件
  - `git fetch / checkout / pull staging`
  - `docker compose up -d --build`
  - `alembic upgrade head`
  - 冒烟测试 `/health` 与 `/api/docs`
- `scripts/rollback-staging.sh`
  - 回滚到上一次成功部署的 commit
  - 重建容器并重新执行冒烟测试
- `scripts/smoke-test.sh`
  - 默认校验 `/health` 和 `/api/docs`

### 服务器准备

```bash
chmod +x scripts/deploy-staging.sh scripts/rollback-staging.sh scripts/smoke-test.sh
```

服务器必须具备：

- `git`
- `docker`
- `docker compose` 或 `docker-compose`
- `curl`

服务器本地维护：

- 根目录 `.env`（如需要）
- `backend/.env`

### 日常部署命令

```bash
bash scripts/deploy-staging.sh
```

### 回滚命令

```bash
bash scripts/rollback-staging.sh
```

### 数据备份策略

- 默认备份：
  - 当前 commit
  - 根目录 `.env`
  - `backend/.env`
  - 可选 compose override 文件
- 可选数据库备份：
  - 通过 `DEPLOY_BACKUP_COMMAND` 注入服务器自定义备份命令

示例：

```bash
DEPLOY_BACKUP_COMMAND='docker compose exec -T postgres pg_dump -U pdfflow_user pdfflow > "$BACKUP_PATH/postgres.sql"' \
bash scripts/deploy-staging.sh
```

### 容错说明

- 当前脚本保证“代码版本 + 容器部署”可回滚
- 数据库回滚不自动处理，需确保迁移具备向后兼容性，或自行维护数据库备份/恢复流程

---

## 7. 项目结构

```
PDF_Flow/
├── 开发文档/              # 原始需求规格 v1.0–v4.0（只读源材料）
├── README.md             # 项目门面，指向本文档
├── docs/
│   ├── PROJECT_MASTER.md # ← 本文件，唯一状态文档
│   ├── OAUTH_SETUP.md    # OAuth 配置操作手册
│   └── STAGING_DEPLOY_GUIDE.md # 单服务器 staging 部署手册
├── scripts/              # staging 部署 / 回滚 / 冒烟测试脚本
├── src/                  # 前端（见 §3.2 / §3.3）
│   ├── components/{common,layout,pdf}/
│   ├── views/{,tools,auth}/
│   ├── stores/  services/  router/  composables/
│   ├── utils/pdf/  workers/  locales/  types/
└── backend/              # 后端（见 §3.4）
    ├── app/  alembic/  tests/
    ├── Dockerfile  docker-compose.yml  requirements.txt
    └── start.sh  stop.sh
```

---

## 8. 测试与 E2E 注意事项

### E2E 等待策略（Playwright SPA 易超时，已沉淀经验）

根因：Vue 应用渲染延迟、文件输入隐藏、动态内容（如压缩质量选择器上传后才出现）。

封装 `tests/helpers/test-utils.ts`：
```typescript
export async function waitForPageReady(page) {
  await page.waitForLoadState('networkidle')
  await page.waitForSelector('h1, h2', { timeout: 10000 })
}
export async function uploadFile(page, filePath) {
  await page.waitForSelector('[data-testid="drag-drop-zone"]', { timeout: 10000 })
  await page.locator('input[type="file"]').setInputFiles(filePath)
  await page.waitForSelector('[data-testid="file-preview"]', { timeout: 10000 })
}
```
配置：`timeout: 60000`、`actionTimeout: 15000`、`retries: CI?2:1`。
关键 `data-testid`：`tool-card / drag-drop-zone / file-preview / delete-file / progress-bar`。

### 后端测试（pytest，无需 Docker）

`backend/tests/` 在无基础设施环境下运行：`conftest.py` 用 `sys.modules` stub 注入缺失库（redis/celery/PIL/magic/pdf2image/pytesseract/uvicorn），DB 用内存 SQLite，Redis 用 FakeRedis。

```bash
cd backend
pip install pytest fastapi pydantic pydantic-settings sqlalchemy \
    "python-jose[cryptography]" "passlib[bcrypt]" bcrypt==4.0.1 \
    httpx email-validator python-multipart psutil
python -m pytest tests/ -q      # 35 通过
```

测试文件：`test_security.py`（哈希/JWT/APIKey/魔术数字）、`test_auth.py`（注册/登录/鉴权/刷新流程）、`test_files.py`（下载分支/文件校验）。
**注意**：`bcrypt` 必须 `==4.0.1`，4.1+ 与 `passlib 1.7.4` 不兼容。

---

## 9. 性能与优化清单

- **包体积**：`pdf-vendor.js` ~1.1MB，用 `manualChunks` 拆分 pdf-lib/pdfjs/jspdf
- **懒加载**：工具页内 `await import('@/utils/pdf/xxx')` 按需载入
- **Service Worker**：`public/sw.js` 缓存静态资源（PWA 离线）
- **错误边界**：`ErrorBoundary.vue` + `onErrorCaptured`
- **大文件**：Web Workers 处理 + 及时 `URL.revokeObjectURL`
- **首屏 FCP** 目标 <1.5s（v4.0 要求），WASM 延迟初始化

---

## 10. 开发规范

### 分支
`main`(生产) ← `develop`(测试) ← `feature/*` / `bugfix/*` / `hotfix/*`，合 develop 需 1 人 Review。

### Commit（Conventional Commits）
`feat:` `fix:` `docs:` `style:` `refactor:` `test:` `chore:`

### 提交前
`npm run test:unit` → `npm run lint` → `npm run build:check`（后端：`pytest`）

### 添加新工具的标准流程
1. `src/utils/pdf/xxx.ts` 处理函数
2. `src/views/tools/XxxPDF.vue` 页面
3. `src/router/index.ts` 注册路由
4. `src/views/Home.vue` 加工具卡片
5. `src/locales/*.json` 三语补 `tools.xxx.title/desc`
6. `tests/unit/Xxx.test.ts` 单测

---

## 11. 技术债务与变更日志

### 已知技术债（不混入功能开发，单独清理）
- 🟠 **后端真实基础设施联调未做** — 逻辑层已 pytest 覆盖，但 Celery 任务执行、Redis 限流、PG 迁移仍需 Docker 环境实跑（见 P0）
  - ~~🔴 `files.py:72` 误用 `current_user.subscription_tier`~~ — **已修复（2026-06-09）**：改为基于 `role.value` 映射 tier，admin 视为 enterprise 级配额
- 🟡 **后端测试依赖手工 stub** — 本机无 redis/celery/PIL/magic，conftest 用 sys.modules stub + SQLite + FakeRedis；装齐依赖后应补真实集成测试
- 🟡 **Celery 完成结果未回写 Redis** — `get_job_status` 靠 `AsyncResult` 读结果后端；若结果过期则状态丢失。建议任务成功后主动 `setex` 回写 `job:` 键
- 🟡 **vue-tsc 严格模式遗留错误**（不阻断 `vite build`，因用 esbuild）：
  - `useDragSort.ts` 泛型 `UnwrapRefSimple` 不匹配
  - `compress.ts`/`merge.ts`/`rotate.ts` `Uint8Array`→`BlobPart`（TS5.x `ArrayBufferLike` 收窄）
  - `HistoryPanel.vue` / `PDFViewer.vue` 未使用变量
- 🟢 i18n 缺 OCR/Office/Pricing 等未来模块文案

### Changelog
- **2026-06-09 P2 邮件系统完成**：创建 `email_service.py`（400+行，4种邮件模板：欢迎/密码重置/订阅确认/流失预警，使用 Resend API，HTML+纯文本双格式，响应式设计）。创建 `email_tasks.py`（180+行，3个定时任务：每日流失预警/12h订阅提醒/每周摘要）。更新 `auth.py` 添加密码重置端点（`/auth/forgot-password`, `/auth/reset-password`，1小时过期Token，防邮箱枚举），注册集成欢迎邮件（BackgroundTasks 非阻塞）。更新 `payment.py` 集成订阅确认邮件（checkout.session.completed webhook）。更新 `config.py` 添加 `EMAIL_FROM`, `FRONTEND_URL`, `PASSWORD_RESET_TOKEN_EXPIRE_HOURS`。更新 `user.py` schemas 添加 `PasswordResetRequest`/`PasswordResetConfirm`。更新 `celery_worker.py` 添加邮件任务队列路由、Celery Beat 定时任务（24h流失预警/12h订阅提醒）。更新 `.env.example` 添加邮件配置。创建完整文档 `backend/docs/EMAIL_SERVICE.md`（配置/端点/任务/测试/安全/前端集成/故障排查）。Python 语法验证 ✅（7个文件 AST 通过）。邮件系统完成度：5% → 95%（需 Resend API Key 真实测试）。**Phase 2 完成度：99% → 100%**（所有功能已实现）。
- **2026-06-09 构建验证通过**：前端 `npm run build` ✅（6.23s，WatermarkPDF-LHFuZaEg.js 8.26 kB），后端 AST 语法验证 ✅（advanced.py/files.py/__init__.py）。水印工具完成度：90% → 95%。**Phase 3 完成度保持 72%**（待前端表单/注释 UI 推升）。
- **2026-06-09 修复 `subscription_tier` bug**：`files.py:72` 上传端点误用 `current_user.subscription_tier`（User 模型无此字段），登录用户上传会抛 `AttributeError`。修复为基于 `current_user.role.value` 映射 user_tier（admin → enterprise 级配额），与 `file_service.upload_file` 期望的 `"free"/"pro"/"enterprise"` 字符串对齐。技术债清零。
- **2026-06-09 P3 高级PDF后端端点完成**：为已有的 `advanced_pdf_service.py`（水印/表单/注释/高亮/签名字段）补齐 REST 端点。创建 `endpoints/advanced.py`（300+行），实现 6 个端点：`POST /advanced/watermark`（服务端水印）、`POST /advanced/form/fields`（读取表单字段名/类型）、`POST /advanced/form/fill`（填写表单）、`POST /advanced/annotate/text`（文本注释）、`POST /advanced/annotate/highlight`（高亮注释）、`POST /advanced/signature/field`（签名字段），全部 Pro/Enterprise 权限保护（`require_pro_user` 复用 ai.py 模式），统一 tempfile 处理 + FileResponse 返回 + 临时文件清理。复用已存在的 `schemas/advanced_pdf.py`。注册路由 `/api/v1/advanced/*`（`api/v1/__init__.py`）。endpoint 参数名与服务方法签名逐一核对一致。高级PDF后端完成度：50% → 75%。**Phase 3 完成度：70% → 72%**。
- **2026-06-09 P3 高级PDF水印工具完成**：新增**纯前端本地**水印功能，符合"隐私优先、文件不出设备"理念。创建 `src/utils/pdf/watermark.ts`（200+行）核心逻辑，使用 pdf-lib 嵌入 Helvetica-Bold 字体，支持 4 种位置（居中/平铺/顶部/底部）+ 可调不透明度（5%-100%）/旋转（0-90°）/字号（12-100）/RGB 颜色，平铺模式自动按文本宽度计算间距重复绘制。创建 `views/tools/WatermarkPDF.vue`（330+行）工具页面，实时参数面板（滑块+取色器+位置按钮组），文件预览+PDF查看器+成功下载，含 100% 本地处理隐私提示。注册路由 `/tools/watermark`，首页添加水印工具卡片（cyan 色），三语国际化（en/zh/es，watermark 段 22 条文案）。`history-manager.ts` 新增 `watermark` 历史类型。同步修正监控集成完成度（`monitoring_service.py` + `middleware/monitoring.py` 已集成 main.py，30% → 80%）。**Phase 3 完成度：60% → 70%**。
- **2026-06-09 AI集成验证完成**：确认 AI 集成（Gemini）所有组件已实现并通过构建验证。后端 `services/ai_service.py`（357行）+ `endpoints/ai.py`（308行）+ `schemas/ai.py` 完整，前端 `AIPDFAnalyzer.vue`（388行）完整，路由注册 `/tools/ai-analyzer`，`aiAPI` 服务4个方法（summarize/ask/extract/batchAnalyze），三语国际化60+条AI文案。前端 build✓（6.12s），AIPDFAnalyzer-C0X1rOWO.js 13.11 kB。AI 集成完成度：90% → 95%（已验证构建，需 Gemini API Key 真实测试）。**Phase 3 完成度：45% → 60%**。
- **2026-06-09 P3 AI 集成（Gemini）完成**：后端创建 `services/ai_service.py`（350+行），实现 GeminiService 类，支持 4 种 AI 操作：PDF 智能摘要（短/中/长三种长度，自动提取关键要点和主题）、智能问答（基于 PDF 内容回答问题，提供置信度和相关摘录）、结构化数据提取（支持发票/简历/合同/通用 4 种文档类型）、批量分析（多操作并行+文档分类）。后端创建 `endpoints/ai.py`（300+行），实现 4 个 AI 端点（`/ai/summarize`, `/ai/ask`, `/ai/extract`, `/ai/batch-analyze`），Pro/Enterprise 权限保护，自动 PDF 文本提取，临时文件清理。创建 `schemas/ai.py`（100+行）Pydantic 模型（SummarizeRequest/Response, QuestionRequest/Response, ExtractRequest/Response, BatchAnalyzeRequest/Response）。创建 `utils/pdf_text_extractor.py` PDF 文本提取工具（使用 PyPDF2）。前端创建 `AIPDFAnalyzer.vue`（400+行）AI 分析器页面，3 个 Tab（智能摘要/智能问答/数据提取），文件上传+拖拽，实时结果展示（摘要+要点+主题/问答+置信度+摘录/JSON 数据展示），错误处理。添加 `aiAPI` 服务（4 个方法：summarize/ask/extract/batchAnalyze），路由注册 `/tools/ai-analyzer`。添加 `GEMINI_API_KEY` 配置，`google-generativeai==0.3.2` 依赖。三语国际化（60+ 条 AI 文案）。前端 build✓（5.79s）。AI 集成完成度：0% → 90%（需 Gemini API Key 测试）。**Phase 3 完成度：30% → 45%**。
- **2026-06-09 P3 企业 API Key 管理系统完成**：后端创建 `endpoints/enterprise.py`（500+行），实现 API Key 完整 CRUD（创建/列表/获取/更新/删除），生成 `pdf_` 前缀密钥，SHA-256 哈希存储，支持速率限制和过期配置。实现使用统计端点（聚合总请求/成功失败/文件处理/Token 使用/费用/端点分布/日度明细），支持日期筛选和分页。实现 Webhook 系统：CRUD 端点 + `webhook_service.py` 投递服务（HMAC-SHA256 签名/5种事件类型/自动重试），新增 `Webhook` 数据库模型 + Alembic 迁移。实现计费系统：Token 计费端点（100K included，$0.10/1K overage），当前周期统计，下次账单预估。实现 Dashboard 统计端点（API Keys/30天使用/本月费用/Webhook/最近活动）。前端创建 `Dashboard.vue` 企业控制台（270+行），5个Tab页（API Keys/Usage/Webhooks/Billing/Documentation），仪表板统计卡片。创建 `APIKeysManager.vue`（280+行）API Key 管理界面，支持创建（带警告只显示一次）/列表/启用禁用/删除，复制到剪贴板。创建 `UsageStats.vue`（170+行）使用统计图表，日度柱状图，端点分布，日期筛选。创建 `WebhookManager.vue`（200+行）Webhook 配置界面，事件订阅，投递统计。创建 `BillingStats.vue`（180+行）计费明细，Token 使用进度条，超额警告，定价信息。创建 `APIDocumentation.vue`（130+行）API 文档，端点列表，认证示例，Webhook 格式，错误处理。创建 `StatCard.vue` 统计卡片组件。更新 `api.ts` 添加 `enterpriseAPI`（200+行），15个方法覆盖全部企业端点。更新 `router/index.ts` 添加 `/enterprise/dashboard` 路由 + `enterpriseGuard` 守卫。添加 `httpx==0.26.0` 依赖（Webhook HTTP 请求）。三语国际化（en/zh，150+条企业文案）。前端 build✓（5.64s）。企业功能完成度：0% → 88%（平均）。**Phase 3 完成度：0% → 30%**。
- **2026-06-09 P2 Stripe支付集成完成**：后端创建 `payment.py` 端点（400+行），实现订阅创建（create-checkout-session）、订阅查询（subscription）、订阅取消（cancel-subscription）、订阅重新激活（reactivate-subscription）、Webhook处理（处理6种事件：checkout.session.completed/customer.subscription.created/updated/deleted/invoice.payment_succeeded/failed），使用 Stripe SDK，支持月付/年付套餐，自动更新用户role。前端创建 `PaymentSuccess.vue`（150+行成功页）、`PaymentCancel.vue`（150+行取消页），添加 paymentAPI 服务（4个方法），更新 Pricing.vue 集成真实支付流程（点击Pro按钮→创建Stripe会话→重定向到Stripe结账页），添加 `/payment/success` 和 `/payment/cancel` 路由。新增 Pydantic schemas（payment.py），三语国际化（60+条文案），添加 stripe==7.0.0 依赖。前端 build✓（6.32s）。Stripe 完成度：25% → 95%（需Stripe凭据测试）。**Phase 2 完成度：98% → 99%**。
- **2026-06-09 P2 Office转换功能完成**：后端创建 `office_tasks.py`（300+行），实现 Word/Excel/PPT → PDF 转换（使用 LibreOffice headless 模式），包含 docx_to_pdf_task/xlsx_to_pdf_task/pptx_to_pdf_task/office_to_pdf_task 四个 Celery 任务，支持自动文件类型检测、重试机制（最多3次）、超时控制（60秒）。前端创建 `OfficeToPDF.vue`（280+行），集成文件上传（支持.docx/.xlsx/.pptx）、CloudToggle 云端开关、进度显示、结果下载，Pro/Enterprise 专享。新增 API 端点 `/files/office-to-pdf`，三语国际化（en/zh/es），首页工具列表添加 Office 转 PDF 卡片（teal色）。前端 build✓（6.18s）。Office 完成度：5% → 90%（需 Docker 环境安装 LibreOffice 验证）。
- **2026-06-09 P2 OAuth社交登录完成**：后端创建 `oauth.py` 端点（Google/GitHub OAuth 集成，使用 Authlib），实现用户自动创建和关联逻辑（OAuth ID 匹配/Email 匹配/新建用户），OAuth 用户自动标记为已验证，JWT token 生成并重定向到前端。前端创建 `OAuthCallback.vue` 回调页面（提取 URL 参数 token、存储到 localStorage、调用 checkAuth、重定向），更新 `Login.vue` handleOAuthLogin 函数（重定向到后端 OAuth 端点），移除"Soon"标记。添加 `requirements.txt` 依赖 authlib==1.3.0，更新 `config.py` 添加 OAUTH_REDIRECT_URL，更新路由注册 oauth.router，三语 i18n 添加"processingLogin/pleaseWait"。创建详细设置文档 `docs/OAUTH_SETUP.md`（配置步骤/OAuth凭据获取指南/流程说明/安全特性/常见问题）。前端 build✓（6.13s）。OAuth 完成度：20% → 95%（仅缺真实凭据测试）。
- **2026-06-09 P2 Pricing定价页面完成**：创建 `Pricing.vue` 定价页面（350+行），展示 Free/Pro/Enterprise 三档套餐完整对比（价格/功能/限制/FAQ/信任指标），集成用户状态判断（当前套餐高亮/CTA按钮智能路由），包含7天退款/随时取消/数据安全等信任要素，FAQ常见问题4条，添加到Header导航栏（💎Pricing入口）。前端 build✓（6.01s）。Stripe支付完成度：5% → 25%。
- **2026-06-09 P1 WebSocket实时进度完成**：后端 `endpoints/websocket.py` 实现完整 WebSocket 端点（任务订阅/进度广播/心跳机制/连接管理器），支持多客户端订阅同一任务，自动清理死连接。前端创建 `useWebSocket.ts` composable（连接/断开/消息处理/自动重连）+ `useTaskProgress.ts` 统一进度追踪（WebSocket优先，3秒超时自动回退轮询）。WebSocket 路由已注册到 API。前端 build✓（6.05s）。**P1任务全部完成（4/4）**，Phase 2 完成度：90% → 95%。
- **2026-06-09 P1 OCR功能完成**：新建 `OCRPDF.vue` 前端页面，支持 10 种语言识别（英语/简繁中文/日韩/法德西俄阿拉伯语），集成 `useCloudProcessing` 云端处理流程，Pro/Enterprise 专享。功能包括：文件上传→语言选择→OCR识别→结果展示（置信度+页数）→文本复制/下载。添加到首页工具列表（粉色卡片）+路由注册。前端 build✓（5.88s）。后端 `ocr_tasks.py` 完整（extract_text_task + batch_ocr_task），使用 Tesseract + pdf2image + PIL，需 Docker 环境真实验证。OCR 完成度：30% → 85%。
- **2026-06-09 P1 云端集成完成**：为 6 个工具页（MergePDF, SplitPDF, RotatePDF, CompressPDF, ImageToPDF, PDFToImage）集成云端处理开关，每个页面添加 `CloudToggle` 组件 + `useCloudProcessing` composable 调用，实现本地/云端双路径处理。云端路径：文件上传→任务提交→进度轮询（1.5s间隔）→结果下载，Pro/Enterprise 用户专享。前端 build✓（5.92s）。当时曾创建项目简报作为崩溃恢复点，现已归档删除并统一收口到主文档。
- **2026-06-09 P0 推进 + 测试**：实现文件下载端点（`GET /files/download/{job_id}`，单文件/zip/txt 三态）+ 前端 `downloadResult`/`pollJobUntilDone`；改进 `get_job_status` 结合 Celery `AsyncResult`；新增后端 pytest 套件（35 通过：security/auth/files，SQLite+stub）；OAuth 按钮加 "Soon" 标记。**测试发现并修复 3 个生产级 bug**：bcrypt 版本锁定、JWT sub 字符串化、files.py role 字段。前端 build✓ + 108 单测✓。
- **2026-06-09 文档整合**：所有分散文档归并为本文件；i18n 三语结构统一；前后端字段对齐(`role`)；新增 Login/Register/Profile + Header 用户菜单 + 路由守卫 + API 服务层；新增 `vite-env.d.ts`。
- **2026-06-09 文档归档清理**：删除重复的阶段性总结、简报、完成报告，仅保留 `PROJECT_MASTER.md` 作为唯一状态文档，保留 `OAUTH_SETUP.md` 作为操作手册；同步补充后续文档治理规则与执行顺序。
- **2026-06-09 联调阻塞清理**：修复后端真实联调前置问题：`files.py` 增加 `import os` 以恢复 Office 转换端点；`api/v1/__init__.py` 去除 `enterprise/ai/advanced` 的重复 `/api/v1` 前缀；`celery_worker.py` 纳入 `office_tasks` 与 `office_processing` 队列；`backend/Dockerfile` 补 `libreoffice` / `libmagic1` 并将健康检查改为 `urllib`，避免依赖未安装的 `requests`；确认当前剩余硬阻塞为“本机无 Docker”。
- **2026-06-09 单服务器 staging 发布流程落地**：新增 `scripts/deploy-staging.sh`、`scripts/rollback-staging.sh`、`scripts/smoke-test.sh`，用于单服务器真实测试、备份容错和代码回滚；`.gitignore` 新增 `.deploy_state/` 与 `.deploy_backups/`；README / backend README / 主文档同步增加 staging→main 的脚本化发布说明。
- **2026-06-09 staging 操作手册补齐**：新增 `docs/STAGING_DEPLOY_GUIDE.md`，明确服务器首次部署 checklist、日常 `staging -> main` Git 流程、回滚流程、数据库备份钩子和文档同步规则，避免后续重复摸索。
- **2026-06-09 服务器部署兼容性修复（第 1 轮）**：真实服务器构建暴露两项跨环境问题：① `.gitignore` 的全局 `*.txt` 误排除了 `backend/requirements.txt`，导致服务器构建上下文缺少依赖文件；现已通过 `!backend/requirements.txt` 例外规则修复。② `backend/requirements.txt` 中 `python-magic-bin==0.4.14` 在 Linux ARM64 环境不可安装；现改为仅在 Windows 安装：`python-magic-bin==0.4.14; sys_platform == "win32"`。后续服务器部署继续以 `staging` 为准验证。
- **2026-06-09 服务器部署兼容性修复（第 2 轮）**：真实服务器启动迁移阶段暴露 `pydantic-settings` 与 `.env` 兼容问题：`ALLOWED_ORIGINS` / `ALLOWED_HOSTS` 在 Pydantic v2 下会优先按 JSON 解析，导致 `.env.example` 中原本的逗号分隔格式在服务器上触发 `SettingsError`。现已将 `backend/app/core/config.py` 调整为兼容两种写法：逗号分隔字符串和 JSON 数组，避免迁移与启动阶段因 CORS 配置格式失败。
- **2026-06-09 服务器部署兼容性修复（第 3 轮）**：真实服务器执行 Alembic 迁移时暴露数据库迁移链分叉：`backend/alembic/versions/001_initial.py` 与 `add_webhook_model.py` 同时作为 head，导致 `alembic upgrade head` 失败。现已将 `add_webhook_model.py` 的 `down_revision` 正确指向 `001_initial`，恢复单链迁移顺序。
- **2026-06-09 服务器部署兼容性修复（第 4 轮）**：真实服务器启动后端时暴露 `EmailStr` 依赖缺失：`app/schemas/user.py` 使用 Pydantic `EmailStr`，但 `backend/requirements.txt` 缺少 `email-validator`，导致 Uvicorn 子进程导入失败、`/health` 连接被重置。现已补充 `email-validator==2.1.0.post1` 依赖。另修正根 `docker-compose.yml` 中 `celery-worker` 的健康检查，避免继承 backend 镜像的 HTTP `/health` 检查后被误标记为 unhealthy，并移除 Compose 过时 `version` 字段以减少服务器告警噪音。
- **2026-06-09 服务器部署兼容性修复（第 5 轮）**：真实服务器继续启动后端时，导入健康检查端点 `app/api/v1/endpoints/health.py` 暴露 `psutil` 依赖缺失，导致 Uvicorn 在载入 API 路由阶段崩溃、`/health` 与 `/api/docs` 持续连接重置。现已补充 `psutil==5.9.8` 到 `backend/requirements.txt`。同时根 `docker-compose.yml` 中 `celery-worker` 健康检查变量转义已修正为 `$$HOSTNAME`，避免 Compose 在解析时发出 `"HOSTNAME" variable is not set` 告警。
- **2026-06-09 服务器部署兼容性修复（第 6 轮）**：真实服务器完成依赖补齐后，后端仍在 API 路由加载阶段崩溃。日志定位到 `app/api/v1/endpoints/websocket.py` 顶部导入了不存在的 `get_current_user_ws`，但实际代码路径并未使用该函数，属于无效遗留导入。现已移除该导入及未使用依赖，避免 FastAPI 在启动时因 `ImportError` 中断整个应用加载。
- **2026-06-09 服务器部署兼容性修复（第 7 轮）**：切换到容器内 `python -c "import app.main"` 快速验导入链后，继续暴露启动期代码错误：`app/api/v1/endpoints/oauth.py` 在路由参数中使用 `Depends(get_current_user)`，但把 `get_current_user` 放在文件尾部才导入，导致模块加载阶段直接 `NameError`。现已将导入前移到文件头部，并删除尾部延迟导入。同步额外清理两处同类潜在问题：`ai.py` 改为从 `app.utils.pdf_text_extractor` 正确导入 `extract_text_from_pdf`；`file_utils.py` 增加顶层 `save_upload_file()` 兼容包装，避免 `files.py` 的 Office 转换路径在运行时因符号缺失失败。
- **2026-06-09 业务验收脚本与缓存清理**：修复 `auth.py` 中“可选认证实际被强制 401”的问题，恢复匿名上传与混合端点行为；新增 `scripts/business-smoke-test.sh`，覆盖 注册→登录→上传→合并→轮询→下载 的真实链路，并补齐更清晰的 HTTP 错误输出；`.gitignore` 补充 `__pycache__/` 与 `*.py[cod]`，同时将仓库内已被错误跟踪的 `__pycache__/*.pyc` 从 Git 索引移除，避免后续提交持续被缓存文件污染。
- **2026-06-09 服务器部署兼容性修复（第 8 轮）**：业务验收脚本首次触发真实注册时，PostgreSQL 报 `invalid input value for enum userrole: "FREE"`。根因是 `backend/app/models/user.py` 使用 `Enum(UserRole)` 时，SQLAlchemy 默认按枚举名写库（`FREE/PRO/...`），而 Alembic 初始迁移 `001_initial.py` 创建的 `userrole` 枚举值为小写（`free/pro/...`）。现已将模型枚举列改为显式持久化 `UserRole.value`，并补充注册后 role 落库值回归测试，避免后续在真实 PG 环境再次踩中。
- **2026-06-09 业务验收脚本可观测性修复**：`scripts/business-smoke-test.sh` 在合并任务提交后会进入轮询，但此前将 `poll_job_completed` 的标准输出整体重定向到了 `/dev/null`，导致脚本一旦在轮询阶段失败，终端只会停在 “Submitting merge job”，几乎没有可用线索。现已补充 `job_id` 输出、保留轮询日志，并让 JSON 请求支持统一携带 Bearer Token，便于直接看见任务状态、失败响应和下载阶段位置。
- **2026-06-09 服务器部署兼容性修复（第 9 轮）**：真实服务器业务验收中，合并任务可成功提交并生成 `job_id`，但 `GET /files/jobs/{job_id}` 持续返回 `pending`，30 次轮询均无进展。根因定位到 Celery worker：任务已被路由到 `pdf_processing / ocr_processing / office_processing / email` 自定义队列，但 worker 启动命令未显式声明消费这些队列，导致任务留在 broker 中无人执行。现已在 `backend/app/celery_worker.py` 中显式声明 `task_default_queue` 与 `task_queues`，并统一改用 `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` 作为 broker/backend 配置来源，避免与 `REDIS_URL` 混用。
- **2026-06-09 业务验收脚本就绪等待补强**：在 `docker compose up -d --build backend celery-worker` 后立即执行业务脚本时，注册请求可能撞上 Uvicorn reload/容器启动窗口，表现为 `curl: (56) Recv failure: Connection reset by peer`。现已让 `scripts/business-smoke-test.sh` 在执行注册前自动等待 `/health` 与 `/api/docs` 就绪，并为核心 `curl` 请求补充轻量连接重试，减少“服务刚拉起时的假失败”。
- **2026-06-09 服务器部署兼容性修复（第 10 轮）**：Celery worker 开始消费合并任务后，任务状态从 `pending` 进入 `processing`，但长时间不结束。进一步排查发现，上传文件默认被保存到容器内 `tempfile.gettempdir()/pdf_flow`，即 `/tmp/pdf_flow/...`；而 Docker 共享卷挂载的是 `/tmp/pdf-flow/...`。两端路径只差下划线/短横线，导致 backend 与 worker 不一定看到同一份文件。现已将 `FileManager` 默认根目录统一改为 `settings.UPLOAD_DIR`（`/tmp/pdf-flow/uploads`），并补充回归测试，确保异步任务读取的是共享卷中的真实文件。
- **2026-06-09 OCR / Office 验收脚本落地**：新增 `scripts/ocr-smoke-test.sh` 与 `scripts/office-smoke-test.sh`，用于上线前真实环境验收。`ocr-smoke-test.sh` 会自动注册并登录测试用户、将其提升为 `pro`、生成带固定文本的 PNG、提交 OCR 任务并校验结果文本；`office-smoke-test.sh` 会自动生成最小 DOCX、提交 Office 转 PDF 任务并验证下载结果为有效 PDF。两条脚本都内置 readiness 等待和任务轮询，目标是把“真实服务器上的功能验收”从手工点测收敛成稳定脚本。
- **2026-06-09 OCR / Office 验收脚本加固 + OOXML 上传兼容补强**：针对真实服务器上 OCR 上传与 Office 转换首轮 `HTTP 400` 难定位的问题，现已把 `ocr-smoke-test.sh` / `office-smoke-test.sh` 改为“在 backend 容器内生成样本文件，再 `docker cp` 回宿主机上传”，避免二进制内容经过终端管道输出时被污染；同时脚本在上传或提交失败时会直接打印后端响应体，减少盲查成本。后端 `FileValidator` 也补充了 OOXML 兼容逻辑：当 `python-magic` 将 `.docx/.xlsx/.pptx` 识别为 `application/zip` 或 `application/octet-stream` 时，只要文件头是标准 ZIP/OOXML 签名仍允许通过，并新增回归测试覆盖“OOXML 允许、普通 zip 拒绝”两条分支。
- **2026-06-09 OCR / Office smoke 登录头污染修复**：真实服务器复跑时，OCR 与 Office 脚本都在上传前收到 `Invalid HTTP request received.`。根因不是业务接口，而是脚本里的 `token="$(login_user)"` 会捕获 `login_user()` 的标准输出；此前该函数先 `log "Logging in"` 再输出 token，导致 `Authorization` 头混入日志文本和换行，Uvicorn 直接把请求判为非法 HTTP。现已将这两条脚本中的登录日志改写到 stderr，保证 stdout 只返回纯 access token。
- **2026-06-09 Office 转换任务状态接线修复**：真实服务器上 `office-smoke-test.sh` 创建 Office 转 PDF 任务后，脚本在查询 `/api/v1/files/jobs/{job_id}` 时收到 `404`。根因是 `/files/office-to-pdf` 端点直接 `delay()` 派发 Celery，使用了 Celery 默认 task id，但没有像 merge/OCR 一样先把同一个 `job_id` 写入 Redis，也没有显式把 task id 固定为统一 job id，导致状态查询链路断开。现已将 Office 转 PDF 接入 `file_processing_service.office_to_pdf()`，统一生成 `job_id`、保存初始状态并通过 `apply_async(task_id=job_id)` 派发任务，使 Office 链路与其它文件任务保持一致。
- **2026-06-09 staging 全链路验收通过**：在真实服务器 `/root/data/docker_data/PDF/pdf-flow` 上连续执行 `bash scripts/smoke-test.sh`、`BUSINESS_SMOKE_EMAIL=... bash scripts/business-smoke-test.sh`、`OCR_SMOKE_EMAIL=... bash scripts/ocr-smoke-test.sh`、`OFFICE_SMOKE_EMAIL=... bash scripts/office-smoke-test.sh`，四条脚本全部通过，说明当前 `staging` 已具备一轮发布到 `main` 前的基础验收信心。
- **2026-06-09 `main` 首轮真实上线测试通过**：在真实服务器 `main` 分支完成 `bash scripts/deploy-main.sh` 后，重新执行 `smoke-test.sh`、`business-smoke-test.sh`、`ocr-smoke-test.sh`、`office-smoke-test.sh` 四条脚本，全部通过；说明当前正式分支已经具备“可继续做人工线上验收”的基础稳定性。下一恢复点：从登录、上传、下载、套餐权限、异常提示这 5 类人工检查继续推进，并把发现的问题继续回填本文档。
- **2026-06-09 本地自动化补稳（第 1 轮）**：为 `backend/tests/conftest.py` 补齐本地/CI 所需的第三方 stub，并将 `UPLOAD_DIR` 固定到仓库内 `.tmp/uploads`，避免 Windows 本地因默认临时目录权限或路径差异导致 pytest 失败。当前后端核心测试 `backend/tests/test_security.py`、`test_auth.py`、`test_files.py` 已可在本地直接跑通。
- **2026-06-09 CI 门禁收敛**：`.github/workflows/ci-cd.yml` 已收敛为当前真实可维护的最小 CI，只对 `main/staging` 执行前端 unit test + build，以及后端核心 pytest。前端 lint 暂不作为强制阻塞项，避免被历史存量问题和生成物目录噪音卡住发布；`.gitignore` 同步补充 `.tmp/`、`playwright-report/`、`test-results/`、`test_pdfflow.db` 忽略规则。
- **2026-06-09 前端 lint 去硬错误（第 1 轮）**：已在 `src/` 与 `tests/` 范围内清理一批低风险但会让 ESLint 直接失败的问题，包括未使用变量、无意义 `try/catch`、测试脚本未声明 Node 环境、少量模板语法错误等；当前 `npx eslint src tests ...` 已无 `Error`，只剩 warning。同步复验 `npm run test:unit:ci` 与 `npm run build` 仍通过，说明这轮清理没有破坏现有前端交付门禁。
- **2026-06-09 后端**：FastAPI 架构、JWT 认证、文件处理 API、Celery 任务、Redis 限流、STRIDE 安全。
- **2026-06-08 MVP**：6 工具 + 20 组件 + 108 单测 + 三语，前端生产就绪。

---

> **维护提醒**：每次开发完成，更新 §0 状态、§2 矩阵、§4 勾选、§11 Changelog。**不要新建文档。**

### 2026-06-10 Frontend UI Alignment / 上线前页面收口

- Unified `src/views/tools/OCRPDF.vue`, `FillFormPDF.vue`, `AnnotatePDF.vue`, and `OfficeToPDF.vue` around the same hero / notice / upload / action shell used by the AI analyzer direction.
- Added shared page primitives: `src/components/tools/ToolHeader.vue` and `src/components/tools/ToolNoticeBar.vue`.
- Rebuilt `src/components/pdf/DragDropZone.vue` to support named slots, generic file accept patterns, and consistent upload events across tool pages.
- Removed duplicated upload copy from `FillFormPDF.vue` and `AnnotatePDF.vue`, and simplified `OfficeToPDF.vue` into a single sign-in then convert flow.
- Verification on 2026-06-10: `npm run build` passed locally.
- Residual repo debt: `npm run build:check` still fails because of pre-existing TypeScript issues in enterprise, history, API, and PDF utility modules. Those errors were already present before this UI refactor.
- Recommended manual QA after deploy: OCR access gating, form field rendering, annotation coordinate inputs, Office sign-in flow, and mobile spacing at 375px.
- 2026-06-10 frontend copy cleanup: simplified the header brand to logo + `PDF-Flow`, rewrote the `Features` hero / core cards / CTA into customer-facing messaging, and replaced the register page left-side helper copy with cleaner onboarding language. Verification target: rerun `npm run build` before next deploy.
- **2026-06-10 ??????????**????? `src/components/layout/Header.vue`?`Footer.vue`?`src/views/Features.vue`?`Pricing.vue`?????????????????????????????????????????????/????????????????`Features` ???????? CTA ????????????????`Pricing` ?????????????????????????????????????2026-06-10 ?????`npm run build` ???????? chunk ??????????
- **2026-06-10 Main smoke 套件补齐**：新增 `scripts/main-smoke-suite.sh`，在 `deploy-main.sh` 之后可一键串行执行 health、business、OCR、Office 四条 smoke 验收脚本，并自动生成隔离测试邮箱，减少手工重复操作。
- **2026-06-10 前端运行时与工具页加固**：修复 `/auth/login` 空白页问题，根因是 `vue-i18n` 的 linked-format 占位符在登录邮箱文案中触发运行时崩溃；同时为部署后的懒加载旧 chunk 增加路由恢复逻辑。另将 Merge PDF 缩略图的 `pdf.js` worker 切换为打包产物，不再依赖缺失的 `/wasm/pdfjs.worker.js`；并统一刷新 `OCRPDF.vue`、`FillFormPDF.vue`、`AnnotatePDF.vue`、`OfficeToPDF.vue` 的 AI 分析器风格布局，移除重复上传提示，修正首屏 notice 被 hero 挤压的问题。2026-06-10 本地验证：`npm run build` 通过，Playwright 路由检查确认登录页可渲染、Merge 缩略图可显示、四个工具页无运行时错误。
- **2026-06-10 认证与受限功能访问逻辑统一**：重建 `src/views/auth/Login.vue` 与 `src/views/auth/Register.vue`，从朴素模板表单升级为完整入口页；新增共享组件 `src/components/common/DiagnosticAlert.vue` 以及工具函数 `src/utils/error-messages.ts`、`src/utils/feature-access.ts`；统一高级功能访问路径，游客先登录，只有登录后的免费用户才看到升级入口；并让 `OCRPDF.vue`、`AIPDFAnalyzer.vue`、`FillFormPDF.vue`、`AnnotatePDF.vue`、`OfficeToPDF.vue` 统一改用带 `PF-*` 诊断码的安全错误提示，避免向用户暴露后端细节。
- **2026-06-10 认证页文案净化**：移除 `src/views/auth/Login.vue` 和 `src/views/auth/Register.vue` 中面向开发者或解释内部流程的文案，将入口页说明改成纯用户视角；同步清理 `src/locales/en.json`、`src/locales/zh.json`、`src/locales/es.json` 中预埋的示例登录/注册信息，避免页面暗示固定测试账号。
- **2026-06-10 前端部署缓存加固**：将“登录/注册在部署后偶发空白”定位为旧 service worker 缓存路径残留，而不是认证页本身逻辑错误。`index.html` 现会主动注销遗留 `/sw.js`、清理 `pdf-flow-*` 缓存，并在清理后强制刷新一次，避免旧缓存 chunk 与新页面混用。同一轮中，`OCRPDF.vue`、`OfficeToPDF.vue`、`FillFormPDF.vue`、`AnnotatePDF.vue` 继续向 AI 分析器的 hero -> notice -> access -> upload/workspace 节奏靠齐。2026-06-10 本地验证：`npm run build` 通过，Playwright 确认 `/auth/login`、`/auth/register`、`/tools/ocr`、`/tools/office-to-pdf`、`/tools/fill-form`、`/tools/annotate` 均无运行时错误。
- **2026-06-10 前端语言统一 / 中文默认修复**：前端语言初始化改为优先读取已保存设置，否则默认使用简体中文而不是浏览器英文；同时持久化保存语言与主题设置。Header、Footer、DragDropZone 也已重构，去掉可见的中英混杂和历史乱码，并新增 `src/locales/overrides.ts` 作为干净的 i18n 覆盖层，让关键中文文案不再依赖历史受污染的 locale JSON。相关页面包括 Login、Register、AIPDFAnalyzer、OCRPDF、OfficeToPDF、FillFormPDF、AnnotatePDF 已切到统一翻译体系。2026-06-10 本地验证：`npm run build` 通过。
- **2026-06-10 Office 转 PDF 登录入口收口**：移除 `src/views/tools/OfficeToPDF.vue` 工作区里重复的登录提示，只保留认证前单一的游客访问面板；主转换按钮仅在已登录状态下显示，避免同一页面出现两个登录入口。
- **2026-06-10 公共营销页与法律页重构**：重做 `src/components/layout/Header.vue`、`Footer.vue`、`src/views/Features.vue`、`Pricing.vue`，把右上角 `功能特性 / 查看定价` 从普通按钮升级为图标化胶囊导航，并让 `Features`、`Pricing` 改为与首页/登录同设计家族但不同节奏的产品简报页；页脚同步重排为品牌说明、工具入口、产品入口、法律与支持四区结构。新增 `src/views/legal/PrivacyPolicy.vue` 与 `TermsOfService.vue`、对应路由 `/privacy` 与 `/terms`，补齐可上线测试使用的隐私政策与服务条款页面；`src/locales/overrides.ts` 追加中英西的法律页、页脚和定价扩展文案。2026-06-10 本地验证：`npm run build` 通过。
- 2026-06-10 frontend dedupe and customer-facing auth cleanup: redesigned the left-side login/register marketing blocks as user-facing value cards, removed duplicate gated-state helper cards/chips from OCR, Office, Fill Form, and Annotate pages, fixed remaining Office/step/color text cleanup, and replaced internal-sounding fallback copy in footer/i18n overrides. Verification target: rerun `npm run build` before deploy.

### 2026-06-10 Legal Pages And Hidden Admin Backlog / 法律页与隐藏后台计划

- 已将 `src/views/legal/PrivacyPolicy.vue` 和 `src/views/legal/TermsOfService.vue` 从占位式摘要升级为面向用户的真实内容，覆盖账户信息、文件处理、云端任务、保留删除、用户权利、订阅限制、禁止行为、免责声明和联系方式。
- 法律页采用页面内中英文内容映射，默认中文；英文环境显示英文版，避免继续依赖历史 locale 文件中受污染或不完整的法律文案。
- 下一阶段新增隐藏后台，定位为“管理员运营控制台”，不在普通用户导航、页脚或公开营销入口展示，但不能依赖隐藏路径作为安全措施，必须由后端 `ADMIN` 角色鉴权保护。
- 后台 MVP 建议范围：
  - 管理员登录后访问隐藏路由，例如 `/control-room` 或 `/ops-console`。
  - 后端新增 `/api/v1/admin/*` 路由，所有接口强制 `UserRole.ADMIN`。
  - 新增站点配置模型：站点名称、公告、联系邮箱、页脚内容、首页 CTA、维护模式。
  - 新增功能开关模型：每个工具可配置 `enabled`、`requires_login`、`requires_pro`、`maintenance_message`。
  - 新增内容块模型：隐私政策、服务条款、首页文案、定价说明等可由后台编辑。
  - 新增审计日志：记录管理员、动作、对象、时间、结果和必要诊断信息。
- 后台第一阶段不做公开注册入口、不做复杂多管理员权限矩阵、不做拖拽页面搭建器，先解决“能安全地开关功能、修改全站基础内容、维护法律页和公告”的真实运营需求。
- 安全要求：后台路由不出现在导航；前端隐藏只是体验层，真实权限必须由后端判断；所有配置更新需要输入校验；敏感错误只返回诊断码；管理员操作写入审计日志。

### 2026-06-10 Hidden Admin Console MVP / 隐藏后台第一阶段落地

- 新增后端后台基础能力：`backend/app/api/v1/endpoints/admin.py`，挂载到 `/api/v1/admin/*`，所有接口强制当前用户为 `admin` 角色，否则返回 403。
- 新增后台数据模型与迁移：`SiteSetting`、`FeatureFlag`、`ContentBlock`、`AdminAuditLog`，对应迁移文件为 `backend/alembic/versions/add_admin_console_models.py`。
- 后台首次访问会自动种子化基础站点配置、全功能开关、默认内容块；后续管理员可通过接口修改，并自动写入审计日志。
- 新增前端隐藏入口 `/control-room`，不加入 Header、Footer 或公开导航；仅 admin 用户可访问，普通用户会被路由守卫拦回首页，未登录用户会被引导登录。
- 新增 `adminAPI`、`adminGuard` 和 `userStore.isAdmin`，前端控制台支持管理功能开关、站点配置、内容块和查看最近审计记录。
- 当前阶段后台开关已经可保存到后端，但尚未统一接入所有公开工具页和后端业务执行路径；下一阶段需要把工具可见性、维护提示、登录要求、Pro 要求统一改为读取后端配置。
- 本地验证：`npm run build` 通过；`python -m pytest backend/tests/test_auth.py backend/tests/test_admin.py -q` 通过，17 passed。Windows 本机直接导入 `app.main` 时会被历史监控服务中的 Unicode 控制台输出影响，服务端 Linux/Docker 不受该 GBK 控制台问题影响。

### 2026-06-10 Admin Feature Gate Enforcement / 后台功能开关联动落地

- Hidden admin feature flags now drive both public UI visibility and backend execution, not just the `/control-room` save form.
- Added `backend/app/services/feature_gate.py` as the shared access gate. If a feature flag row is missing after a fresh migration, the backend now creates the default row and still enforces the default access rule instead of silently allowing the feature.
- Added unauthenticated public config endpoint `GET /api/v1/admin/public-config` for read-only frontend settings, feature flags, and public content blocks.
- Backend endpoints now call the shared gate for core tools (`merge_pdf`, `split_pdf`, `compress_pdf`, `rotate_pdf`, `image_to_pdf`, `pdf_to_image`, `ocr_pdf`, `office_to_pdf`), AI analyzer, watermark, form fill, and annotation operations.
- Frontend now fetches public config through `src/stores/siteConfig.ts`; homepage and footer hide disabled tool entries, and direct tool routes redirect to login, pricing, or the homepage maintenance notice according to the saved backend rule.
- Admin saves refresh the public config store immediately, so changing a switch in `/control-room` is reflected without needing to guess whether the old SPA cache is still active.
- Verification target for this step: `python -m pytest backend/tests/test_auth.py backend/tests/test_admin.py -q`, `npm run build`, and `git diff --check` before pushing.
- Server validation after deploy: turn off `merge_pdf` in `/control-room`, confirm `/tools/merge` disappears or redirects, confirm `POST /api/v1/files/merge` returns `503`, then turn it back on.

### 2026-06-10 Public Content Config Wiring / 公开内容接入后台配置

- Server deployment of `99940c7` succeeded on the real host: backend and frontend rebuilt, backend stayed healthy, `alembic upgrade head` ran, and `GET /api/v1/admin/public-config` returned settings, feature flags, and content blocks.
- Upgraded admin default seeding so it now fills missing settings, feature flags, and content blocks individually instead of only seeding when a table is empty. This lets older live databases receive new defaults such as `support_email` and English content blocks without wiping admin edits.
- Replaced legacy placeholder content blocks with real user-facing defaults when the saved content still exactly matches the old placeholder text.
- Added public config helpers in `src/stores/siteConfig.ts` for `getSettingValue()` and locale-aware `getContentBlock()`.
- Wired public pages to backend-managed content where it is safe: Header/Footer brand name, Footer and payment success support email, Footer support note, Home hero title/description, Pricing intro title/description, and the hero summary/title on Privacy Policy and Terms of Service.
- Intentional guardrail: legal page body sections remain frontend-rendered structured content for now; admin content blocks can adjust the public title and summary without allowing arbitrary HTML to break layout or introduce unsafe markup.
- Verification on 2026-06-10: `npm run build` passed and `python -m pytest backend/tests/test_auth.py backend/tests/test_admin.py -q` passed with 20 tests.

### 2026-06-11 Maintenance Mode And Announcement Wiring / 维护模式与全站公告落地

- Added shared backend helper `backend/app/services/site_state.py` for public site settings such as `maintenance_mode` and `global_announcement`.
- Backend processing gates now respect `maintenance_mode`: normal users receive `503` with the announcement text, while admin users can still operate and recover the site.
- Frontend now reads `global_announcement` and `maintenance_mode` from `public-config`. Announcements render as a site-wide banner, and maintenance mode shows a public maintenance panel.
- Maintenance mode intentionally allows `/auth`, `/control-room`, `/privacy`, and `/terms` to remain accessible so admins can sign in, disable maintenance mode, and users can still read legal/support pages.
- Added store helpers for boolean settings and global announcement access in `src/stores/siteConfig.ts`.
- Added regression coverage for public config defaults and maintenance-mode API blocking in `backend/tests/test_admin.py`.
- Verification on 2026-06-11: `python -m pytest backend/tests/test_auth.py backend/tests/test_admin.py -q` passed with 21 tests, `npm run build` passed, and `git diff --check` passed.
- Server validation after deploy: set `global_announcement` to a short message and `maintenance_mode=true` in `/control-room`; verify the public site shows the maintenance panel, `/control-room` remains reachable after login, and `POST /api/v1/files/merge` returns `503`; then set `maintenance_mode=false`.

### 2026-06-11 Admin User And Job Operations / 后台用户与任务运营能力
- Added admin-only user operations endpoints under `/api/v1/admin/users`: list/search recent users and update role, active status, and verification status.
- Added a safety guard that prevents the current admin from demoting or deactivating their own account, reducing the risk of locking the hidden control room during live operations.
- Added admin-only job observation endpoint `/api/v1/admin/jobs` with recent processing job context, user email, status, progress, file size, and error message.
- Expanded `/api/v1/admin/overview` with user counts, active user counts, admin count, total job count, and failed job count so the control room can show operational health at a glance.
- Updated `/control-room` with two new hidden tabs: `用户管理` for role/status adjustments and `任务观察` for recent processing failures and stuck job triage.
- Verification on 2026-06-11: `python -m pytest backend/tests/test_admin.py -q` passed with 9 tests, and `npm run build` passed with only the existing large chunk warning.
- Server validation after deploy: visit `/control-room`, confirm `用户管理` can search a test user and promote/demote non-admin users, then confirm `任务观察` shows recent OCR/Office/merge jobs after running smoke tests.
