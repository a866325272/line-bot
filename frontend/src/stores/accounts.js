/**
 * Account Store — 記帳資料狀態管理 (Pinia)
 */

import { defineStore } from 'pinia'
import { accountsApi } from '../api/accounts'

/**
 * 取得當月 YYYY_MM
 */
function getCurrentMonth() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  return `${year}_${month}`
}

export const useAccountStore = defineStore('accounts', {
  state: () => ({
    currentMonth: getCurrentMonth(),
    accounts: [],
    summary: null,
    loading: false,
  }),

  actions: {
    /**
     * 查詢月份明細
     */
    async fetchAccounts(month = null) {
      this.loading = true
      try {
        const targetMonth = month || this.currentMonth
        const result = await accountsApi.getAccounts(targetMonth)
        this.accounts = result.accounts
        this.currentMonth = result.month
        return result
      } finally {
        this.loading = false
      }
    },

    /**
     * 查詢月帳統計
     */
    async fetchSummary(month = null) {
      const targetMonth = month || this.currentMonth
      const result = await accountsApi.getSummary(targetMonth)
      this.summary = result
      return result
    },

    /**
     * 新增記帳
     */
    async createAccount(data) {
      const result = await accountsApi.createAccount(data)
      // 重新載入當月資料
      await this.fetchAccounts(this.currentMonth)
      return result
    },

    /**
     * 編輯記錄
     */
    async updateAccount(month, index, data) {
      const result = await accountsApi.updateAccount(month, index, data)
      // 重新載入資料
      await this.fetchAccounts(month)
      return result
    },

    /**
     * 刪除記錄
     */
    async deleteAccount(month, index) {
      await accountsApi.deleteAccount(month, index)
      // 重新載入資料
      await this.fetchAccounts(month)
    },

    /**
     * 切換月份
     */
    setMonth(month) {
      this.currentMonth = month
    },
  },
})
