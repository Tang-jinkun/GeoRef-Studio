<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { artifactDownloadUrl, exportGeoTiff, listExportArtifacts, type ExportArtifact } from '@/api/exports'
import { getProject, type Project } from '@/api/projects'
import AppBar from '@/components/AppBar.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { formatDate, formatSize } from '@/utils/format'

const route = useRoute()
const project = ref<Project | null>(null)
const artifacts = ref<ExportArtifact[]>([])
const loading = ref(false)
const exporting = ref(false)
const error = ref('')

const projectId = computed(() => String(route.params.id))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [projectResponse, artifactsResponse] = await Promise.all([
      getProject(projectId.value),
      listExportArtifacts(projectId.value),
    ])
    project.value = projectResponse.data
    artifacts.value = artifactsResponse.data
  } catch {
    error.value = '导出信息加载失败。'
  } finally {
    loading.value = false
  }
}

async function handleExportGeoTiff() {
  exporting.value = true
  error.value = ''
  try {
    await exportGeoTiff(projectId.value)
    await load()
  } catch {
    error.value = 'GeoTIFF 导出失败，请确认工程已完成配准。'
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <div class="app-bg">
    <AppBar />
    <main class="wrap wrap-wide">
      <nav class="crumbs">
        <RouterLink to="/projects">工程列表</RouterLink><span class="sep">/</span>
        <RouterLink v-if="project" :to="`/projects/${project.id}`">{{ project.name }}</RouterLink>
        <span class="sep">/</span><span>导出成果</span>
      </nav>

      <div class="between export-head">
        <div>
          <div class="eyebrow">EXPORT</div>
          <h1 class="h-page mt-2">导出成果</h1>
        </div>
        <RouterLink class="btn btn-ghost" :to="`/projects/${projectId}`">
          <SvgIcon name="back" :size="16" />返回工程
        </RouterLink>
      </div>

      <section v-if="error" class="callout danger mt-4">
        <SvgIcon name="warn" :size="18" />{{ error }}
      </section>

      <div class="grid export-grid mt-8">
        <section class="card export-card">
          <div class="between">
            <div>
              <h2 class="h-sec">GeoTIFF</h2>
              <p class="muted mt-2">包含坐标系、地理变换矩阵和空间参考。</p>
            </div>
            <span class="badge accent"><span class="dot"></span>核心成果</span>
          </div>
          <div class="dl mt-6">
            <dt>坐标系</dt><dd>EPSG:4326</dd>
            <dt>变换方式</dt><dd>Affine Transformation</dd>
            <dt>当前 RMS</dt><dd>{{ project?.rms_error ?? '-' }}</dd>
          </div>
          <button
            class="btn btn-primary mt-6"
            :disabled="exporting || loading || project?.status === '未配准'"
            @click="handleExportGeoTiff"
          >
            <SvgIcon name="download" :size="16" />{{ exporting ? '正在导出...' : '导出 GeoTIFF' }}
          </button>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h2 class="h-sec">成果列表</h2>
            <button class="btn btn-ghost btn-sm" @click="load"><SvgIcon name="refresh" :size="16" />刷新</button>
          </div>
          <div v-if="artifacts.length === 0" class="state">
            <span class="glyph"><SvgIcon name="file" :size="30" /></span>
            <h3>还没有成果</h3>
            <p>完成配准后可以生成 GeoTIFF 成果。</p>
          </div>
          <table v-else class="table">
            <thead><tr><th>类型</th><th>文件名</th><th>大小</th><th>生成时间</th><th style="text-align:right">操作</th></tr></thead>
            <tbody>
              <tr v-for="artifact in artifacts" :key="artifact.id">
                <td><span class="badge ok"><span class="dot"></span>{{ artifact.artifact_type }}</span></td>
                <td class="mono artifact-name">{{ artifact.file_name }}</td>
                <td>{{ formatSize(artifact.size_bytes) }}</td>
                <td class="table-num">{{ formatDate(artifact.create_time) }}</td>
                <td><div class="actions"><a class="btn btn-primary btn-sm" :href="artifactDownloadUrl(artifact.id)">下载</a></div></td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.export-head {
  align-items: flex-start;
}
.export-grid {
  grid-template-columns: 360px 1fr;
  align-items: start;
}
.export-card {
  padding: var(--space-6);
}
.artifact-name {
  font-size: var(--text-xs);
}
@media (max-width: 900px) {
  .export-grid {
    grid-template-columns: 1fr;
  }
}
</style>
