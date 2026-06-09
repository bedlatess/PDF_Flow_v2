# 📄 PDF-Flow

> 🔒 隐私优先的在线 PDF 工具集 | Privacy-First PDF Tools

[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()
[![Vue](https://img.shields.io/badge/Vue-3.4.21-green.svg)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4.2-blue.svg)](https://www.typescriptlang.org/)
[![Tests](https://img.shields.io/badge/tests-108%20passed-success.svg)]()

**PDF-Flow** 是一个现代化的在线 PDF 工具集，所有处理完全在浏览器本地进行，确保您的文件隐私和安全。

[🚀 在线演示](https://pdf-flow.vercel.app) | [📖 文档](./docs) | [🐛 问题反馈](https://github.com/bedlatess/PDF_Flow/issues)

---

## ✨ 功能特性

### 🛠️ 核心工具

| 工具 | 功能描述 | 状态 |
|------|---------|------|
| **合并 PDF** | 将多个 PDF 合并为一个，支持拖拽排序 | ✅ |
| **拆分 PDF** | 从 PDF 中提取指定页面，支持可视化选择 | ✅ |
| **旋转 PDF** | 旋转 PDF 页面（90°/180°/270°） | ✅ |
| **压缩 PDF** | 减小 PDF 文件大小，三种质量级别 | ✅ |
| **图片转 PDF** | 将多张图片转换为 PDF | ✅ |
| **PDF 转图片** | 将 PDF 页面导出为图片（PNG/JPEG） | ✅ |
| **OCR 文字识别** | 从 PDF/图片中提取文字，支持10种语言 | ✅ |
| **Office 转 PDF** | Word/Excel/PowerPoint 转 PDF | ✅ |
| **添加水印** | 为 PDF 添加文字水印（本地/云端） | ✅ |
| **填写表单** | 自动填写 PDF 表单字段 | ✅ |
| **PDF 注释** | 添加文本注释和高亮标记 | ✅ |

### 🔒 隐私保护

- ✅ **100% 本地处理** - 文件不上传到服务器
- ✅ **无数据收集** - 不追踪用户行为
- ✅ **自动清理** - 处理完成后自动释放内存
- ✅ **GDPR 合规** - 符合隐私保护要求

### ⚡ 性能优化

- ✅ **Web Workers** - 后台多线程处理，UI 不阻塞
- ✅ **懒加载** - 按需加载 PDF 处理库
- ✅ **代码分割** - 路由级别代码分割
- ✅ **内存管理** - 自动释放 Blob URLs，防止内存泄漏

### 🎨 用户体验

- ✅ **拖拽上传** - 直观的文件操作
- ✅ **实时预览** - 内置 PDF 查看器
- ✅ **进度显示** - 实时处理进度反馈
- ✅ **响应式设计** - 完美适配移动端和桌面端
- ✅ **多语言** - 支持英语、中文、西班牙语

---

## 🚀 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:5173

### 生产构建

```bash
npm run build
npm run preview
```

### 运行测试

```bash
# 单元测试
npm run test:unit

# E2E 测试
npm run test:e2e

# 代码检查
npm run lint
npm run format
```

---

## 📦 技术栈

### 核心框架
- **Vue 3.4.21** - 渐进式 JavaScript 框架
- **TypeScript 5.4.2** - 类型安全
- **Vite 5.1.6** - 现代化构建工具

### PDF 处理
- **pdf-lib** - PDF 创建和修改
- **pdfjs-dist** - PDF 解析和渲染
- **jspdf** - PDF 生成

### UI 框架
- **TailwindCSS** - 原子化 CSS
- **Radix Vue** - 无样式 UI 组件
- **Lucide Icons** - 图标库

### 状态管理
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Vue I18n** - 国际化

---

## 📁 项目结构

```
PDF_Flow/
├── src/
│   ├── components/          # Vue 组件
│   │   ├── common/          # 通用组件
│   │   ├── layout/          # 布局组件
│   │   └── pdf/             # PDF 专用组件
│   ├── views/               # 页面视图
│   │   ├── Home.vue         # 首页
│   │   └── tools/           # 工具页面
│   ├── utils/               # 工具函数
│   │   └── pdf/             # PDF 处理核心
│   ├── composables/         # 组合式函数
│   ├── stores/              # Pinia stores
│   ├── locales/             # 国际化文件
│   ├── workers/             # Web Workers
│   └── router/              # 路由配置
├── tests/
│   ├── unit/                # 单元测试
│   ├── e2e-playwright/      # E2E 测试
│   └── helpers/             # 测试辅助函数
└── docs/                    # 文档
```

---

## 🧪 测试

### 单元测试覆盖

✅ **108/108 测试通过**

- Button, Card, Modal 等通用组件
- DragDropZone, FilePreview 等 PDF 组件
- 文件验证、内存管理等工具函数
- PDF 处理核心功能

### E2E 测试

- 首页加载和导航
- 工具页面功能测试
- 文件上传和处理流程
- 响应式设计验证

---

## 📖 文档

> 本项目只有**一份**开发文档，所有状态、计划、规范、指南都在其中。

- **[docs/PROJECT_MASTER.md](./docs/PROJECT_MASTER.md)** — 📘 唯一开发主文档（Single Source of Truth）
- **[开发文档/](./开发文档/)** — 📋 原始需求规格 v1.0–v4.0（只读源材料）
- **[backend/README.md](./backend/README.md)** — ⚙️ 后端运行说明

> ⚠️ 开发完成后只更新 `PROJECT_MASTER.md`，不要新建报告类文档。

---

## 🌐 部署

### 推荐平台

#### Vercel（推荐）
```bash
npm i -g vercel
vercel
```

#### Netlify
```bash
npm run build
netlify deploy --prod --dir=dist
```

#### Cloudflare Pages
连接 Git 仓库，设置：
- 构建命令: `npm run build`
- 输出目录: `dist`

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

### 开发流程

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

```bash
# 代码检查
npm run lint

# 代码格式化
npm run format

# 运行测试
npm run test:unit
```

---

## 📊 项目状态

### ✅ 已完成
- [x] 8 大核心工具（6个基础工具 + OCR + Office转换）
- [x] 3 个高级工具（水印 + 表单填写 + 注释）
- [x] 20+ 个 UI 组件
- [x] 108 个单元测试
- [x] 3 种语言支持（英语/中文/西班牙语）
- [x] Web Workers 集成
- [x] 响应式设计
- [x] 生产构建优化
- [x] 用户认证系统（JWT + OAuth）
- [x] 云端处理集成
- [x] WebSocket 实时进度
- [x] Pricing 定价页面
- [x] AI PDF 分析器（Gemini）
- [x] 企业控制台（API Keys/统计/Webhooks/计费）

### 🚧 进行中
- [ ] E2E 测试优化
- [ ] 性能持续优化
- [ ] OAuth/Office 真实环境测试

### 📋 计划中
- [ ] Stripe 支付真实测试
- [ ] OAuth 真实凭据测试
- [ ] 云端 OCR 真实环境验证
- [ ] 邮件系统真实测试
- [ ] 后端 Docker 环境联调
- [ ] 生产环境部署

---

## 📝 许可证

MIT License - 详见 [LICENSE](./LICENSE) 文件

---

## 🙏 致谢

### 核心依赖

- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [pdf-lib](https://pdf-lib.js.org/) - PDF 操作库
- [PDF.js](https://mozilla.github.io/pdf.js/) - PDF 渲染引擎
- [TailwindCSS](https://tailwindcss.com/) - CSS 框架

### 灵感来源

- [iLovePDF](https://www.ilovepdf.com/)
- [Smallpdf](https://smallpdf.com/)
- [PDF24](https://tools.pdf24.org/)

---

## 📞 联系方式

- **项目主页**: [GitHub Repository](https://github.com/bedlatess/PDF_Flow)
- **问题反馈**: [Issues](https://github.com/bedlatess/PDF_Flow/issues)
- **功能建议**: [Discussions](https://github.com/bedlatess/PDF_Flow/discussions)

---

## 🌟 Star History

如果这个项目对您有帮助，请给我们一个 ⭐️！

---

## 📈 统计数据

![GitHub stars](https://img.shields.io/github/stars/bedlatess/PDF_Flow?style=social)
![GitHub forks](https://img.shields.io/github/forks/bedlatess/PDF_Flow?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/bedlatess/PDF_Flow?style=social)

---

<div align="center">

**使用 ❤️ 和 Vue 3 构建**

[⬆ 回到顶部](#-pdf-flow)

</div>
