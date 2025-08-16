import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { fileId } = await request.json()
    
    // Get user ID from Supabase auth
    const userId = request.headers.get('x-user-id') || 'anonymous'
    
    if (!fileId) {
      return NextResponse.json({ error: 'Missing file ID' }, { status: 400 })
    }

    // Call backend service to confirm upload and start conversion
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/files/confirm-upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.BACKEND_API_KEY}`,
        'X-User-ID': userId
      },
      body: JSON.stringify({ fileId })
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json({ error: errorData.detail || 'Failed to confirm upload' }, { status: response.status })
    }

    const data = await response.json()
    
    return NextResponse.json({
      fileId: data.file_id,
      jobId: data.job_id,
      status: data.status,
      message: 'Upload confirmed. Conversion started.'
    })
  } catch (error) {
    console.error('Upload confirmation error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function GET(request: NextRequest) {
  try {
    // Get user ID from Supabase auth
    const userId = request.headers.get('x-user-id') || 'anonymous'
    
    const url = new URL(request.url)
    const limit = parseInt(url.searchParams.get('limit') || '20')
    const offset = parseInt(url.searchParams.get('offset') || '0')

    // Call backend service to get user files
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/files?limit=${limit}&offset=${offset}`, {
      headers: {
        'Authorization': `Bearer ${process.env.BACKEND_API_KEY}`,
        'X-User-ID': userId
      }
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json({ error: errorData.detail || 'Failed to fetch files' }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Files fetch error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}