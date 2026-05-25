<template>
  <nav class="cyber-nav" :class="{ 'nav-glass': glass }">
    <div class="nav-back" @click="handleBack">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
    </div>
    <div class="nav-title">{{ title }}</div>
    <div class="nav-action" v-if="$slots.action">
      <slot name="action" />
    </div>
    <div v-else class="nav-placeholder"></div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  title: { type: String, default: '' },
  glass: { type: Boolean, default: true },
  backPath: { type: String, default: '' }
})

const router = useRouter()

const handleBack = () => {
  if (props.backPath) {
    router.push(props.backPath)
  } else {
    router.back()
  }
}
</script>

<style scoped>
.cyber-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 16px;
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid var(--border-gray);
}

.nav-glass {
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.nav-back {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--paper-white);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.nav-back:hover {
  background: rgba(0, 245, 212, 0.1);
  color: var(--neon-cyan);
}

.nav-back:active {
  transform: scale(0.95);
}

.nav-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--paper-white);
  letter-spacing: 0.5px;
}

.nav-action {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--ink-gray);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.nav-action:hover {
  color: var(--neon-cyan);
  background: rgba(0, 245, 212, 0.1);
}

.nav-placeholder {
  width: 40px;
}
</style>
