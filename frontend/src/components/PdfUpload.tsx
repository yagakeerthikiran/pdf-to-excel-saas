'use client'

import { useState, useCallback } from 'react'
import { apiClient } from '@/lib/api'

interface ConversionJob {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress?: number
  downloadUrl?: string
  errorMessage?: string
  fileName: string
}

export default function PdfUpload() {
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<ConversionJob[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const processFile = async (file: File) => {
    if (!file.type.includes('pdf')) {
      alert('Please select a PDF file')
      return
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      alert('File size must be less than 10MB')
      return
    }

    const tempJob: ConversionJob = {
      id: `temp-${Date.now()}`,
      status: 'pending',
      fileName: file.name,
      progress: 0,
    }

    setUploadedFiles(prev => [...prev, tempJob])
    setIsUploading(true)

    try {
      // Upload file and start conversion
      const response = await apiClient.convertPdf(file)
      
      // Update with real job ID
      setUploadedFiles(prev => 
        prev.map(job => 
          job.id === tempJob.id 
            ? { ...job, id: response.job_id, status: 'processing' as const }
            : job
        )
      )

      // Poll for status
      pollJobStatus(response.job_id)

    } catch (error: any) {
      console.error('Upload failed:', error)
      setUploadedFiles(prev => 
        prev.map(job => 
          job.id === tempJob.id 
            ? { ...job, status: 'failed' as const, errorMessage: error.message }
            : job
        )
      )
    } finally {
      setIsUploading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const status = await apiClient.getConversionStatus(jobId)
        
        setUploadedFiles(prev => 
          prev.map(job => 
            job.id === jobId 
              ? { 
                  ...job, 
                  status: status.status,
                  progress: status.progress || job.progress,
                  downloadUrl: status.download_url,
                  errorMessage: status.error_message
                }
              : job
          )
        )

        // Continue polling if still processing
        if (status.status === 'processing' || status.status === 'pending') {
          setTimeout(poll, 2000) // Poll every 2 seconds
        }
      } catch (error) {
        console.error('Status polling failed:', error)
        setUploadedFiles(prev => 
          prev.map(job => 
            job.id === jobId 
              ? { ...job, status: 'failed' as const, errorMessage: 'Status check failed' }
              : job
          )
        )
      }
    }

    poll()
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    files.forEach(processFile)
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    files.forEach(processFile)
    e.target.value = '' // Reset input
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return '⏳'
      case 'processing':
        return '⚡'
      case 'completed':
        return '✅'
      case 'failed':
        return '❌'
      default:
        return '📄'
    }
  }

  const getStatusText = (job: ConversionJob) => {
    switch (job.status) {
      case 'pending':
        return 'Queued for processing...'
      case 'processing':
        return `Converting... ${job.progress || 0}%`
      case 'completed':
        return 'Conversion completed!'
      case 'failed':
        return `Failed: ${job.errorMessage || 'Unknown error'}`
      default:
        return 'Unknown status'
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragOver 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="max-w-md mx-auto">
          <svg
            className="mx-auto h-12 w-12 text-gray-400 mb-4"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Upload your PDF files
          </h3>
          
          <p className="text-sm text-gray-600 mb-4">
            Drag and drop your PDF files here, or click to browse
          </p>
          
          <div className="space-y-2">
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
              disabled={isUploading}
            />
            
            <label
              htmlFor="file-upload"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
            >
              {isUploading ? 'Uploading...' : 'Select PDF Files'}
            </label>
          </div>
          
          <p className="text-xs text-gray-500 mt-2">
            Maximum file size: 10MB per file
          </p>
        </div>
      </div>

      {/* Conversion Jobs List */}
      {uploadedFiles.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-4">Conversion Progress</h3>
          
          <div className="space-y-3">
            {uploadedFiles.map((job) => (
              <div
                key={job.id}
                className="bg-white border rounded-lg p-4 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3 flex-1">
                    <span className="text-2xl">{getStatusIcon(job.status)}</span>
                    
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {job.fileName}
                      </p>
                      <p className="text-sm text-gray-600">
                        {getStatusText(job)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {job.status === 'completed' && job.downloadUrl && (
                      <a
                        href={job.downloadUrl}
                        download
                        className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700"
                      >
                        Download Excel
                      </a>
                    )}
                    
                    {job.status === 'failed' && (
                      <button
                        onClick={() => {
                          // Remove failed job from list
                          setUploadedFiles(prev => prev.filter(f => f.id !== job.id))
                        }}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>
                
                {/* Progress bar for processing jobs */}
                {job.status === 'processing' && job.progress !== undefined && (
                  <div className="mt-3">
                    <div className="bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Usage Tips */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">💡 Tips for best results:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• PDFs with clear, well-formatted tables work best</li>
          <li>• Ensure text is not rotated or skewed</li>
          <li>• For scanned documents, our AI OCR will automatically process them</li>
          <li>• Multiple tables per page are supported</li>
        </ul>
      </div>
    </div>
  )
}
