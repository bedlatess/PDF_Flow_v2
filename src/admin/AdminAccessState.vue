<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ShieldAlert } from 'lucide-vue-next'

const route = useRoute()
const reason = computed(() => String(route.query.reason || 'auth'))

const title = computed(() =>
  reason.value === 'forbidden' ? '没有后台权限' : '需要管理员登录'
)

const description = computed(() =>
  reason.value === 'forbidden'
    ? '当前账号不是管理员。请切换到拥有 admin 角色的账号后再打开后台。'
    : '后台站点只接受已经登录的管理员会话。请先在主站完成登录，再回到后台域名。'
)
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-10 text-white">
    <section class="w-full max-w-xl rounded-lg border border-white/10 bg-white p-6 text-slate-950 shadow-2xl sm:p-8">
      <div class="flex h-12 w-12 items-center justify-center rounded-md bg-slate-950 text-white">
        <ShieldAlert class="h-6 w-6" />
      </div>
      <h1 class="mt-5 text-3xl font-semibold">{{ title }}</h1>
      <p class="mt-3 text-sm leading-7 text-slate-600">{{ description }}</p>
      <a
        class="mt-6 inline-flex min-h-11 items-center rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800"
        href="/zh-cn/auth/login"
      >
        打开主站登录页
      </a>
    </section>
  </main>
</template>
