/**
 * 認證 API 模組
 */

import { apiClient } from './client'

export const authApi = {
  /**
   * 使用者登入
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{access_token: string, user: object}>}
   */
  login(username, password) {
    return apiClient.post('/auth/login', { username, password })
  },

  /**
   * 使用者註冊
   * @param {string} username
   * @param {string} password
   * @param {string|null} firestoreDocId - 選填，綁定現有 document
   * @returns {Promise<{access_token: string, user: object}>}
   */
  register(username, password, firestoreDocId = null) {
    const data = { username, password }
    if (firestoreDocId) {
      data.firestore_doc_id = firestoreDocId
    }
    return apiClient.post('/auth/register', data)
  },

  /**
   * 刷新 Access Token
   * @returns {Promise<{access_token: string}>}
   */
  async refresh() {
    const response = await fetch('/line-bot/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error('Refresh failed')
    }
    return response.json()
  },

  /**
   * 登出
   */
  logout() {
    return apiClient.post('/auth/logout')
  },

  /**
   * 取得當前使用者資訊
   * @returns {Promise<{id: string, username: string, firestore_doc_id: string}>}
   */
  getMe() {
    return apiClient.get('/auth/me')
  },
}
