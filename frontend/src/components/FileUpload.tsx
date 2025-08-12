'use client'

import { useState, type FormEvent } from 'react'

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0])
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
      const res = await fetch('/api/generate-upload-url', { // Using Next.js rewrite for backend proxy
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, contentType: file.type }),
      })

      if (!res.ok) throw new Error('Failed to get upload URL.')

      const { url, fields } = await res.json()

      // 2. Upload the file to S3 using the pre-signed URL
      setMessage('Uploading file...')
      const formData = new FormData()
      Object.entries(fields).forEach(([key, value]) => {
        formData.append(key, value as string)
      })
      formData.append('file', file)

      const uploadResponse = await fetch(url, {
        method: 'POST',
        body: formData,
      })

      if (!uploadResponse.ok) throw new Error('Upload to S3 failed.')

      setMessage('File uploaded successfully! Starting conversion...')

      // 3. Notify our backend that the file is ready for conversion
      const convertResponse = await fetch('/api/convert', { // Using Next.js rewrite
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileKey: fields.key }), // Pass the S3 key to the backend
      })

      if (!convertResponse.ok) throw new Error('Conversion failed.')

      const { download_url } = await convertResponse.json()
      setMessage(`Conversion successful! Download your file: ${download_url}`)

    } catch (error) {
      console.error(error)
      setMessage(error instanceof Error ? error.message : 'An unknown error occurred.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="application/pdf" onChange={handleFileChange} disabled={uploading} />
        <button type="submit" disabled={uploading}>
          {uploading ? 'Uploading...' : 'Upload and Convert'}
        </button>
      </form>
      {message && <p>{message}</p>}
    </div>
  )
}
