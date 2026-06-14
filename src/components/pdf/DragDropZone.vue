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

const { t } = useI18n()
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

  const formatList = (types: string) => t('common.dragDropZone.helper.format', {
    types,
    size: props.maxSize,
  })

  if (props.accept === 'pdf') {
    return formatList('PDF')
  }

  if (props.accept === 'image') {
    return formatList('PNG, JPG, WEBP')
  }

  if (props.accept === 'all') {
    return t('common.dragDropZone.helper.pdfAndImages', { size: props.maxSize })
  }

  if (extensionTokens.length > 0) {
    return formatList(extensionTokens.join(', '))
  }

  return t('common.dragDropZone.helper.files', { size: props.maxSize })
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
    emit('error', t('common.dragDropZone.errors.maxFiles', { count: props.maxFiles }))
    return
  }

  const validFiles: File[] = []

  for (const file of files) {
    const fileSizeMB = file.size / (1024 * 1024)
    if (fileSizeMB > props.maxSize) {
      emit('error', t('common.dragDropZone.errors.fileTooLarge', {
        file: file.name,
        size: props.maxSize,
      }))
      continue
    }

    const isValid = await validateFile(file)
    if (!isValid) {
      emit('error', t('common.dragDropZone.errors.unsupportedType', { file: file.name }))
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
    role="button"
    tabindex="0"
    :class="[
      'group relative grid min-h-[184px] cursor-pointer overflow-hidden rounded-lg border border-dashed px-5 py-5 text-left transition-all duration-200 md:grid-cols-[1fr_auto] md:items-center md:gap-5',
      'border-slate-300 bg-white/90 shadow-sm hover:border-primary/60 hover:bg-white hover:shadow-md',
      'dark:border-slate-700 dark:bg-slate-900/90 dark:hover:border-primary/50 dark:hover:bg-slate-900',
      {
        'border-primary bg-primary/5 shadow-lg shadow-primary/10 dark:bg-primary/10': isDragging,
      },
    ]"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    @dragover="handleDragOver"
    @drop="handleDrop"
    @click="openFileDialog"
    @keydown.enter.prevent="openFileDialog"
    @keydown.space.prevent="openFileDialog"
  >
    <div class="flex items-start gap-4">
      <div
        :class="[
          'flex h-12 w-12 shrink-0 items-center justify-center rounded-md transition-all duration-200',
          isDragging
            ? 'scale-105 bg-primary/15 text-primary'
            : 'bg-slate-100 text-slate-500 group-hover:bg-primary/10 group-hover:text-primary dark:bg-slate-800 dark:text-slate-300',
        ]"
      >
        <slot name="icon">
          <svg
            class="h-7 w-7"
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

      <div class="min-w-0">
        <p class="text-base font-semibold text-slate-950 dark:text-white sm:text-lg">
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

        <p class="mt-1.5 text-sm leading-6 text-slate-500 dark:text-slate-300">
          <slot name="subtitle">
            {{ t('common.or') }} {{ t('common.browse') }}
          </slot>
        </p>

        <p class="mt-2 text-xs font-medium text-slate-400 dark:text-slate-500">
          {{ helperText }}
        </p>
      </div>
    </div>

    <div class="mt-5 flex flex-col gap-2 md:mt-0 md:min-w-44 md:items-end">
      <span
        class="inline-flex min-h-11 items-center justify-center rounded-md bg-slate-950 px-5 text-sm font-semibold text-white shadow-sm transition-colors group-hover:bg-primary focus:outline-none focus:ring-2 focus:ring-primary/40 dark:bg-white dark:text-slate-950 dark:group-hover:bg-primary dark:group-hover:text-white"
      >
        {{ t('common.browse') }}
      </span>
      <span class="text-xs text-slate-400">
        {{ multiple ? t('common.dragDropZone.helper.multiple') : t('common.dragDropZone.helper.single') }}
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
      class="mt-5 w-full max-w-2xl"
    >
      <slot />
    </div>
  </div>
</template>
