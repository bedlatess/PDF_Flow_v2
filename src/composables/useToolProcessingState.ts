import { ref } from 'vue'

export function useToolProcessingState() {
  const isProcessing = ref(false)
  const processingProgress = ref(0)
  const processingStatus = ref('')
  const processingError = ref('')

  const startProcessing = (status = '') => {
    isProcessing.value = true
    processingProgress.value = 0
    processingStatus.value = status
    processingError.value = ''
  }

  const updateProcessing = (progress: number, status?: string) => {
    processingProgress.value = Math.max(0, Math.min(100, progress))
    if (status !== undefined) {
      processingStatus.value = status
    }
  }

  const finishProcessing = (status = '') => {
    processingProgress.value = 100
    processingStatus.value = status
    isProcessing.value = false
  }

  const failProcessing = (message: string) => {
    processingError.value = message
    isProcessing.value = false
  }

  const resetProcessing = () => {
    isProcessing.value = false
    processingProgress.value = 0
    processingStatus.value = ''
    processingError.value = ''
  }

  const setProcessingError = (message: string) => {
    processingError.value = message
  }

  const clearProcessingError = () => {
    processingError.value = ''
  }

  return {
    isProcessing,
    processingProgress,
    processingStatus,
    processingError,
    startProcessing,
    updateProcessing,
    finishProcessing,
    failProcessing,
    resetProcessing,
    setProcessingError,
    clearProcessingError,
  }
}
