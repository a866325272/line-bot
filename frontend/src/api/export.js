/**
 * 匯出 API 模組
 */

import { apiClient } from './client'

export const exportApi = {
  /**
   * 匯出月份明細到 Google Spreadsheet
   * @param {string} month - 格式 YYYY_MM
   * @returns {Promise<{message: string, sheet_url: string}>}
   */
  exportToSpreadsheet(month) {
    return apiClient.post('/export/spreadsheet', { month })
  },
}
