<template>
  <button
    class="cyber-btn"
    :class="[variantClass, sizeClass, { 'btn-block': block, 'btn-loading': loading }]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <span v-if="loading" class="btn-spinner"></span>
    <span class="btn-text" :class="{ 'text-hidden': loading }">
      <slot />
    </span>
  </button>
</template>

<script setup>
const props = defineProps({
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'default' },
  block: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['click'])

const variantClass = computed(() => `btn-${props.variant}`)
const sizeClass = computed(() => `btn-${props.size}`)

const handleClick = (e) => {
  if (!props.loading && !props.disabled) {
    emit('click', e)
  }
}
</script>

<style scoped>
.cyber-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: var(--font-body);
  font-weight: 600;
  border: none;
  cursor: pointer;
  border-radius: var(--radius-button);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  white-space: nowrap;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.cyber-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cyber-btn:not(:disabled):active {
  transform: scale(0.97);
}

/* Sizes */
.btn-small {
  padding: 8px 16px;
  font-size: 13px;
  border-radius: 20px;
}

.btn-default {
  padding: 12px 24px;
  font-size: 15px;
}

.btn-large {
  padding: 16px 32px;
  font-size: 16px;
  border-radius: 32px;
}

.btn-block {
  width: 100%;
}

/* Variants */
.btn-primary {
  background: var(--gradient-btn-primary);
  color: #fff;
  box-shadow: 0 4px 20px rgba(255, 0, 110, 0.3);
}

.btn-primary:not(:disabled):hover {
  box-shadow: 0 6px 30px rgba(255, 0, 110, 0.4);
  transform: translateY(-1px);
}

.btn-secondary {
  background: transparent;
  color: var(--neon-cyan);
  border: 1.5px solid var(--neon-cyan);
}

.btn-secondary:not(:disabled):hover {
  background: rgba(0, 245, 212, 0.1);
  box-shadow: 0 0 20px rgba(0, 245, 212, 0.15);
}

.btn-ghost {
  background: transparent;
  color: var(--ink-gray);
  border: 1px solid var(--border-gray);
}

.btn-ghost:not(:disabled):hover {
  color: var(--paper-white);
  border-color: var(--ink-gray);
}

.btn-gold {
  background: var(--gradient-btn-gold);
  color: var(--ink-black);
  box-shadow: 0 4px 20px rgba(255, 214, 10, 0.3);
}

.btn-gold:not(:disabled):hover {
  box-shadow: 0 6px 30px rgba(255, 214, 10, 0.4);
  transform: translateY(-1px);
}

/* Loading */
.btn-loading {
  cursor: wait;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.text-hidden {
  opacity: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
