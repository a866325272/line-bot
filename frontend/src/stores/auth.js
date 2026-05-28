/**
 * Auth Store — 認證狀態管理 (Pinia)
 */

import { defineStore } from 'pinia'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: null,
    isAuthenticated: false,
    loading: false,
  }),

  actions: {
    /**
     * 使用者登入
     */
    async login(username, password) {
      this.loading = true
      try {
        const result = await authApi.login(username, password)
        this.accessToken = result.access_token
        this.user = result.user
        this.isAuthenticated = true
        return result
      } finally {
        this.loading = false
      }
    },

    /**
     * 使用者註冊
     */
    async register(username, password, firestoreDocId = null) {
      this.loading = true
      try {
        const result = await authApi.register(username, password, firestoreDocId)
        this.accessToken = result.access_token
        this.user = result.user
        this.isAuthenticated = true
        return result
      } finally {
        this.loading = false
      }
    },

    /**
     * 登出
     */
    async logout() {
      try {
        await authApi.logout()
      } catch {
        // 即使 API 失敗也清除本地狀態
      }
      this.clearAuth()
    },

    /**
     * 嘗試恢復登入狀態（App 啟動時呼叫）
     */
    async tryRestore() {
      try {
        const refreshResult = await authApi.refresh()
        this.accessToken = refreshResult.access_token
        const user = await authApi.getMe()
        this.user = user
        this.isAuthenticated = true
      } catch {
        this.clearAuth()
      }
    },

    /**
     * 設定 Access Token（refresh 後呼叫）
     */
    setAccessToken(token) {
      this.accessToken = token
    },

    /**
     * 清除認證狀態
     */
    clearAuth() {
      this.user = null
      this.accessToken = null
      this.isAuthenticated = false
    },
  },
})
