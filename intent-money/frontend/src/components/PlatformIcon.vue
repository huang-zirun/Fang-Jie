<template>
  <img
    v-if="platform === 'douyin' || platform === '抖音'"
    src="../assets/douyin-logo.svg"
    :width="size"
    :height="size"
    alt="抖音"
    class="platform-logo"
  />

  <img
    v-else-if="platform === 'xiaohongshu' || platform === '小红书'"
    src="../assets/xiaohongshu-logo.svg"
    :width="size"
    :height="size"
    alt="小红书"
    class="platform-logo"
  />

  <svg
    v-else
    :width="size"
    :height="size"
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- 默认平台图标 -->
    <rect x="10" y="6" width="28" height="36" rx="4" stroke="#666" stroke-width="3" fill="none" />
    <line x1="18" y1="14" x2="30" y2="14" stroke="#666" stroke-width="2" stroke-linecap="round" />
    <line x1="18" y1="20" x2="30" y2="20" stroke="#666" stroke-width="2" stroke-linecap="round" />
    <line x1="18" y1="26" x2="24" y2="26" stroke="#666" stroke-width="2" stroke-linecap="round" />
  </svg>
</template>

<script setup lang="ts">
interface Props {
  platform: string
  size?: number
}

withDefaults(defineProps<Props>(), {
  size: 48
})
</script>

<style scoped>
.platform-logo {
  object-fit: contain;
}
</style>
