import { createRouter, createWebHistory } from 'vue-router'
import IntentSelect from '../views/IntentSelect.vue'
import PlatformSelect from '../views/PlatformSelect.vue'
import TaskDetail from '../views/TaskDetail.vue'
import DataReport from '../views/DataReport.vue'
import TaskHistory from '../views/TaskHistory.vue'
import Admin from '../views/Admin.vue'
import AccountManage from '../views/AccountManage.vue'
import { useUserStore } from '../stores/user'
import { anonymousRegister } from '../api/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: IntentSelect },
    { path: '/platform/:intentId', component: PlatformSelect },
    { path: '/task/:id', component: TaskDetail },
    { path: '/report/:id', component: DataReport },
    { path: '/history', component: TaskHistory },
    { path: '/admin', component: Admin },
    { path: '/accounts', component: AccountManage },
  ],
})

router.beforeEach(async () => {
  const userStore = useUserStore()
  userStore.loadFromStorage()

  if (!userStore.token) {
    try {
      const res = await anonymousRegister()
      userStore.setToken(res.data.token)
      userStore.setUserId(res.data.user_id)
    } catch {
      // proceed anyway
    }
  }
})

export default router
