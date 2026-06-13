import apiClient from '../http'

export interface FileUploadResponse {
  file_id: string
  filename: string
  size: number
  mime_type: string
  upload_time: number
}

export interface ProcessingJobResponse {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  message?: string
  progress?: number
  result_url?: string
  error?: string
}

export interface JobStatusResponse {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: number
  updated_at: number
  progress?: number
  result?: any
  error?: string
}

export const fileAPI = {
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<FileUploadResponse>('/api/v1/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    return response.data
  },

  async mergePDFs(fileIds: string[], outputFilename?: string): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/merge', {
      file_ids: fileIds,
      output_filename: outputFilename,
    })
    return response.data
  },

  async splitPDF(fileId: string, pageRanges: number[][]): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/split', {
      file_id: fileId,
      page_ranges: pageRanges,
    })
    return response.data
  },

  async compressPDF(
    fileId: string,
    quality: 'low' | 'medium' | 'high',
  ): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/compress', {
      file_id: fileId,
      quality,
    })
    return response.data
  },

  async rotatePDF(fileId: string, rotation: 90 | 180 | 270): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/rotate', {
      file_id: fileId,
      rotation,
    })
    return response.data
  },

  async imagesToPDF(fileIds: string[], outputFilename?: string): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/images-to-pdf', {
      file_ids: fileIds,
      output_filename: outputFilename,
    })
    return response.data
  },

  async pdfToImages(fileId: string, format: 'png' | 'jpeg' = 'png'): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/pdf-to-images', {
      file_id: fileId,
      format,
    })
    return response.data
  },

  async extractTextOCR(fileId: string, language = 'eng'): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>('/api/v1/files/ocr', {
      file_id: fileId,
      language,
    })
    return response.data
  },

  async officeToPDF(formData: FormData): Promise<ProcessingJobResponse> {
    const response = await apiClient.post<ProcessingJobResponse>(
      '/api/v1/files/office-to-pdf',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      },
    )
    return response.data
  },

  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await apiClient.get<JobStatusResponse>(`/api/v1/files/jobs/${jobId}`)
    return response.data
  },

  async downloadResult(jobId: string): Promise<Blob> {
    const response = await apiClient.get(`/api/v1/files/download/${jobId}`, {
      responseType: 'blob',
    })
    return response.data as Blob
  },

  async pollJobUntilDone(
    jobId: string,
    onProgress?: (status: JobStatusResponse) => void,
    intervalMs = 1500,
    maxAttempts = 80,
  ): Promise<JobStatusResponse> {
    for (let i = 0; i < maxAttempts; i++) {
      const status = await this.getJobStatus(jobId)
      onProgress?.(status)
      if (status.status === 'completed' || status.status === 'failed') {
        return status
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs))
    }
    throw new Error('Job polling timed out')
  },

  async cancelJob(jobId: string): Promise<void> {
    await apiClient.delete(`/api/v1/files/jobs/${jobId}`)
  },
}
