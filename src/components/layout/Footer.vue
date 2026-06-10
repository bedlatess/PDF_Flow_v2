<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSiteConfigStore } from '@/stores/siteConfig'
import {
  ArrowUpRight,
  FileStack,
  Headphones,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Sparkles,
} from 'lucide-vue-next'

const { t, locale } = useI18n()
const siteConfigStore = useSiteConfigStore()
const activeLocale = computed(() => locale.value)
const currentYear = new Date().getFullYear()

const toolLinks = computed(() => [
  { label: t('tools.merge.title'), href: '/tools/merge', featureKey: 'merge_pdf' },
  { label: t('tools.split.title'), href: '/tools/split', featureKey: 'split_pdf' },
  { label: t('tools.rotate.title'), href: '/tools/rotate', featureKey: 'rotate_pdf' },
  { label: t('tools.officeToPdf.title'), href: '/tools/office-to-pdf', featureKey: 'office_to_pdf' },
])

const visibleToolLinks = computed(() =>
  toolLinks.value.filter((link) => siteConfigStore.getFeatureFlag(link.featureKey, link.label).enabled)
)

const brandName = computed(() => siteConfigStore.getSettingValue('site_name', t('app.title')))
const supportEmail = computed(() => siteConfigStore.getSettingValue('support_email', 'support@pdf-flow.com'))

const productLinks = computed(() => [
  { label: t('nav.features'), href: '/features' },
  { label: t('nav.pricing'), href: '/pricing' },
  { label: t('auth.login'), href: '/auth/login' },
  { label: t('auth.signUp'), href: '/auth/register' },
])

const legalLinks = computed(() => [
  { label: t('footer.privacyPolicy'), href: '/privacy' },
  { label: t('footer.termsOfService'), href: '/terms' },
])

const footerCopy = computed(() => {
  if (locale.value === 'zh') {
    return {
      eyebrow: 'Secure PDF Studio',
      description: '\u4e3a\u6ce8\u91cd\u9690\u79c1\u3001\u901f\u5ea6\u548c\u6e05\u6670\u53cd\u9988\u7684\u6587\u6863\u5de5\u4f5c\u6d41\u7a0b\u800c\u8bbe\u8ba1\u3002',
      trustPrivacyTitle: '\u672c\u5730\u4f18\u5148',
      trustPrivacyDescription: '\u57fa\u7840 PDF \u5904\u7406\u5c3d\u91cf\u7559\u5728\u6d4f\u89c8\u5668\u5185\u5b8c\u6210\u3002',
      trustSupportTitle: '\u95ee\u9898\u66f4\u597d\u5b9a\u4f4d',
      trustSupportDescription: '\u9519\u8bef\u63d0\u793a\u4f1a\u4fdd\u7559\u5fc5\u8981\u7ebf\u7d22\uff0c\u65b9\u4fbf\u622a\u56fe\u53cd\u9988\u3002',
      trustWorkflowTitle: '\u4f53\u9a8c\u66f4\u8fde\u8d2f',
      trustWorkflowDescription: '\u4e0a\u4f20\u3001\u5904\u7406\u3001\u4e0b\u8f7d\u5728\u4e00\u4e2a\u5de5\u4f5c\u533a\u91cc\u5b8c\u6210\u3002',
      linksTitle: '\u5feb\u901f\u5165\u53e3',
      productTitle: '\u4ea7\u54c1\u5bfc\u822a',
      supportTitle: '\u652f\u6301\u4e0e\u534f\u8bae',
      contactTitle: '\u8054\u7cfb\u652f\u6301',
      contactDescription: '\u9047\u5230\u4e0a\u4f20\u3001\u8f6c\u6362\u6216\u5957\u9910\u95ee\u9898\u65f6\uff0c\u9644\u4e0a\u622a\u56fe\u548c\u5927\u81f4\u65f6\u95f4\uff0c\u4f1a\u66f4\u5feb\u5b9a\u4f4d\u3002',
      contactPromise: '\u5de5\u4f5c\u65e5 24 \u5c0f\u65f6\u5185\u54cd\u5e94',
      bottomLine: '\u9690\u79c1\u4f18\u5148\u7684 PDF \u5de5\u4f5c\u53f0',
      copyright: '\u4e3a\u6ce8\u91cd\u9690\u79c1\u7684\u6587\u6863\u5de5\u4f5c\u8005\u800c\u8bbe\u8ba1',
    }
  }

  if (locale.value === 'es') {
    return {
      eyebrow: 'Secure PDF Studio',
      description: 'Pensado para flujos PDF que priorizan privacidad, velocidad y comentarios claros.',
      trustPrivacyTitle: 'Primero en local',
      trustPrivacyDescription: 'Las tareas PDF esenciales permanecen en el navegador siempre que sea posible.',
      trustSupportTitle: 'Mas facil de revisar',
      trustSupportDescription: 'Los mensajes conservan pistas utiles para que soporte pueda ubicar el problema mas rapido.',
      trustWorkflowTitle: 'Todo en un ritmo',
      trustWorkflowDescription: 'Subida, proceso y descarga conviven en un mismo espacio de trabajo.',
      linksTitle: 'Accesos rapidos',
      productTitle: 'Producto',
      supportTitle: 'Soporte y legal',
      contactTitle: 'Contactar soporte',
      contactDescription: 'Si ves un problema con carga, conversion o suscripcion, comparte una captura y la hora aproximada para acelerarlo.',
      contactPromise: 'Respuesta en 24 horas habiles',
      bottomLine: 'Espacio PDF centrado en privacidad',
      copyright: 'Hecho para equipos que necesitan documentos sin ruido',
    }
  }

  return {
    eyebrow: 'Secure PDF Studio',
    description: 'Built for document workflows that care about privacy, speed, and clearer feedback.',
    trustPrivacyTitle: 'Local-first',
    trustPrivacyDescription: 'Core PDF work stays in the browser whenever it can.',
    trustSupportTitle: 'Easier to troubleshoot',
    trustSupportDescription: 'Clear messages make it easier to share issues with support and get help faster.',
    trustWorkflowTitle: 'One workspace',
    trustWorkflowDescription: 'Upload, processing, and download stay inside one calmer flow.',
    linksTitle: 'Quick access',
    productTitle: 'Product',
    supportTitle: 'Support and legal',
    contactTitle: 'Contact support',
    contactDescription: 'If something goes wrong with upload, conversion, or billing, a screenshot and rough timestamp help us diagnose it faster.',
    contactPromise: 'Response within 24 business hours',
    bottomLine: 'Privacy-first PDF workspace',
    copyright: 'Designed for teams who want less document friction',
  }
})

