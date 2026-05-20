import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: '',
    userId: '',
    isLoggedIn: false,
  }),
  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem('token', token)
    },
    setUserId(userId: string) {
      this.userId = userId
      localStorage.setItem('userId', userId)
    },
    clearUser() {
      this.token = ''
      this.userId = ''
      this.isLoggedIn = false
      localStorage.removeItem('token')
      localStorage.removeItem('userId')
    },
    loadFromStorage() {
      this.token = localStorage.getItem('token') || ''
      this.userId = localStorage.getItem('userId') || ''
      this.isLoggedIn = !!this.token
    },
  },
})
