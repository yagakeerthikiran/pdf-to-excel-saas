import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { filename, contentType } = await request.json()
    
    // Get user ID from Supabase auth (you'll need to implement this)
    const userId = request.headers.get('x-user-id') || 'anonymous'
    
    if (!filename || !contentType) {
      return NextResponse.json({ error: 'Missing filename or content type' }, { status: 400 })
    }

    // Validate file type
    if (contentType !== 'application/pdf') {
      return NextResponse.json({ error: 'Only PDF files are allowed' }, { status: 400 })
    }

    // Call backend service to generate upload URL
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/files/upload-url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.BACKEND_API_KEY}`,
        'X-User-ID': userId
      },
      body: JSON.stringify({ filename, contentType })
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json({ error: errorData.detail || 'Failed to generate upload URL' }, { status: response.status })
    }

    const data = await response.json()
    
    return NextResponse.json({
      fileId: data.file_id,
      uploadUrl: data.upload_url,
      fields: data.fields
    })
  } catch (error) {
    console.error('Upload URL generation error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}