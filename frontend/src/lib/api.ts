const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000'

export class ApiClient {
  private baseUrl: string
  private headers: Record<string, string>

  constructor() {
    this.baseUrl = API_BASE_URL
    this.headers = {
      'Content-Type': 'application/json',
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.headers,
        ...options.headers,
      },
    }

    // Add auth header if token exists
    const token = this.getAuthToken()
    if (token) {
      config.headers = {
        ...config.headers,
        'Authorization': `Bearer ${token}`,
      }
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorData}`)
      }

      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      } else {
        return response as unknown as T
      }
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('supabase.auth.token')
    }
    return null
  }

  // Health check
  async health() {
    return this.request<{ status: string; timestamp: string }>('/health')
  }

  // File conversion
  async convertPdf(file: File): Promise<{ job_id: string }> {
    const formData = new FormData()
    formData.append('file', file)

    return this.request<{ job_id: string }>('/api/convert', {
      method: 'POST',
      headers: {}, // Remove default headers for FormData
      body: formData,
    })
  }

  // Check conversion status
  async getConversionStatus(jobId: string) {
    return this.request<{
      status: 'pending' | 'processing' | 'completed' | 'failed'
      progress?: number
      download_url?: string
      error_message?: string
    }>(`/api/convert/${jobId}/status`)
  }

  // Get user conversion history
  async getConversions() {
    return this.request<Array<{
      id: string
      filename: string
      status: string
      created_at: string
      download_url?: string
    }>>('/api/conversions')
  }

  // User profile
  async getProfile() {
    return this.request<{
      id: string
      email: string
      subscription_tier: string
      conversions_remaining: number
      created_at: string
    }>('/api/profile')
  }

  // Stripe checkout
  async createCheckoutSession(priceId: string) {
    return this.request<{ checkout_url: string }>('/api/stripe/checkout', {
      method: 'POST',
      body: JSON.stringify({ price_id: priceId }),
    })
  }

  // Cancel subscription
  async cancelSubscription() {
    return this.request<{ message: string }>('/api/stripe/cancel', {
      method: 'POST',
    })
  }
}

export const apiClient = new ApiClient()
