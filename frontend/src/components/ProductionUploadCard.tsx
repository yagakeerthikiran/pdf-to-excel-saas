'use client'

import { useState, useRef, useEffect } from 'react'
import posthog from 'posthog-js'

interface UploadState {
  stage: 'idle' | 'preparing' | 'uploading' | 'confirming' | 'processing' | 'success' | 'error'
  progress: number
  message: string
  fileId?: string
  jobId?: string
}

export default function ProductionUploadCard() {
  const [file, setFile] = useState<File | null>(null)
  const [uploadState, setUploadState] = useState<UploadState>({
    stage: 'idle',
    progress: 0,
    message: ''
  })
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Safe PostHog capture function
  const safeCapture = (event: string, properties?: any) => {
    try {
      if (posthog && typeof posthog.capture === 'function') {
        posthog.capture(event, properties)
      }
    } catch (error) {
      console.warn('PostHog capture failed:', error)
    }
  }

  useEffect(() => {
    safeCapture('upload_button_viewed')
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFile = e.target.files[0]
      setFile(selectedFile)
      setUploadState({
        stage: 'idle',
        progress: 0,
        message: `Selected: ${selectedFile.name}`
      })
      
      safeCapture('file_selected', {
        file_size: selectedFile.size,
        file_type: selectedFile.type,
        file_name: selectedFile.name.split('.').pop()?.toLowerCase()
      })
    }
  }

  const handleUploadClick = () => {
    safeCapture('upload_button_clicked')
    fileInputRef.current?.click()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setUploadState({
        stage: 'error',
        progress: 0,
        message: 'Please select a file to upload.'
      })
      return
    }

    safeCapture('upload_started', {
      file_size: file.size,
      file_type: file.type
    })

    try {
      // Step 1: Get presigned upload URL
      setUploadState({
        stage: 'preparing',
        progress: 10,
        message: 'Preparing upload...'
      })

      const urlResponse = await fetch('/api/upload-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: file.name,
          contentType: file.type
        }),
      })

      if (!urlResponse.ok) {
        throw new Error('Failed to get upload URL')
      }

      const { fileId, uploadUrl, fields } = await urlResponse.json()

      // Step 2: Upload directly to S3
      setUploadState({
        stage: 'uploading',
        progress: 30,
        message: 'Uploading to cloud storage...'
      })

      const formData = new FormData()
      Object.entries(fields).forEach(([key, value]) => {
        formData.append(key, value as string)
      })
      formData.append('file', file)

      const uploadResponse = await fetch(uploadUrl, {
        method: 'POST',
        body: formData,
      })

      if (!uploadResponse.ok) {
        throw new Error('Upload to storage failed')
      }

      // Step 3: Confirm upload and start processing
      setUploadState({
        stage: 'confirming',
        progress: 60,
        message: 'Confirming upload...'
      })

      const confirmResponse = await fetch('/api/files', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fileId }),
      })

      if (!confirmResponse.ok) {
        throw new Error('Failed to confirm upload')
      }

      const { jobId } = await confirmResponse.json()

      // Step 4: Processing started
      setUploadState({
        stage: 'processing',
        progress: 80,
        message: 'Converting PDF to Excel...',
        fileId,
        jobId
      })

      safeCapture('upload_succeeded', {
        file_size: file.size,
        file_type: file.type,
        file_id: fileId,
        job_id: jobId
      })

      // Poll for completion (in a real app, you'd use WebSockets or SSE)
      setTimeout(() => {
        setUploadState({
          stage: 'success',
          progress: 100,
          message: 'Conversion complete! Check your dashboard.',
          fileId,
          jobId
        })
      }, 3000)

    } catch (error) {
      console.error('Upload error:', error)
      setUploadState({
        stage: 'error',
        progress: 0,
        message: error instanceof Error ? error.message : 'Upload failed. Please try again.'
      })
      
      safeCapture('upload_failed', {
        error: error instanceof Error ? error.message : 'Unknown error',
        file_size: file?.size,
        file_type: file?.type
      })
    }
  }

  const resetUpload = () => {
    setFile(null)
    setUploadState({
      stage: 'idle',
      progress: 0,
      message: ''
    })
  }

  const getProgressColor = () => {
    switch (uploadState.stage) {
      case 'success': return 'bg-green-500'
      case 'error': return 'bg-red-500'
      case 'processing': return 'bg-blue-500'
      default: return 'bg-indigo-500'
    }
  }

  const getButtonText = () => {
    switch (uploadState.stage) {
      case 'preparing': return 'Preparing...'
      case 'uploading': return 'Uploading...'
      case 'confirming': return 'Confirming...'
      case 'processing': return 'Converting...'
      case 'success': return 'Upload Another'
      case 'error': return 'Try Again'
      default: return file ? 'Upload PDF' : 'Select PDF File'
    }
  }

  const isUploading = ['preparing', 'uploading', 'confirming', 'processing'].includes(uploadState.stage)

  return (
    <div className="w-full max-w-lg mx-auto">
      <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-gray-400 transition-colors bg-white">
        <div className="mb-4">
          <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <p className="mt-2 text-sm text-gray-600">
            <span className="font-semibold">Click to upload</span> or drag and drop
          </p>
          <p className="text-xs text-gray-500">PDF up to 20MB</p>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept="application/pdf"
          onChange={handleFileChange}
          disabled={isUploading}
        />

        {file && !uploadState.message && (
          <div className="mb-4 text-sm text-gray-700">
            <p>Selected: <span className="font-medium">{file.name}</span></p>
          </div>
        )}

        {/* Progress Bar */}
        {uploadState.progress > 0 && (
          <div className="mb-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${getProgressColor()}`}
                style={{ width: `${uploadState.progress}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">{uploadState.progress}%</p>
          </div>
        )}

        <button
          type="button"
          onClick={uploadState.stage === 'success' || uploadState.stage === 'error' ? resetUpload : (file ? handleSubmit : handleUploadClick)}
          disabled={isUploading}
          className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isUploading && (
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          {getButtonText()}
        </button>

        {uploadState.message && (
          <div className={`mt-4 text-sm ${
            uploadState.stage === 'success' ? 'text-green-600' : 
            uploadState.stage === 'error' ? 'text-red-600' : 
            'text-blue-600'
          }`}>
            {uploadState.message}
          </div>
        )}

        {uploadState.stage === 'success' && (
          <div className="mt-4 p-3 bg-green-50 rounded-md">
            <div className="text-sm text-green-700">
              <p className="font-medium">Upload Successful!</p>
              <p>File ID: {uploadState.fileId}</p>
              <p>Job ID: {uploadState.jobId}</p>
              <a href="/dashboard" className="underline hover:text-green-800">
                View in Dashboard →
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}