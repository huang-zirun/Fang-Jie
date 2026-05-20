import axios from 'axios'

const request = axios.create({
  baseURL: '/api/v1',
})

const authRequest = axios.create({
  baseURL: '/api/v1',
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        const res = await authRequest.post('/auth/anonymous')
        const { token, user_id } = res.data
        localStorage.setItem('token', token)
        localStorage.setItem('userId', user_id)
        if (error.config) {
          error.config.headers.Authorization = `Bearer ${token}`
          return request(error.config)
        }
      } catch {
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

export default request
