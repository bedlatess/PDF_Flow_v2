<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Clock3,
  Database,
  FileLock2,
  Mail,
  ServerCog,
  ShieldCheck,
  Sparkles,
  Trash2,
  UserCheck,
} from 'lucide-vue-next'

type LegalSection = {
  icon: unknown
  title: string
  paragraphs: string[]
  bullets?: string[]
}

const { locale } = useI18n()

const content = {
  zh: {
    eyebrow: '隐私政策',
    title: '我们如何保护你的文件与账户信息',
    updated: '最后更新：2026 年 6 月 10 日',
    description:
      'PDF-Flow 是一个面向日常文档处理的在线 PDF 工具。我们尽量让基础 PDF 操作在浏览器本地完成；确实需要云端能力的功能，例如 OCR、Office 转 PDF、AI 分析等，会在必要范围内处理上传文件。',
    summaryTitle: '简短说明',
    summary:
      '我们不会出售你的个人信息，也不会为了广告画像而读取你的文件内容。上传到云端处理的文件仅用于完成你主动发起的任务、排查故障和保障服务安全，并会尽量缩短保留时间。',
    note:
      '本政策用于说明 PDF-Flow 当前的数据处理方式。若未来上线更完整的企业、支付或后台管理能力，我们会同步更新本页面。',
    sections: [
      {
        icon: Database,
        title: '1. 我们收集的信息',
        paragraphs: [
          '当你访问网站时，我们可能会接收基础访问数据，例如浏览器类型、访问时间、页面路径、语言设置和必要的安全日志。这些信息主要用于让网站稳定运行、排查异常访问和改进体验。',
          '当你注册或登录账户时，我们会保存邮箱、昵称或显示名称、加密后的密码、账户角色、订阅状态、登录时间等必要信息。我们不会保存你的明文密码。',
        ],
        bullets: [
          '账户信息：邮箱、显示名称、认证状态、角色权限。',
          '运行信息：任务状态、错误代码、必要诊断日志。',
          '支付信息：如启用订阅，将由支付服务商处理付款细节，PDF-Flow 仅保存必要的订阅状态。',
        ],
      },
      {
        icon: FileLock2,
        title: '2. 文件如何被处理',
        paragraphs: [
          '合并、拆分、旋转、压缩、图片转 PDF、PDF 转图片等基础工具会优先在浏览器本地处理，通常不需要把文件上传到服务器。',
          'OCR 文字识别、Office 转 PDF、AI PDF 分析、部分高级表单或标注能力需要服务端参与。你主动提交这些任务时，相关文件会被上传并在服务器上临时处理。',
        ],
        bullets: [
          '我们只会为完成你选择的功能处理文件。',
          '我们不会主动公开、出售或用于广告训练你的文件内容。',
          '重要文件建议你自行保留原件和处理后结果。',
        ],
      },
      {
        icon: ServerCog,
        title: '3. 我们如何使用信息',
        paragraphs: [
          '我们使用必要信息来提供账户登录、文件处理、任务进度、下载结果、权限控制、订阅识别、异常排查和安全防护。',
          '如果你向管理员或支持渠道反馈问题，我们可能会根据你提供的截图、时间点、错误编号和操作步骤定位问题。请不要在反馈中主动发送不必要的敏感文件。',
        ],
        bullets: [
          '保持登录状态与账户安全。',
          '判断某项功能是否可用或是否需要登录。',
          '定位任务失败、上传失败、下载失败等问题。',
        ],
      },
      {
        icon: Trash2,
        title: '4. 文件保留与删除',
        paragraphs: [
          '临时上传文件、转换结果和任务缓存通常只在处理、下载或排障所需的合理时间内保留。我们会尽量通过自动清理策略减少残留。',
          '由于队列任务、备份、日志轮转或系统异常的存在，我们不能承诺所有临时数据都会在任务完成瞬间立即删除，但会尽量限制保留范围和保留时间。',
        ],
      },
      {
        icon: UserCheck,
        title: '5. 你的选择与权利',
        paragraphs: [
          '你可以选择不注册账户而使用部分基础功能。对于需要云端处理、登录或订阅的功能，你可以自行决定是否继续使用。',
          '你可以请求查看、更正或删除账户相关信息。某些安全、支付、审计或故障排查记录可能需要按照合理期限继续保留。',
        ],
      },
      {
        icon: ShieldCheck,
        title: '6. 安全措施',
        paragraphs: [
          '我们采用加密密码存储、基于令牌的登录、权限分级、基础安全日志、容器化部署和最小必要访问原则来降低风险。',
          '任何在线服务都无法保证绝对安全。如果你处理高度敏感、受监管或具有法律效力的文件，请在上传前自行评估风险。',
        ],
      },
      {
        icon: Clock3,
        title: '7. 政策更新',
        paragraphs: [
          '随着后台管理、支付、团队协作、企业 API 或更多云端功能上线，本政策可能会更新。重要变化会尽量通过页面提示、版本记录或站内说明告知。',
        ],
      },
      {
        icon: Mail,
        title: '8. 联系我们',
        paragraphs: [
          '如果你对隐私、文件处理或账户数据有疑问，请通过网站展示的支持渠道联系管理员。反馈问题时，建议提供页面截图、时间点、错误编号和简短复现步骤。',
        ],
      },
    ] satisfies LegalSection[],
  },
  en: {
    eyebrow: 'Privacy Policy',
    title: 'How we protect your files and account information',
    updated: 'Last updated: June 10, 2026',
    description:
      'PDF-Flow is an online PDF workspace for everyday document tasks. We try to keep core PDF operations in your browser. Features that require cloud processing, such as OCR, Office to PDF, and AI analysis, process uploaded files only when needed.',
    summaryTitle: 'Short version',
    summary:
      'We do not sell your personal information or read your documents for advertising profiles. Files uploaded for cloud processing are used to complete the task you requested, troubleshoot issues, and protect service security, with retention kept as short as practical.',
    note:
      'This policy describes the current PDF-Flow service. As admin, billing, enterprise, or content-management features expand, this page will be updated.',
    sections: [
      {
        icon: Database,
        title: '1. Information we collect',
        paragraphs: [
          'When you visit the site, we may receive basic access data such as browser type, visit time, page path, language setting, and necessary security logs.',
          'When you create or use an account, we store information needed to operate the service, including email, display name, hashed password, account role, subscription status, and login timestamps.',
        ],
        bullets: [
          'Account data: email, display name, authentication status, role.',
          'Operational data: task status, error codes, essential diagnostics.',
          'Billing status: if subscriptions are enabled, payment details are handled by the payment provider.',
        ],
      },
      {
        icon: FileLock2,
        title: '2. How files are processed',
        paragraphs: [
          'Basic tools such as merge, split, rotate, compress, image to PDF, and PDF to image are designed to run locally in the browser whenever possible.',
          'OCR, Office to PDF, AI PDF analysis, and some advanced form or annotation workflows require backend processing. When you submit these tasks, related files are uploaded temporarily.',
        ],
        bullets: [
          'Files are processed only to provide the feature you selected.',
          'We do not sell, publish, or use your file contents for advertising training.',
          'Please keep your own originals and final copies for important documents.',
        ],
      },
      {
        icon: ServerCog,
        title: '3. How information is used',
        paragraphs: [
          'We use necessary information to provide login, file processing, task progress, downloads, permission checks, subscription recognition, troubleshooting, and security protection.',
          'If you contact support, we may use the screenshot, timestamp, error code, and steps you provide to locate the issue. Please avoid sending unnecessary sensitive files.',
        ],
      },
      {
        icon: Trash2,
        title: '4. Retention and deletion',
        paragraphs: [
          'Temporary uploads, generated results, and task caches are usually retained only for a reasonable period needed for processing, download, or troubleshooting.',
          'Because queues, backups, log rotation, and system failures can exist, we cannot promise instant deletion at the exact moment a task finishes, but we try to limit retention scope and time.',
        ],
      },
      {
        icon: UserCheck,
        title: '5. Your choices and rights',
        paragraphs: [
          'You may use some basic features without creating an account. For cloud, login, or subscription features, you decide whether to continue.',
          'You may request access, correction, or deletion of account-related information. Some security, billing, audit, or troubleshooting records may need to remain for a reasonable period.',
        ],
      },
      {
        icon: ShieldCheck,
        title: '6. Security',
        paragraphs: [
          'We use hashed passwords, token-based authentication, role-based access, security logs, containerized deployment, and least-necessary access practices to reduce risk.',
          'No online service can be perfectly secure. If you handle highly sensitive, regulated, or legally binding documents, please assess the risk before uploading.',
        ],
      },
      {
        icon: Clock3,
        title: '7. Updates',
        paragraphs: [
          'As admin, billing, team, enterprise API, or cloud features expand, this policy may change. Material updates will be reflected on this page.',
        ],
      },
      {
        icon: Mail,
        title: '8. Contact',
        paragraphs: [
          'For privacy, file-processing, or account-data questions, contact the administrator through the support channel shown by the site. Include screenshots, timestamps, error codes, and short reproduction steps when reporting issues.',
        ],
      },
    ] satisfies LegalSection[],
  },
}

