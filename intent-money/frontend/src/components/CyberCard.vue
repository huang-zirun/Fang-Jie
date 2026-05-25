<template>
  <div
    class="cyber-card"
    :class="[variantClass, { 'card-hover': hover }]"
    :style="customStyle"
  >
    <div v-if="glowBorder" class="card-glow" :style="glowStyle"></div>
    <div class="card-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: { type: String, default: 'default' },
  hover: { type: Boolean, default: true },
  glowBorder: { type: Boolean, default: false },
  glowColor: { type: String, default: 'cyan' },
  padding: { type: String, default: '16px' },
})

const variantClass = computed(() => `card-${props.variant}`)

const glowStyle = computed(() => {
  const colors = {
    cyan: 'rgba(0, 245, 212, 0.3)',
    magenta: 'rgba(255, 0, 110, 0.3)',
    gold: 'rgba(255, 214, 10, 0.3)',
    purple: 'rgba(155, 93, 229, 0.3)',
  }
  return {
    borderColor: colors[props.glowColor] || colors.cyan,
    boxShadow: `0 0 15px ${colors[props.glowColor] || colors.cyan}`,
  }
})

const customStyle = computed(() => ({
  padding: props.padding,
}))
</script>

<style scoped>
.cyber-card {
  position: relative;
  background: var(--gradient-card);
  border: 1px solid var(--border-gray);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.card-content {
  position: relative;
  z-index: 2;
}

.card-glow {
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  bottom: -1px;
  border-radius: var(--radius-card);
  border: 1px solid transparent;
  pointer-events: none;
  z-index: 1;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.cyber-card:hover .card-glow {
  opacity: 1;
}

.card-hover:hover {
  transform: translateY(-2px);
  border-color: var(--border-cyan);
  box-shadow: var(--shadow-card), var(--shadow-glow-cyan);
}

/* Variants */
.card-cyan {
  border-color: var(--border-cyan);
}

.card-cyan:hover {
  box-shadow: var(--shadow-card), var(--shadow-glow-cyan);
}

.card-magenta {
  border-color: var(--border-magenta);
}

.card-magenta:hover {
  box-shadow: var(--shadow-card), var(--shadow-glow-magenta);
}

.card-gold {
  border-color: var(--border-gold);
}

.card-gold:hover {
  box-shadow: var(--shadow-card), var(--shadow-glow-gold);
}

.card-ghost {
  background: transparent;
  border-color: transparent;
  box-shadow: none;
}

.card-ghost:hover {
  background: rgba(26, 26, 46, 0.5);
}
</style>
