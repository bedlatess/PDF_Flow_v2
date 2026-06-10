<script setup lang="ts">
import { computed, ref, useSlots } from 'vue'
import { useI18n } from 'vue-i18n'
import { validateImage, validatePDF } from '@/utils/file-validator'

type AcceptValue = 'pdf' | 'image' | 'all' | string | string[]

interface DragDropZoneProps {
  accept?: AcceptValue
  multiple?: boolean
  maxSize?: number
  maxFiles?: number
}

const props = withDefaults(defineProps<DragDropZoneProps>(), {
  accept: 'pdf',
  multiple: true,
  maxSize: 100,
  maxFiles: 10,
})

const emit = defineEmits<{
  filesSelected: [files: File[]]
  error: [message: string]
}>()

const { t, locale } = useI18n()
const slots = useSlots()

const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement>()

const acceptTokens = computed(() => {
  if (Array.isArray(props.accept)) {
    return props.accept.map((token) => token.trim()).filter(Boolean)
  }

  switch (props.accept) {
    case 'pdf':
      return ['application/pdf', '.pdf']
    case 'image':
      return ['image/*', '.png', '.jpg', '.jpeg', '.webp']
    case 'all':
      return ['application/pdf', '.pdf', 'image/*', '.png', '.jpg', '.jpeg', '.webp']
    default:
      return String(props.accept)
        .split(',')
        .map((token) => token.trim())
        .filter(Boolean)
  }
})

const acceptedTypes = computed(() => acceptTokens.value.join(','))

const acceptsPDF = computed(() =>
  acceptTokens.value.some((token) => token === 'application/pdf' || token === '.pdf')
)

const acceptsImage = computed(() =>
  acceptTokens.value.some((token) => token === 'image/*' || token.startsWith('image/') || token.match(/^\.(png|jpg|jpeg|webp|gif|bmp|svg)$/i))
)

const helperText = computed(() => {
  const extensionTokens = acceptTokens.value
    .filter((token) => token.startsWith('.'))
    .map((token) => token.slice(1).toUpperCase())
  const language = locale.value.toLowerCase()
  const isZh = language.startsWith('zh')
  const isEs = language.startsWith('es')

  const formatList = (text: string) => {
    if (isZh) {
      return `${text}，最大 ${props.maxSize}MB`
    }

    if (isEs) {
      return `${text} hasta ${props.maxSize}MB`
    }

    return `${text} up to ${props.maxSize}MB`
  }

  if (props.accept === 'pdf') {
    return formatList('PDF')
  }

  if (props.accept === 'image') {
    return formatList('PNG, JPG, WEBP')
  }

  if (props.accept === 'all') {
    return isZh
      ? `PDF 和图片文件，最大 ${props.maxSize}MB`
      : isEs
        ? `Archivos PDF e imagen hasta ${props.maxSize}MB`
        : `PDF and image files up to ${props.maxSize}MB`
  }

  if (extensionTokens.length > 0) {
    return formatList(extensionTokens.join(', '))
  }

  return isZh
    ? `文件最大 ${props.maxSize}MB`
    : isEs
      ? `Archivos hasta ${props.maxSize}MB`
      : `Files up to ${props.maxSize}MB`
})

const matchesAccept = (file: File) => {
  if (acceptTokens.value.length === 0) {
    return true
  }

  const extension = file.name.includes('.')
    ? `.${file.name.split('.').pop()?.toLowerCase()}`
    : ''

  return acceptTokens.value.some((token) => {
    const normalized = token.toLowerCase()

    if (normalized === '*/*') {
      return true
    }

    if (normalized.startsWith('.')) {
      return extension === normalized
    }

    if (normalized.endsWith('/*')) {
      const family = normalized.slice(0, -2)
      return file.type.toLowerCase().startsWith(`${family}/`)
    }

    return file.type.toLowerCase() === normalized
  })
}

const validateFile = async (file: File) => {
  if (!matchesAccept(file)) {
    return false
  }

  if (acceptsPDF.value && file.type === 'application/pdf') {
    return validatePDF(file)
  }

  if (acceptsImage.value && file.type.startsWith('image/')) {
    return validateImage(file)
  }

  return true
}

const handleDragEnter = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
}

const handleDrop = async (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false

  const files = Array.from(event.dataTransfer?.files || [])
  await processFiles(files)
}

const handleFileSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  await processFiles(files)
  input.value = ''
}

const processFiles = async (files: File[]) => {
  if (files.length === 0) {
    return
  }

  if (files.length > props.maxFiles) {
    emit('error', `You can upload up to ${props.maxFiles} files at a time.`)
    return
  }

  const validFiles: File[] = []

  for (const file of files) {
    const fileSizeMB = file.size / (1024 * 1024)
    if (fileSizeMB > props.maxSize) {
      emit('error', `${file.name} is larger than ${props.maxSize}MB.`)
      continue
    }

    const isValid = await validateFile(file)
    if (!isValid) {
      emit('error', `${file.name} is not a supported file type.`)
      continue
    }

    validFiles.push(file)
  }

  if (validFiles.length > 0) {
    emit('filesSelected', validFiles)
  }
}

const openFileDialog = () => {
  fileInputRef.value?.click()
}
</script>

<template>
  <div
    data-testid="drag-drop-zone"
    :class="[
      'group relative flex min-h-[320px] flex-col items-center justify-center overflow-hidden rounded-[28px] border border-dashed px-6 py-10 text-center transition-all duration-300',
      'cursor-pointer border-slate-300 bg-white/80 shadow-sm backdrop-blur-sm hover:border-primary hover:shadow-lg hover:shadow-primary/10',
      'dark:border-slate-700 dark:bg-slate-900/70',
      {
        'border-primary bg-primary/5 shadow-lg shadow-primary/10': isDragging,
      },
    ]"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    @dragover="handleDragOver"
    @drop="handleDrop"
    @click="openFileDialog"
  >
    <div class="absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-white/80 to-transparent dark:via-slate-600/40" />

    <div
      :class="[
        'mb-5 rounded-full p-4 transition-all duration-300',
        isDragging
          ? 'scale-105 bg-primary/15 text-primary'
          : 'bg-slate-100 text-slate-500 group-hover:bg-primary/10 group-hover:text-primary dark:bg-slate-800 dark:text-slate-400',
      ]"
    >
      <slot name="icon">
        <svg
          class="h-12 w-12"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
      </slot>
    </div>

    <div class="max-w-xl">
      <p class="text-lg font-semibold text-slate-900 dark:text-white">
        <slot
          v-if="slots.title"
          name="title"
        />
        <slot
          v-else-if="slots.text"
          name="text"
        />
        <template v-else>
          {{ t('common.dragDrop') }}
        </template>
      </p>

      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
        <slot name="subtitle">
          {{ t('common.or') }} {{ t('common.browse') }}
        </slot>
      </p>

      <p class="mt-3 text-xs font-medium uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">
        {{ helperText }}
      </p>
    </div>

    <div class="mt-6">
      <span class="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
        {{ t('common.privacyBadge') }}
      </span>
    </div>

    <input
      ref="fileInputRef"
      type="file"
      class="hidden"
      :accept="acceptedTypes"
      :multiple="multiple"
      @change="handleFileSelect"
    >

    <div
      v-if="$slots.default"
      class="mt-6 w-full max-w-2xl"
    >
      <slot />
    </div>
  </div>
</template>
