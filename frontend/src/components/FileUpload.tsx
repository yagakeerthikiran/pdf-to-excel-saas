'use client'

import { useState, type FormEvent } from 'react'
import type { User } from '@supabase/supabase-js'

export default function FileUpload({ user }: { user: User }) {
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

    try {
      // 1. Get a pre-signed URL from our API
      const res = await fetch('/api/generate-upload-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': user.id, // Pass the user ID in the header
        },
        body: JSON.stringify({ filename: file.name, contentType: file.type }),
      })

      if (!res.ok) {
        const errorBody = await res.json();
        throw new Error(errorBody.detail || 'Failed to get upload URL.');
      }

      const { url, fields } = await res.json()

      // 2. Upload the file to S3 using the pre-signed URL
      setMessage('Uploading file...')
      const formData = new FormData()
      Object.entries(fields).forEach(([key, value]) => {
        formData.append(key, value as string)
      })
      formData.append('file', file)

      const uploadResponse = await fetch(url, { method: 'POST', body: formData })

      if (!uploadResponse.ok) throw new Error('Upload to S3 failed.')

      setMessage('File uploaded successfully! Starting conversion...')

      // 3. Notify our backend that the file is ready for conversion
      const convertResponse = await fetch('/api/convert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': user.id, // Pass the user ID in the header
        },
        body: JSON.stringify({ fileKey: fields.key }),
      })

      if (!convertResponse.ok) throw new Error('Conversion failed.')

      const { download_url } = await convertResponse.json()

      // Create a clickable link for the download
      const link = document.createElement('a');
      link.href = download_url;
      link.textContent = 'Click here to download your file.';
      link.target = '_blank';
      link.className = 'text-blue-600 hover:underline';

      // Clear the message and append the link
      setMessage('Conversion successful! ');
      // This is a bit of a hack for the message area, a real UI would have a dedicated results spot
      const messageElement = document.querySelector('#message-area');
      if(messageElement) {
        messageElement.innerHTML = 'Conversion successful! ';
        messageElement.appendChild(link);
      } else {
        setMessage(`Conversion successful! Download link: ${download_url}`);
      }


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
      <div id="message-area" className={`mt-4 text-sm ${message.startsWith('Error') ? 'text-red-600' : 'text-green-600'}`}>
          {message}
      </div>
    </div>
  )
}