const supportContact = computed(() =>
  siteConfigStore.getSettingValue('support_contact', footerCopy.value.contactDescription)
)

const trustNotes = computed(() => [
  {
    title: footerCopy.value.trustPrivacyTitle,
    description: footerCopy.value.trustPrivacyDescription,
    icon: LockKeyhole,
  },
  {
    title: footerCopy.value.trustSupportTitle,
    description: footerCopy.value.trustSupportDescription,
    icon: Headphones,
  },
  {
    title: footerCopy.value.trustWorkflowTitle,
    description: footerCopy.value.trustWorkflowDescription,
    icon: FileStack,
  },
])

const quickSections = computed(() => [
  {
    title: footerCopy.value.linksTitle,
    icon: FileStack,
    links: visibleToolLinks.value,
  },
  {
    title: footerCopy.value.productTitle,
    icon: ShieldCheck,
    links: productLinks.value,
  },
])

onMounted(() => {
  siteConfigStore.fetchPublicConfig()
})
</script>

<template>
  <footer
    class="border-t border-white/60 bg-[radial-gradient(circle_at_top_left,rgba(109,40,217,0.12),transparent_25%),radial-gradient(circle_at_100%_0%,rgba(14,165,233,0.08),transparent_22%),linear-gradient(180deg,#fbf9ff_0%,#f8fafc_100%)] dark:border-white/10 dark:bg-[radial-gradient(circle_at_top_left,rgba(139,92,246,0.15),transparent_24%),radial-gradient(circle_at_100%_0%,rgba(14,165,233,0.10),transparent_22%),linear-gradient(180deg,#020617_0%,#0f172a_100%)]"
    :data-locale="activeLocale"
  >
    <div class="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div class="grid gap-6 lg:grid-cols-[1.15fr_0.95fr_0.9fr]">
        <section class="rounded-[32px] border border-white/70 bg-white/84 p-7 shadow-xl shadow-violet-100/60 backdrop-blur dark:border-white/10 dark:bg-slate-900/72 dark:shadow-none">
          <div class="flex items-center gap-3">
            <div class="relative flex h-12 w-12 items-center justify-center overflow-hidden rounded-[18px] bg-[linear-gradient(145deg,#2e1065_0%,#6d28d9_54%,#c084fc_100%)] text-white shadow-lg shadow-violet-500/25">
              <Sparkles class="relative h-5 w-5" />
              <span class="absolute right-[7px] top-[6px] h-1.5 w-1.5 rounded-full bg-fuchsia-100 shadow-[0_0_10px_rgba(255,255,255,0.85)]" />
            </div>

            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-violet-700 dark:text-violet-300">
                {{ footerCopy.eyebrow }}
              </p>
              <h3 class="text-xl font-semibold text-slate-950 dark:text-white">
                {{ brandName }}
              </h3>
            </div>
          </div>

          <p class="mt-5 max-w-xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            {{ footerCopy.description }}
          </p>

          <div class="mt-7 grid gap-4 sm:grid-cols-3">
            <article
              v-for="note in trustNotes"
              :key="note.title"
              class="rounded-[24px] border border-slate-200/80 bg-slate-50/85 p-4 dark:border-slate-800 dark:bg-slate-950/55"
            >
              <component :is="note.icon" class="h-5 w-5 text-violet-600 dark:text-violet-300" />
              <p class="mt-3 text-sm font-semibold text-slate-900 dark:text-white">
                {{ note.title }}
              </p>
              <p class="mt-2 text-xs leading-6 text-slate-600 dark:text-slate-400">
                {{ note.description }}
              </p>
            </article>
          </div>
        </section>

        <section class="rounded-[32px] border border-white/70 bg-white/80 p-7 shadow-lg shadow-slate-100/60 backdrop-blur dark:border-white/10 dark:bg-slate-900/68 dark:shadow-none">
          <div class="grid gap-6 sm:grid-cols-2">
            <div
              v-for="section in quickSections"
              :key="section.title"
            >
              <div class="flex items-center gap-2">
                <component :is="section.icon" class="h-4 w-4 text-sky-600 dark:text-sky-300" />
                <h4 class="text-sm font-semibold uppercase tracking-[0.22em] text-slate-900 dark:text-white">
                  {{ section.title }}
                </h4>
              </div>

              <ul class="mt-5 space-y-3">
                <li
                  v-for="link in section.links"
                  :key="link.href"
                >
                  <a
                    :href="link.href"
                    class="group flex items-center justify-between rounded-2xl px-3 py-2 text-sm text-slate-700 transition hover:bg-slate-50 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800/80 dark:hover:text-white"
                  >
                    <span>{{ link.label }}</span>
                    <ArrowUpRight class="h-4 w-4 opacity-0 transition group-hover:opacity-100" />
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section class="rounded-[32px] border border-white/70 bg-white/80 p-7 shadow-lg shadow-slate-100/60 backdrop-blur dark:border-white/10 dark:bg-slate-900/68 dark:shadow-none">
          <div class="flex items-center gap-2">
            <Mail class="h-4 w-4 text-violet-600 dark:text-violet-300" />
            <h4 class="text-sm font-semibold uppercase tracking-[0.22em] text-slate-900 dark:text-white">
              {{ footerCopy.supportTitle }}
            </h4>
          </div>

          <ul class="mt-5 space-y-3">
            <li
              v-for="link in legalLinks"
              :key="link.href"
            >
              <a
                :href="link.href"
                class="group flex items-center justify-between rounded-2xl px-3 py-2 text-sm text-slate-700 transition hover:bg-slate-50 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800/80 dark:hover:text-white"
              >
                <span>{{ link.label }}</span>
                <ArrowUpRight class="h-4 w-4 opacity-0 transition group-hover:opacity-100" />
              </a>
            </li>
          </ul>

          <div class="mt-6 rounded-[26px] border border-violet-200/70 bg-[linear-gradient(180deg,rgba(245,243,255,0.95),rgba(255,255,255,0.92))] p-5 dark:border-violet-500/20 dark:bg-[linear-gradient(180deg,rgba(30,27,75,0.7),rgba(15,23,42,0.78))]">
            <p class="text-sm font-semibold text-slate-900 dark:text-white">
              {{ footerCopy.contactTitle }}
            </p>
            <p class="mt-2 text-xs leading-6 text-slate-600 dark:text-slate-300">
              {{ supportContact }}
            </p>
            <a
              :href="`mailto:${supportEmail}`"
              class="mt-4 inline-flex items-center gap-2 text-sm font-medium text-violet-700 transition hover:text-violet-500 dark:text-violet-300"
            >
              {{ supportEmail }}
              <ArrowUpRight class="h-4 w-4" />
            </a>
            <div class="mt-4 inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-2 text-xs font-medium text-slate-600 dark:bg-slate-950/55 dark:text-slate-300">
              <Headphones class="h-3.5 w-3.5 text-violet-500" />
              {{ footerCopy.contactPromise }}
            </div>
          </div>
        </section>
      </div>

      <div class="mt-8 flex flex-col gap-3 border-t border-slate-200/80 pt-6 text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400 sm:flex-row sm:items-center sm:justify-between">
        <p>&copy; {{ currentYear }} {{ brandName }}. {{ footerCopy.copyright }}</p>
        <p>{{ footerCopy.bottomLine }}</p>
      </div>
    </div>
  </footer>
</template>
