# PDF-Flow 单服务器部署指南

> 适用场景：
> - 本地不安装 Docker
> - 只有 1 台服务器
> - 服务器用于真实环境测试
> - 代码先在 `staging` 验收，再按需切到 `main` 做上线测试

---

## 1. 目标

这套流程解决 4 个问题：

1. 本地改完代码后，如何稳定推到服务器测试
2. 服务器如何在 `staging` 与 `main` 之间安全切换，而不丢失回滚能力
3. 部署失败后如何快速回滚
4. 每次改完流程后，如何保证文档同步，避免重复踩坑

---

## 2. 分支规则

- `main`
  - 正式稳定分支
  - 只接收已经在服务器上验证通过的代码

- `staging`
  - 服务器真实测试分支
  - 服务器固定部署这个分支

规则：

1. 日常开发先合入 `staging`
2. 服务器只拉取并部署 `staging`
3. 服务器测试通过后，再把 `staging` 合并到 `main`

### 当前建议

- `staging`：继续作为开发完成后的首轮真实验收分支
- `main`：现在已经可以承接真实上线测试
- 如果这次目标是“直接按正式分支做线上验证”，优先在服务器执行 `main` 包装脚本，而不是手工拼 `DEPLOY_BRANCH=main`

---

## 3. 服务器首次部署 Checklist

### 3.1 服务器基础环境

确认服务器已安装：

```bash
git --version
docker --version
docker compose version
curl --version
```

如果服务器使用的是旧版 compose，也可以是：

```bash
docker-compose --version
```

### 3.2 克隆项目

```bash
git clone <your-repo-url> pdf-flow
cd pdf-flow
```

### 3.3 切到 `staging`

如果远端已经有 `staging`：

```bash
git fetch origin
git checkout -b staging origin/staging
```

如果远端还没有 `staging`，先在本地创建并推送，见第 5 节。

### 3.4 配置环境文件

服务器本地维护，不要提交到仓库：

```bash
cp backend/.env.example backend/.env
```

按需填写：

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `STRIPE_*`
- `GOOGLE_*`
- `GITHUB_*`
- `RESEND_API_KEY`
- `GEMINI_API_KEY`
- `SENTRY_DSN`
- `POSTHOG_API_KEY`

如果根目录也有本地环境文件需求，再额外维护根目录 `.env`。

### 3.5 赋予脚本执行权限

```bash
chmod +x scripts/deploy-staging.sh
chmod +x scripts/rollback-staging.sh
chmod +x scripts/deploy-main.sh
chmod +x scripts/rollback-main.sh
chmod +x scripts/smoke-test.sh
chmod +x scripts/business-smoke-test.sh
chmod +x scripts/ocr-smoke-test.sh
chmod +x scripts/office-smoke-test.sh
```

### 3.6 首次部署

```bash
bash scripts/deploy-staging.sh
```

默认会执行：

1. 备份当前 commit 和环境文件
2. 拉取远端 `staging`
3. `docker compose up -d --build`
4. `alembic upgrade head`
5. 冒烟检查 `/health` 和 `/api/docs`

---

## 4. 日常部署 Checklist

每次服务器测试都按这个顺序执行。

### 4.1 本地

先做本地可做的验证：

```bash
npm run build
npm run test:unit
```

如果后端改动较大，再补：

```bash
cd backend
python -m pytest tests/ -q
```

### 4.2 提交到 `staging`

```bash
git checkout staging
git pull --ff-only origin staging
git add .
git commit -m "feat: xxx"
git push origin staging
```

### 4.3 服务器部署

```bash
cd /path/to/pdf-flow
bash scripts/deploy-staging.sh
```

如果当前服务器已经切到 `main` 做真实上线测试，改用：

```bash
cd /path/to/pdf-flow
bash scripts/deploy-main.sh
```

### 4.4 冒烟测试

至少验证：

1. `GET /health`
2. `GET /api/docs`
3. 上传 PDF -> 合并 -> 下载
4. OCR
5. Office 转 PDF

推荐按两层执行：

```bash
bash scripts/smoke-test.sh
bash scripts/business-smoke-test.sh
```

说明：

- `smoke-test.sh` 只检查基础可达性，适合部署后快速确认服务是否活着
- `business-smoke-test.sh` 会复用仓库里的 `tests/fixtures/sample1.pdf` 和 `tests/fixtures/sample2.pdf`
- 业务脚本会自动执行：注册测试账号 -> 登录 -> 上传两个 PDF -> 发起合并 -> 轮询任务 -> 下载结果
- 默认测试账号为 `smoke@example.com`，重复执行可复用；如需隔离可临时覆盖：

```bash
BUSINESS_SMOKE_EMAIL="smoke-$(date +%s)@example.com" bash scripts/business-smoke-test.sh
```

如果只是改了 Python 代码，优先走快速反馈链路，避免每次都整套重建：

```bash
git pull --ff-only origin staging
docker compose restart backend
docker compose exec backend python -c "import app.main; print('app import ok')"
bash scripts/smoke-test.sh
```

如果要做上线前的三条核心业务验收，按这个顺序跑：

```bash
BUSINESS_SMOKE_EMAIL="smoke-$(date +%s)@example.com" bash scripts/business-smoke-test.sh
OCR_SMOKE_EMAIL="ocr-$(date +%s)@example.com" bash scripts/ocr-smoke-test.sh
OFFICE_SMOKE_EMAIL="office-$(date +%s)@example.com" bash scripts/office-smoke-test.sh
```

说明：

