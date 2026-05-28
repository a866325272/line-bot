/**
 * 記帳 API 模組
 */

import { apiClient } from './client'

export const accountsApi = {
  /**
   * 查詢月份記帳明細
   * @param {string} month - 格式 YYYY_MM
   */
  getAccounts(month) {
    return apiClient.get('/accounts', month ? { month } : {})
  },

  /**
   * 月帳統計資料
   * @param {string} month - 格式 YYYY_MM
   */
  getSummary(month) {
    return apiClient.get('/accounts/summary', month ? { month } : {})
  },

  /**
   * 新增記帳項目
   * @param {{name: string, amount: number, type: number, date?: string}} data
   */
  createAccount(data) {
    return apiClient.post('/accounts', data)
  },

  /**
   * 編輯單筆記錄
   * @param {string} month
   * @param {number} index
   * @param {{name?: string, amount?: number, type?: number, date?: string}} data
   */
  updateAccount(month, index, data) {
    return apiClient.put(`/accounts/${index}?month=${month}`, data)
  },

  /**
   * 刪除單筆記錄
   * @param {string} month
   * @param {number} index
   */
  deleteAccount(month, index) {
    return apiClient.delete(`/accounts/${index}?month=${month}`)
  },
}
