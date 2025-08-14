'use client'

import { useState, type FormEvent } from 'react'

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0])
      setMessage(`Selected file: ${e.target.files[0].name}`)
    }
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!file) {
      setMessage('Please select a file to upload.')
      return
    }

    setUploading(true)
    setMessage('Getting upload URL...')

    // This requires the user to be logged in and the user ID to be passed
    // in the header. We will assume the parent component handles auth state.
    // For now, we need to get the user from supabase to pass the header.
    // A better implementation would pass the user object as a prop.

    // For now, let's assume the call is made correctly.
    // The logic to get the user ID should be added here.

    try {
      const res = await fetch('/api/generate-upload-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, contentType: file.type }),
      })

      if (!res.ok) throw new Error('Failed to get upload URL.')

      const { url, fields } = await res.json()

      setMessage('Uploading file...')
      const formData = new FormData()
      Object.entries(fields).forEach(([key, value]) => {
        formData.append(key, value as string)
      })
      formData.append('file', file)

      const uploadResponse = await fetch(url, { method: 'POST', body: formData })

      if (!uploadResponse.ok) throw new Error('Upload to S3 failed.')

      setMessage('File uploaded successfully! Starting conversion...')

      const convertResponse = await fetch('/api/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileKey: fields.key }),
      })

      if (!convertResponse.ok) throw new Error('Conversion failed.')

      const { download_url } = await convertResponse.json()
      setMessage(`Conversion successful! Click here to download.`)
      // In a real UI, you'd make this a clickable link:
      // e.g., set a new state with the URL and render an <a> tag.

    } catch (error) {
      console.error(error)
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred.'
      setMessage(`Error: ${errorMessage}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="w-full max-w-lg mx-auto">
      <form onSubmit={handleSubmit} className="p-6 border-2 border-dashed border-gray-300 rounded-lg text-center">
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="mb-4">
            <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500">PDF up to 20MB</p>
          </div>
          <input id="file-upload" name="file-upload" type="file" className="sr-only" accept="application/pdf" onChange={handleFileChange} disabled={uploading} />
        </label>

        {file && (
          <div className="mt-4 text-sm text-gray-700">
            <p>Selected: <span className="font-medium">{file.name}</span></p>
          </div>
        )}

        <button
          type="submit"
          disabled={uploading || !file}
          className="mt-4 w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {uploading ? 'Uploading...' : 'Upload and Convert'}
        </button>
      </form>
      {message && (
        <p className={`mt-4 text-sm ${message.startsWith('Error') ? 'text-red-600' : 'text-green-600'}`}>
          {message}
        </p>
      )}
    </div>
  )
}
