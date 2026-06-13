import apiClient from '../http'

export const advancedAPI = {
  async protectPDF(file: File, password: string): Promise<Blob> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('password', password)

    const response = await apiClient.post('/api/v1/advanced/protect', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  async unlockPDF(file: File, password: string): Promise<Blob> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('password', password)

    const response = await apiClient.post('/api/v1/advanced/unlock', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  async repairPDF(file: File): Promise<Blob> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post('/api/v1/advanced/repair', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  async getFormFields(file: File): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post('/api/v1/advanced/form/fields', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async fillForm(file: File, formData: Record<string, any>): Promise<Blob> {
    const data = new FormData()
    data.append('file', file)
    data.append('form_data', JSON.stringify(formData))

    const response = await apiClient.post('/api/v1/advanced/form/fill', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  async annotateText(
    file: File,
    text: string,
    page: number,
    x: number,
    y: number,
    color = '#FF0000',
  ): Promise<Blob> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('text', text)
    formData.append('page_number', Math.max(0, page - 1).toString())
    formData.append('x', x.toString())
    formData.append('y', y.toString())
    formData.append('color', color)

    const response = await apiClient.post('/api/v1/advanced/annotate/text', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  async annotateHighlight(
    file: File,
    page: number,
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    color = '#FFFF00',
  ): Promise<Blob> {
    const x = Math.min(x1, x2)
    const y = Math.min(y1, y2)
    const width = Math.abs(x2 - x1)
    const height = Math.abs(y2 - y1)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('page_number', Math.max(0, page - 1).toString())
    formData.append('x', x.toString())
    formData.append('y', y.toString())
    formData.append('width', width.toString())
    formData.append('height', height.toString())
    formData.append('color', color)

    const response = await apiClient.post('/api/v1/advanced/annotate/highlight', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'blob',
    })
    return response.data as Blob
  },

  async addSignatureField(
    file: File,
    page: number,
    x: number,
    y: number,
    width: number,
    height: number,
  ): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('page', page.toString())
    formData.append('x', x.toString())
    formData.append('y', y.toString())
    formData.append('width', width.toString())
    formData.append('height', height.toString())

    const response = await apiClient.post('/api/v1/advanced/signature/field', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async downloadResult(jobId: string, filename: string): Promise<void> {
    const response = await apiClient.get(`/api/v1/files/download/${jobId}`, {
      responseType: 'blob',
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}
