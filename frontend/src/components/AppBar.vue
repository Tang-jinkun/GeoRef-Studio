<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { getHealth } from '@/api/health'
import SvgIcon from '@/components/SvgIcon.vue'

const online = ref<boolean | null>(null)

async function refreshHealth() {
  try {
    await getHealth()
    online.value = true
  } catch {
    online.value = false
  }
}

onMounted(() => {
  void refreshHealth()
})
</script>

<template>
  <header class="appbar">
    <RouterLink class="brand" to="/projects" title="GeoRef Studio">
      <span class="bolt"><SvgIcon name="target" :size="24" /></span>
      <span>GeoRef Studio <small>影像配准</small></span>
    </RouterLink>
    <div class="appbar-spacer"></div>
    <span v-if="online !== null" class="conn" :class="{ bad: !online }" title="后端连接状态">
      <span class="dot"></span>{{ online ? '后端连接正常' : '后端连接异常' }}
    </span>
    <button class="btn btn-ghost btn-sm" @click="refreshHealth">
      <SvgIcon name="refresh" :size="16" />刷新
    </button>
    <RouterLink class="btn btn-primary btn-sm" to="/projects/new">
      <SvgIcon name="plus" :size="16" />新建工程
    </RouterLink>
  </header>
</template>
