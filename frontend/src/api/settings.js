import { apiClient } from './client'

export const settingsApi = {
  getSettings() {
    return apiClient.get('/settings')
  },
  updateSettings(data) {
    return apiClient.put('/settings', data)
  },
}
