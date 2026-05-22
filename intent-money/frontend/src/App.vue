<template>
  <router-view v-slot="{ Component }">
    <transition name="page" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { initTracker, trackPageView } from './utils/tracker'

const router = useRouter()

onMounted(() => {
  initTracker()
})

router.afterEach((to) => {
  trackPageView(to.path)
})
</script>

<style>
.page-enter-active {
  transition: all 0.3s ease-out;
}

.page-leave-active {
  transition: all 0.15s ease-in;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-leave-to {
  opacity: 0;
}
</style>