- `ocr-smoke-test.sh` 会自动把测试用户提升为 `pro`，生成一张带文字的 PNG，走 上传 -> OCR -> 下载文本 的真实链路
- `office-smoke-test.sh` 会自动生成一个最小 DOCX，走 Office -> PDF -> 下载结果 的真实链路
- 这两条脚本都会自己等待服务就绪，不需要额外先手工跑健康检查
- 两条脚本现在改为在 `backend` 容器内生成样本，再通过 `docker cp` 拷回宿主机上传，避免二进制文件经过终端管道输出时损坏
- 如果 OCR 上传或 Office 提交返回 `400/401/403/500`，脚本会直接打印后端响应体，便于第一时间定位是业务校验失败还是环境问题

如果这次改动涉及认证、支付、AI，再额外测：

- 登录 / 注册 / OAuth
- Stripe
- Resend
- Gemini

### 4.5 `main` 上线测试基线

截至 2026-06-09，以下四条脚本已经在真实服务器 Docker 环境连续通过，可作为本轮 `main` 上线测试的最小发布门禁：

```bash
bash scripts/smoke-test.sh
BUSINESS_SMOKE_EMAIL="smoke-$(date +%s)@example.com" bash scripts/business-smoke-test.sh
OCR_SMOKE_EMAIL="ocr-$(date +%s)@example.com" bash scripts/ocr-smoke-test.sh
OFFICE_SMOKE_EMAIL="office-$(date +%s)@example.com" bash scripts/office-smoke-test.sh
```

推荐真实上线测试顺序：

1. `git push origin main`
2. 服务器执行 `git pull --ff-only origin main`
3. 服务器执行 `bash scripts/deploy-main.sh`
4. 依次跑 4 条 smoke 脚本
5. 再做人工页面验证：登录、上传、下载、套餐拦截、异常提示

当前状态：

- 截至 2026-06-09，`main` 分支已在真实服务器完成一轮重新部署
- `smoke-test.sh`、`business-smoke-test.sh`、`ocr-smoke-test.sh`、`office-smoke-test.sh` 已在 `main` 上连续通过
- 下一步不再是补脚本，而是做人工线上验收并记录问题清单

推荐人工线上验收最小清单：

1. 注册新用户并登录，确认注册、登录、退出都正常
2. 以普通用户上传 2 个 PDF 做一次合并，确认结果可下载
3. 验证 OCR 页面与 Office 转 PDF 页面能正常提交、查看结果、下载结果
4. 检查 Pro/Enterprise 限制是否按预期提示，而不是无响应或 500
5. 人工触发 1 次异常输入，确认前端错误提示和后端返回信息可理解
### 4.6 通过后合并到 `main`

当前已在真实服务器验证通过的最小发布门禁：

```bash
bash scripts/smoke-test.sh
BUSINESS_SMOKE_EMAIL="smoke-$(date +%s)@example.com" bash scripts/business-smoke-test.sh
OCR_SMOKE_EMAIL="ocr-$(date +%s)@example.com" bash scripts/ocr-smoke-test.sh
OFFICE_SMOKE_EMAIL="office-$(date +%s)@example.com" bash scripts/office-smoke-test.sh
```

本地执行：

```bash
git checkout main
git pull --ff-only origin main
git merge --ff-only staging
git push origin main
```

---

## 5. 首次创建 `staging` 分支

如果仓库里还没有 `staging`，本地执行一次：

```bash
git checkout main
git pull --ff-only origin main
git checkout -b staging
git push -u origin staging
```

之后本地和服务器都基于 `staging` 工作。

---

## 6. 回滚流程

如果部署失败或服务异常：

```bash
bash scripts/rollback-staging.sh
```

如果当前部署的是 `main`，改用：

```bash
bash scripts/rollback-main.sh
```

这个脚本会：

1. 回到上一次成功部署记录的 commit
2. 重建容器
3. 再次执行冒烟检查

注意：

- 这是“代码和容器版本回滚”
- 数据库不会自动回滚
- 如果本次迁移不向后兼容，你必须额外准备数据库备份恢复方案

---

## 7. 可选数据库备份

如果你希望每次部署前自动导出数据库，可以这样执行：

```bash
DEPLOY_BACKUP_COMMAND='docker compose exec -T postgres pg_dump -U pdfflow_user pdfflow > "$BACKUP_PATH/postgres.sql"' \
bash scripts/deploy-staging.sh
```

如果你的数据库服务名、用户名、库名不同，请替换成服务器上的实际值。

---

## 8. 推荐命令清单

### 本地开发到测试

```bash
git checkout staging
git pull --ff-only origin staging
git add .
git commit -m "feat: xxx"
git push origin staging
```

### 服务器真实测试

```bash
cd /path/to/pdf-flow
bash scripts/deploy-staging.sh
```

### 服务器 `main` 上线测试

```bash
git checkout main
git pull --ff-only origin main
bash scripts/deploy-main.sh
```

### 服务器回滚

```bash
bash scripts/rollback-staging.sh
```

### 服务器 `main` 回滚

```bash
bash scripts/rollback-main.sh
```

### 测试通过后进正式分支

```bash
git checkout main
git pull --ff-only origin main
git merge --ff-only staging
git push origin main
```

---

## 9. 文档同步规则

每次遇到以下情况，必须同步更新文档：

- 部署脚本行为变化
- 备份或回滚机制变化
- 服务器部署命令变化
- 分支策略变化
- Docker / compose / 环境变量要求变化

优先更新：

- [PROJECT_MASTER.md](./PROJECT_MASTER.md)
- 本文档 `STAGING_DEPLOY_GUIDE.md`

不要再新增阶段总结、完成报告、简报类文档。

---

## 10. 当前最适合你的实际工作流

一句话版：

**本地开发 -> 推 `staging` -> 服务器验收 -> 合并 `main` -> 服务器跑 `deploy-main.sh` 做真实上线测试**

这是当前“只有 1 台服务器、但又要有容错和回滚”的最稳妥方案。
