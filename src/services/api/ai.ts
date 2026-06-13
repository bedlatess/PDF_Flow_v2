import apiClient from '../http'

export const aiAPI = {
  async summarize(file: File, length = 'medium'): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('length', length)

    const response = await apiClient.post('/api/v1/ai/summarize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: { length },
    })
    return response.data
  },

  async ask(file: File, question: string): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('question', question)

    const response = await apiClient.post('/api/v1/ai/ask', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async extract(file: File, dataType = 'general'): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post('/api/v1/ai/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: { data_type: dataType },
    })
    return response.data
  },

  async batchAnalyze(file: File, operations: string[]): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    operations.forEach((operation) => {
      formData.append('operations', operation)
    })

    const response = await apiClient.post('/api/v1/ai/batch-analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}
