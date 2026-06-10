<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AlertTriangle,
  BadgeCheck,
  Ban,
  CreditCard,
  FileText,
  Gavel,
  Mail,
  Shield,
  Sparkles,
  UserCog,
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
    eyebrow: '服务条款',
    title: '使用 PDF-Flow 前请了解这些规则',
    updated: '最后更新：2026 年 6 月 10 日',
    description:
      '这些条款说明你使用 PDF-Flow 时的基本权利、责任和限制。我们尽量用清楚的语言解释，而不是把重要信息藏在复杂术语里。',
    summaryTitle: '核心原则',
    summary:
      '你可以使用 PDF-Flow 处理合法、合规、属于你或你有权处理的文件。请不要上传违法、侵权、恶意、滥用资源或可能伤害他人的内容。重要文件请自行保留备份并核对处理结果。',
    note:
      '如果你不同意这些条款，请停止使用需要登录、上传、云端处理或订阅的功能。',
    sections: [
      {
        icon: BadgeCheck,
        title: '1. 接受条款',
        paragraphs: [
          '当你访问、注册、登录或继续使用 PDF-Flow，即表示你理解并同意遵守当前服务条款和隐私政策。',
          '我们可能会根据产品变化、法律要求或运营需要更新条款。更新后的条款会展示在本页面，继续使用服务即表示你接受更新后的版本。',
        ],
      },
      {
        icon: UserCog,
        title: '2. 账户与安全',
        paragraphs: [
          '你需要对自己的账户、登录凭据和账户下发生的操作负责。请使用安全密码，不要共享账户，也不要允许未经授权的人使用你的账户。',
          '如果你发现账户异常、疑似被盗、订阅异常或未知任务记录，请尽快联系管理员或支持渠道。',
        ],
        bullets: [
          '不得冒用他人身份注册或使用服务。',
          '不得绕过权限、套餐限制、上传限制或安全控制。',
          '不得尝试访问后台、接口或其他用户数据。',
        ],
      },
      {
        icon: FileText,
        title: '3. 文件与内容责任',
        paragraphs: [
          '你确认自己拥有上传、转换、识别、分析或下载相关文件所需的合法权利。PDF-Flow 不会替你判断某份文件是否可以处理或传播。',
          '你应自行保存重要文件的原件和备份，并在使用处理结果前进行核对。转换、压缩、OCR 或 AI 分析可能受到文件质量、格式、语言、浏览器环境或第三方依赖影响。',
        ],
      },
      {
        icon: Ban,
        title: '4. 禁止行为',
        paragraphs: [
          '为了保护服务稳定和其他用户体验，你不得将 PDF-Flow 用于违法、侵权、欺诈、骚扰、传播恶意代码、批量滥用资源或规避访问控制的行为。',
          '如果系统检测到异常请求、恶意文件、资源滥用或高风险行为，我们可能限制上传、暂停任务、冻结账户或拒绝继续提供部分服务。',
        ],
        bullets: [
          '上传病毒、木马、攻击脚本或伪装文件。',
          '批量刷接口、绕过速率限制或消耗异常资源。',
          '处理你无权处理的受版权、隐私或监管保护的内容。',
        ],
      },
      {
        icon: CreditCard,
        title: '5. 订阅、付费与功能限制',
        paragraphs: [
          '部分高级功能可能需要登录、Pro 或企业权限。具体功能、额度、价格、退款和取消规则以购买页面或支付流程展示为准。',
          '我们可能根据产品阶段调整套餐边界、可用额度或功能开放方式。对于影响较大的调整，会尽量用清楚的页面提示或公告说明。',
        ],
      },
      {
        icon: Shield,
        title: '6. 服务可用性与限制',
        paragraphs: [
          '我们会努力保持服务稳定，但不能保证所有文件、格式、浏览器、网络环境和第三方依赖都能始终正常工作。',
          '服务可能因为维护、升级、依赖故障、网络问题、安全事件或不可抗力而中断、变慢或暂时不可用。我们会尽量缩短影响并恢复服务。',
        ],
      },
      {
        icon: AlertTriangle,
        title: '7. 免责声明',
        paragraphs: [
          'PDF-Flow 提供的是文档处理工具，不提供法律、财务、医疗或专业审查意见。AI 分析、OCR 识别和格式转换结果可能存在错误或遗漏。',
          '对于重要合同、发票、证件、合规文件或其他关键资料，请在使用结果前自行复核，必要时寻求专业人士确认。',
        ],
      },
      {
        icon: Gavel,
        title: '8. 变更、暂停与终止',
        paragraphs: [
          '如果账户违反条款、危害服务安全、侵犯他人权益或造成明显资源滥用，我们可以限制、暂停或终止相关账户和任务。',
          '你也可以停止使用服务，或在账户功能支持时请求删除账户。某些安全、支付、审计和故障排查记录可能会在合理期限内继续保留。',
        ],
      },
      {
        icon: Mail,
        title: '9. 联系与反馈',
        paragraphs: [
          '如果你对条款、账户、订阅或文件处理结果有疑问，请通过网站展示的支持渠道联系管理员。反馈技术问题时，请提供截图、时间点、错误编号和简短复现步骤。',
        ],
      },
    ] satisfies LegalSection[],
  },
  en: {
    eyebrow: 'Terms of Service',
    title: 'Please understand these rules before using PDF-Flow',
    updated: 'Last updated: June 10, 2026',
    description:
      'These terms explain the basic rights, responsibilities, and limits that apply when you use PDF-Flow. We use plain language so important information is easier to understand.',
    summaryTitle: 'Core principle',
    summary:
      'You may use PDF-Flow to process legal documents that you own or are allowed to handle. Do not upload unlawful, infringing, malicious, abusive, or harmful content. Keep your own backups and verify important results.',
    note:
      'If you do not agree with these terms, please stop using features that require login, upload, cloud processing, or subscription.',
    sections: [
      {
        icon: BadgeCheck,
        title: '1. Acceptance',
        paragraphs: [
          'By accessing, registering, signing in, or continuing to use PDF-Flow, you agree to the current Terms of Service and Privacy Policy.',
          'We may update these terms as the product, legal requirements, or operations change. Updated terms will be shown on this page.',
        ],
      },
      {
        icon: UserCog,
        title: '2. Accounts and security',
        paragraphs: [
          'You are responsible for your account, credentials, and activity under your account. Use a secure password and do not share access with unauthorized people.',
          'If you notice suspicious account activity, billing issues, or unknown tasks, contact the administrator or support channel promptly.',
        ],
        bullets: [
          'Do not impersonate another person or organization.',
          'Do not bypass permissions, plan limits, upload limits, or security controls.',
          'Do not attempt to access admin areas, private APIs, or other users data.',
        ],
      },
      {
        icon: FileText,
        title: '3. Files and content responsibility',
        paragraphs: [
          'You confirm that you have the legal right to upload, convert, recognize, analyze, or download the files you use with PDF-Flow.',
          'You should keep your own originals and backups, and review results before relying on them. Conversion, compression, OCR, and AI analysis can be affected by file quality, format, language, browser environment, and third-party dependencies.',
        ],
      },
      {
        icon: Ban,
        title: '4. Prohibited use',
        paragraphs: [
          'To protect the service and other users, you may not use PDF-Flow for unlawful, infringing, fraudulent, harassing, malicious, abusive, or access-control-bypassing activity.',
          'If we detect suspicious requests, malicious files, resource abuse, or high-risk behavior, we may limit uploads, stop tasks, suspend accounts, or refuse part of the service.',
        ],
      },
      {
        icon: CreditCard,
        title: '5. Subscriptions and feature limits',
        paragraphs: [
          'Some advanced features may require login, Pro, or enterprise access. Feature availability, quotas, prices, refunds, and cancellation rules follow the purchase or payment flow shown at the time.',
          'We may adjust plan boundaries, quotas, and feature availability as the product evolves. Material changes should be communicated clearly.',
        ],
      },
      {
        icon: Shield,
        title: '6. Availability and limits',
        paragraphs: [
          'We work to keep the service stable, but we cannot guarantee every file, format, browser, network, or third-party dependency will work at all times.',
          'Maintenance, upgrades, dependency failures, network issues, security events, or force majeure may interrupt or slow the service.',
        ],
      },
      {
        icon: AlertTriangle,
        title: '7. Disclaimer',
        paragraphs: [
          'PDF-Flow is a document-processing tool. It does not provide legal, financial, medical, or professional review advice. AI analysis, OCR, and conversion results may contain errors or omissions.',
          'For contracts, invoices, identity documents, compliance materials, or other critical files, review results yourself and seek professional confirmation when needed.',
        ],
      },
      {
        icon: Gavel,
        title: '8. Changes, suspension, and termination',
        paragraphs: [
          'If an account violates these terms, harms service security, infringes rights, or causes clear resource abuse, we may restrict, suspend, or terminate related accounts and tasks.',
          'You may stop using the service or request account deletion where supported. Some security, billing, audit, and troubleshooting records may remain for a reasonable period.',
        ],
      },
      {
        icon: Mail,
        title: '9. Contact',
        paragraphs: [
          'For questions about these terms, accounts, subscriptions, or file results, contact the administrator through the support channel shown by the site. Include screenshots, timestamps, error codes, and short reproduction steps for technical issues.',
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
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(20,184,166,0.12),transparent_28%),radial-gradient(circle_at_100%_0%,rgba(56,189,248,0.1),transparent_24%),linear-gradient(180deg,#f8fffd_0%,#f8fafc_100%)] dark:bg-[radial-gradient(circle_at_top_left,rgba(20,184,166,0.12),transparent_28%),radial-gradient(circle_at_100%_0%,rgba(56,189,248,0.1),transparent_24%),linear-gradient(180deg,#02110f_0%,#0f172a_100%)]">
    <section class="px-4 pb-10 pt-16 sm:px-6 lg:px-8">
      <div class="mx-auto max-w-6xl">
        <div class="grid gap-6 rounded-[36px] border border-white/70 bg-white/88 p-7 shadow-2xl shadow-emerald-100/60 backdrop-blur dark:border-white/10 dark:bg-slate-900/78 dark:shadow-none lg:grid-cols-[1.2fr_0.8fr] lg:p-10">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full border border-emerald-200/80 bg-emerald-50/90 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300">
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
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
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
                  <span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
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
