<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { getHealth, type HealthPayload } from '@/api/health'

const health = ref<HealthPayload | null>(null)
const loading = ref(false)
const error = ref('')

async function loadHealth() {
  loading.value = true
  error.value = ''

  try {
    const response = await getHealth()
    health.value = response.data
  } catch {
    error.value = '后端健康检查暂不可用'
  } finally {
    loading.value = false
  }
}

onMounted(loadHealth)
</script>

<template>
  <main class="home">
    <section class="shell">
      <div class="title-row">
        <div>
          <p class="eyebrow">GeoRef Studio</p>
          <h1>地理配准工作台</h1>
        </div>
        <el-tag :type="health?.status === 'ok' ? 'success' : 'warning'" effect="plain">
          {{ health?.status ?? 'checking' }}
        </el-tag>
      </div>

      <div class="status-panel">
        <div>
          <span class="label">Backend</span>
          <strong>{{ health?.service ?? 'GeoRef Studio API' }}</strong>
        </div>
        <div>
          <span class="label">Environment</span>
          <strong>{{ health?.environment ?? '-' }}</strong>
        </div>
        <el-button :loading="loading" @click="loadHealth">刷新</el-button>
      </div>

      <el-alert v-if="error" :title="error" type="warning" :closable="false" />
    </section>
  </main>
</template>

<style scoped>
.home {
  min-height: 100vh;
  padding: 32px;
}

.shell {
  max-width: 960px;
  margin: 0 auto;
}

.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #49617d;
  font-size: 14px;
}

h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.2;
  letter-spacing: 0;
}

.status-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 18px;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  background: #ffffff;
}

.label {
  display: block;
  margin-bottom: 6px;
  color: #66788f;
  font-size: 13px;
}

strong {
  overflow-wrap: anywhere;
}

@media (max-width: 720px) {
  .home {
    padding: 20px;
  }

  .title-row,
  .status-panel {
    grid-template-columns: 1fr;
  }

  .title-row {
    display: grid;
  }
}
</style>

