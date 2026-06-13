import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import DragDropZone from '@/components/pdf/DragDropZone.vue'

const createTestI18n = () => createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      common: {
        dragDrop: 'Drag and drop files here',
        or: 'or',
        browse: 'browse',
        dragDropZone: {
          helper: {
            format: '{types} up to {size} MB',
            pdfAndImages: 'PDF and images up to {size} MB',
            files: 'Files up to {size} MB',
            single: 'Choose one file',
            multiple: 'Multiple files supported',
          },
          errors: {
            maxFiles: 'Upload up to {count} files',
            fileTooLarge: '{file} is larger than {size} MB',
            unsupportedType: '{file} is not supported',
          },
        },
      },
    },
  },
})

const mountZone = (props = {}) => mount(DragDropZone, {
  props,
  global: {
    plugins: [createTestI18n()],
  },
})

describe('DragDropZone Component', () => {
  it('renders default upload copy and helper text', () => {
    const wrapper = mountZone()

    expect(wrapper.text()).toContain('Drag and drop files here')
    expect(wrapper.text()).toContain('or browse')
    expect(wrapper.text()).toContain('PDF up to 100 MB')
  })

  it('accepts PDF files by MIME type and extension', () => {
    const wrapper = mountZone({ accept: 'pdf' })

    const input = wrapper.find('input[type="file"]')
    expect(input.attributes('accept')).toBe('application/pdf,.pdf')
  })

  it('supports multiple file upload', () => {
    const wrapper = mountZone({ multiple: true })

    const input = wrapper.find('input[type="file"]')
    expect(input.attributes('multiple')).toBeDefined()
  })

  it('shows drag active styling while dragging', async () => {
    const wrapper = mountZone()

    await wrapper.trigger('dragenter')

    expect(wrapper.classes()).toContain('border-primary')
    expect(wrapper.classes()).toContain('bg-primary/5')
  })

  it('removes drag active styling on drag leave', async () => {
    const wrapper = mountZone()

    await wrapper.trigger('dragenter')
    await wrapper.trigger('dragleave')

    expect(wrapper.classes()).not.toContain('bg-primary/5')
  })

  it('shows configured file size limit', () => {
    const wrapper = mountZone({ maxSize: 50 })

    expect(wrapper.text()).toContain('PDF up to 50 MB')
  })

  it('shows multiple file helper text', () => {
    const wrapper = mountZone()

    expect(wrapper.text()).toContain('Multiple files supported')
  })
})