const activeContent = computed(() => {
  const key = locale.value.startsWith('zh') ? 'zh' : 'en'
  return content[key]
})
</script>

<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.12),transparent_28%),radial-gradient(circle_at_100%_0%,rgba(34,197,94,0.1),transparent_24%),linear-gradient(180deg,#f8fbff_0%,#f8fafc_100%)] dark:bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.12),transparent_28%),radial-gradient(circle_at_100%_0%,rgba(34,197,94,0.1),transparent_24%),linear-gradient(180deg,#020617_0%,#0f172a_100%)]">
    <section class="px-4 pb-10 pt-16 sm:px-6 lg:px-8">
      <div class="mx-auto max-w-6xl">
        <div class="grid gap-6 rounded-[36px] border border-white/70 bg-white/88 p-7 shadow-2xl shadow-sky-100/60 backdrop-blur dark:border-white/10 dark:bg-slate-900/78 dark:shadow-none lg:grid-cols-[1.2fr_0.8fr] lg:p-10">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full border border-sky-200/80 bg-sky-50/90 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700 dark:border-sky-500/20 dark:bg-sky-500/10 dark:text-sky-300">
              <Sparkles class="h-4 w-4" />
              {{ activeContent.eyebrow }}
            </div>

            <h1 class="mt-6 text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl">
              {{ activeContent.title }}
            </h1>
            <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600 dark:text-slate-300 sm:text-lg">
              {{ activeContent.description }}
            </p>
            <p class="mt-5 text-sm font-medium text-slate-500 dark:text-slate-400">
              {{ activeContent.updated }}
            </p>
          </div>

          <aside class="rounded-[30px] border border-slate-200/80 bg-slate-50/88 p-6 dark:border-slate-800 dark:bg-slate-950/50">
            <p class="text-sm font-semibold text-slate-900 dark:text-white">
              {{ activeContent.summaryTitle }}
            </p>
            <p class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
              {{ activeContent.summary }}
            </p>
            <p class="mt-5 rounded-2xl bg-white p-4 text-xs leading-6 text-slate-500 shadow-sm dark:bg-slate-900 dark:text-slate-400">
              {{ activeContent.note }}
            </p>
          </aside>
        </div>
      </div>
    </section>

    <section class="px-4 pb-20 sm:px-6 lg:px-8">
      <div class="mx-auto grid max-w-6xl gap-5 lg:grid-cols-2">
        <article
          v-for="section in activeContent.sections"
          :key="section.title"
          class="rounded-[30px] border border-white/70 bg-white/84 p-6 shadow-lg shadow-slate-100/60 backdrop-blur dark:border-white/10 dark:bg-slate-900/70 dark:shadow-none sm:p-7"
        >
          <div class="flex items-start gap-4">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-sky-50 text-sky-700 dark:bg-sky-500/10 dark:text-sky-300">
              <component :is="section.icon" class="h-5 w-5" />
            </div>
            <div>
              <h2 class="text-xl font-semibold text-slate-950 dark:text-white">
                {{ section.title }}
              </h2>
              <p
                v-for="paragraph in section.paragraphs"
                :key="paragraph"
                class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300 sm:text-[15px]"
              >
                {{ paragraph }}
              </p>
              <ul v-if="section.bullets" class="mt-4 space-y-2">
                <li
                  v-for="bullet in section.bullets"
                  :key="bullet"
                  class="flex gap-2 text-sm leading-6 text-slate-600 dark:text-slate-300"
                >
                  <span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-500" />
                  <span>{{ bullet }}</span>
                </li>
              </ul>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
