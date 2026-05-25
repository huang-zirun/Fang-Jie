<template>
  <div class="app-container">
    <ParticleBackground />
    <div class="scanlines"></div>
    <router-view v-slot="{ Component }">
      <transition name="page-slide" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { initTracker, trackPageView } from './utils/tracker'
import ParticleBackground from './components/ParticleBackground.vue'

const router = useRouter()

onMounted(() => {
  initTracker()
})

router.afterEach((to) => {
  trackPageView(to.path)
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: var(--ink-black);
  position: relative;
}

.scanlines {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 9998;
  opacity: 0.03;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 245, 212, 0.03) 2px,
    rgba(0, 245, 212, 0.03) 4px
  );
}

.page-slide-enter-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 1, 1);
}

.page-slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.page-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
