/**
 * HTTP Client — 統一 API 呼叫封裝
 * - 自動附加 Authorization header
 * - 401 攔截 → 自動 refresh → 重試
 * - 統一錯誤格式
 */

import { useAuthStore } from '../stores/auth'
import router from '../router'

const BASE_URL = '/line-bot/api'

let isRefreshing = false
let refreshSubscribers = []

function onRefreshed(token) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

function addRefreshSubscriber(cb) {
  refreshSubscribers.push(cb)
}

async function request(method, url, data = null, isRetry = false) {
  const authStore = useAuthStore()

  const headers = {
    'Content-Type': 'application/json',
  }

  if (authStore.accessToken) {
    headers['Authorization'] = `Bearer ${authStore.accessToken}`
  }

  const options = {
    method,
    headers,
    credentials: 'include', // 包含 cookies (refresh token)
  }

  if (data && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(data)
  }

  const response = await fetch(`${BASE_URL}${url}`, options)

  // 處理 401 — 嘗試 refresh
  if (response.status === 401 && !isRetry) {
    if (!isRefreshing) {
      isRefreshing = true
      try {
        const refreshResult = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          credentials: 'include',
        })

        if (refreshResult.ok) {
          const refreshData = await refreshResult.json()
          authStore.setAccessToken(refreshData.access_token)
          isRefreshing = false
          onRefreshed(refreshData.access_token)
          // 重試原始請求
          return request(method, url, data, true)
        } else {
          // Refresh 失敗 → 登出
          isRefreshing = false
          authStore.clearAuth()
          router.push('/login')
          throw new ApiError('登入已過期，請重新登入', 'SESSION_EXPIRED', 401)
        }
      } catch (err) {
        isRefreshing = false
        if (err instanceof ApiError) throw err
        authStore.clearAuth()
        router.push('/login')
        throw new ApiError('登入已過期，請重新登入', 'SESSION_EXPIRED', 401)
      }
    } else {
      // 等待 refresh 完成後重試
      return new Promise((resolve, reject) => {
        addRefreshSubscriber(async (token) => {
          try {
            const result = await request(method, url, data, true)
            resolve(result)
          } catch (err) {
            reject(err)
          }
        })
      })
    }
  }

  // 解析回應
  const responseData = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(
      responseData?.error || '發生未知錯誤',
      responseData?.code || 'UNKNOWN_ERROR',
      response.status,
      responseData?.details
    )
  }

  return responseData
}

export class ApiError extends Error {
  constructor(message, code, status, details = {}) {
    super(message)
    this.code = code
    this.status = status
    this.details = details
  }
}

export const apiClient = {
  get: (url, params) => {
    const queryString = params
      ? '?' + new URLSearchParams(params).toString()
      : ''
    return request('GET', url + queryString)
  },
  post: (url, data) => request('POST', url, data),
  put: (url, data) => request('PUT', url, data),
  delete: (url) => request('DELETE', url),
}
