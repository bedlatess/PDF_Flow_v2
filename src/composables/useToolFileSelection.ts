import { computed, ref, type Ref } from 'vue'

export function useToolFileSelection<T>(initialItems: T[] = []) {
  const selectedItems = ref<T[]>(initialItems) as Ref<T[]>
  const fileError = ref('')

  const hasSelection = computed(() => selectedItems.value.length > 0)

  const setItems = (items: T[]) => {
    selectedItems.value = [...items]
  }

  const appendItems = (items: T[]) => {
    selectedItems.value = [...selectedItems.value, ...items]
  }

  const removeAt = (index: number) => {
    selectedItems.value.splice(index, 1)
  }

  const clearSelection = () => {
    selectedItems.value = []
    fileError.value = ''
  }

  const setFileError = (message: string) => {
    fileError.value = message
  }

  const clearFileError = () => {
    fileError.value = ''
  }

  return {
    selectedItems,
    fileError,
    hasSelection,
    setItems,
    appendItems,
    removeAt,
    clearSelection,
    setFileError,
    clearFileError,
  }
}
