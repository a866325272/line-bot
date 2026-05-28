import { apiClient } from './client'

export const categoriesApi = {
  getCategories() {
    return apiClient.get('/categories')
  },
  createCategory(data) {
    return apiClient.post('/categories', data)
  },
  updateCategory(id, data) {
    return apiClient.put(`/categories/${id}`, data)
  },
  deleteCategory(id) {
    return apiClient.delete(`/categories/${id}`)
  },
}
