import { apiClient } from './client'

export const budgetApi = {
  getBudgets() {
    return apiClient.get('/budget')
  },
  getBudgetStatus(month) {
    return apiClient.get('/budget/status', month ? { month } : {})
  },
  setBudget(categoryId, amount) {
    return apiClient.put(`/budget/${categoryId}`, { amount })
  },
}
