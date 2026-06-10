<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-white to-blue-50 px-4 py-12">
    <div class="max-w-2xl w-full">
      <!-- Success Card -->
      <div class="bg-white rounded-2xl shadow-xl p-8 text-center">
        <!-- Success Icon -->
        <div class="inline-block p-4 bg-green-100 rounded-full mb-6">
          <CheckCircle2 class="h-16 w-16 text-green-600" />
        </div>

        <!-- Title -->
        <h1 class="text-3xl font-bold text-gray-900 mb-4">
          🎉 {{ $t('payment.success.title') }}
        </h1>

        <p class="text-lg text-gray-600 mb-8">
          {{ $t('payment.success.message') }}
        </p>

        <!-- Plan Details -->
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 mb-8">
          <div class="flex items-center justify-between mb-4">
            <span class="text-gray-700 font-medium">{{ $t('payment.success.plan') }}</span>
            <span class="text-xl font-bold text-indigo-600">Pro</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-gray-700 font-medium">{{ $t('payment.success.status') }}</span>
            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              <span class="h-2 w-2 bg-green-500 rounded-full mr-2"></span>
              {{ $t('payment.success.active') }}
            </span>
          </div>
        </div>

        <!-- Features Unlocked -->
        <div class="text-left mb-8">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            ✨ {{ $t('payment.success.unlocked') }}
          </h3>
          <ul class="space-y-2">
            <li class="flex items-start">
              <CheckCircle2 class="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
              <span class="text-gray-700">{{ $t('payment.success.feature1') }}</span>
            </li>
            <li class="flex items-start">
              <CheckCircle2 class="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
              <span class="text-gray-700">{{ $t('payment.success.feature2') }}</span>
            </li>
            <li class="flex items-start">
              <CheckCircle2 class="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
              <span class="text-gray-700">{{ $t('payment.success.feature3') }}</span>
            </li>
            <li class="flex items-start">
              <CheckCircle2 class="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
              <span class="text-gray-700">{{ $t('payment.success.feature4') }}</span>
            </li>
          </ul>
        </div>

        <!-- Actions -->
        <div class="flex gap-4">
          <button
            @click="goToProfile"
            class="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl"
          >
            {{ $t('payment.success.viewAccount') }}
          </button>
          <button
            @click="startUsing"
            class="flex-1 px-6 py-3 bg-white border-2 border-indigo-600 text-indigo-600 rounded-xl font-medium hover:bg-indigo-50 transition-all"
          >
            {{ $t('payment.success.startUsing') }}
          </button>
        </div>

        <!-- Support Link -->
        <p class="mt-6 text-sm text-gray-500">
          {{ $t('payment.success.needHelp') }}
          <a :href="`mailto:${supportEmail}`" class="text-indigo-600 hover:text-indigo-700 font-medium">
            {{ $t('payment.success.contactSupport') }}
          </a>
        </p>
      </div>

      <!-- Next Steps -->
      <div class="mt-8 bg-white rounded-xl p-6 shadow-lg">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          🚀 {{ $t('payment.success.nextSteps') }}
        </h3>
        <div class="space-y-3">
          <div class="flex items-start">
            <span class="flex-shrink-0 h-6 w-6 flex items-center justify-center rounded-full bg-indigo-100 text-indigo-600 text-sm font-medium mr-3">1</span>
            <span class="text-gray-700">{{ $t('payment.success.step1') }}</span>
          </div>
          <div class="flex items-start">
            <span class="flex-shrink-0 h-6 w-6 flex items-center justify-center rounded-full bg-indigo-100 text-indigo-600 text-sm font-medium mr-3">2</span>
            <span class="text-gray-700">{{ $t('payment.success.step2') }}</span>
          </div>
          <div class="flex items-start">
            <span class="flex-shrink-0 h-6 w-6 flex items-center justify-center rounded-full bg-indigo-100 text-indigo-600 text-sm font-medium mr-3">3</span>
            <span class="text-gray-700">{{ $t('payment.success.step3') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CheckCircle2 } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { useSiteConfigStore } from '@/stores/siteConfig'

const router = useRouter()
const userStore = useUserStore()
const siteConfigStore = useSiteConfigStore()
const supportEmail = computed(() => siteConfigStore.getSettingValue('support_email', 'support@pdf-flow.com'))

onMounted(async () => {
  siteConfigStore.fetchPublicConfig()
  // 刷新用户信息以获取最新的订阅状态
  if (userStore.isAuthenticated) {
    await userStore.checkAuth()
  }
})

const goToProfile = () => {
  router.push('/auth/profile')
}

const startUsing = () => {
  router.push('/')
}
</script>
