'use client'

import { useState, useRef } from 'react'
import posthog from 'posthog-js'

export default function UploadCard() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFile = e.target.files[0]
      setFile(selectedFile)
      setMessage(`Selected file: ${selectedFile.name}`)
      
      // PostHog event
      posthog.capture('file_selected', {
        file_size: selectedFile.size,
        file_type: selectedFile.type,
        file_name: selectedFile.name.split('.').pop()?.toLowerCase()
      })
    }
  }

  const handleUploadClick = () => {
    posthog.capture('upload_button_clicked')
    fileInputRef.current?.click()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setMessage('Please select a file to upload.')
      return
    }

    setUploading(true)
    posthog.capture('upload_started', {
      file_size: file.size,
      file_type: file.type
    })

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const result = await response.json()
      setMessage('File uploaded successfully!')
      
      posthog.capture('upload_succeeded', {
        file_size: file.size,
        file_type: file.type
      })
    } catch (error) {
      console.error('Upload error:', error)
      setMessage('Upload failed. Please try again.')
      
      posthog.capture('upload_failed', {
        error: error instanceof Error ? error.message : 'Unknown error',
        file_size: file.size,
        file_type: file.type
      })
    } finally {
      setUploading(false)
    }
  }

  // Track when upload button is viewed
  const handleCardView = () => {
    posthog.capture('upload_button_viewed')
  }

  return (
    <div className="w-full max-w-lg mx-auto" onLoad={handleCardView}>
      <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-gray-400 transition-colors">
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
          disabled={uploading}
        />

        {file && (
          <div className="mb-4 text-sm text-gray-700">
            <p>Selected: <span className="font-medium">{file.name}</span></p>
          </div>
        )}

        <button
          type="button"
          onClick={file ? handleSubmit : handleUploadClick}
          disabled={uploading}
          className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {uploading ? 'Uploading...' : file ? 'Upload PDF' : 'Select PDF File'}
        </button>

        {message && (
          <div className={`mt-4 text-sm ${message.includes('successfully') ? 'text-green-600' : message.includes('failed') || message.includes('error') ? 'text-red-600' : 'text-gray-600'}`}>
            {message}
          </div>
        )}
      </div>
    </div>
  )
}