import { defineStore } from 'pinia'
import api from '../api/client.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('soar_token') || null,
    user: localStorage.getItem('soar_user') ? { username: localStorage.getItem('soar_user') } : null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(username, password) {
      const { data } = await api.post('/auth/login', { username, password })
      this.token = data.access_token
      this.user = { username }
      localStorage.setItem('soar_token', data.access_token)
      localStorage.setItem('soar_user', username)
    },
    async register(username, password) {
      await api.post('/auth/register', { username, password })
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('soar_token')
      localStorage.removeItem('soar_user')
    },
  },
})
