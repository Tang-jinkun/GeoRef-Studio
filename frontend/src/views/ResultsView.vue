<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { artifactDownloadUrl, listExportArtifacts, type ExportArtifact } from '@/api/exports'
import { getProject, type Project } from '@/api/projects'
import AppBar from '@/components/AppBar.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { formatDate, formatSize } from '@/utils/format'

const route = useRoute()
const project = ref<Project | null>(null)
const artifacts = ref<ExportArtifact[]>([])
const projectId = computed(() => String(route.params.id))

async function load() {
  const [projectResponse, artifactResponse] = await Promise.all([
    getProject(projectId.value),
    listExportArtifacts(projectId.value),
  ])
  project.value = projectResponse.data
  artifacts.value = artifactResponse.data
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
        <span class="sep">/</span><span>成果管理</span>
      </nav>
      <div class="between">
        <div><div class="eyebrow">RESULTS</div><h1 class="h-page mt-2">成果管理</h1></div>
        <RouterLink class="btn btn-primary" :to="`/projects/${projectId}/export`">生成成果</RouterLink>
      </div>
      <section class="panel mt-8">
        <div v-if="artifacts.length === 0" class="state">
          <span class="glyph"><SvgIcon name="file" :size="30" /></span>
          <h3>暂无成果</h3>
          <p>完成配准后可以导出 GeoTIFF 成果。</p>
        </div>
        <table v-else class="table">
          <thead><tr><th>成果类型</th><th>文件名</th><th>大小</th><th>生成时间</th><th style="text-align:right">操作</th></tr></thead>
          <tbody>
            <tr v-for="artifact in artifacts" :key="artifact.id">
              <td><span class="badge ok"><span class="dot"></span>{{ artifact.artifact_type }}</span></td>
              <td class="mono">{{ artifact.file_name }}</td>
              <td>{{ formatSize(artifact.size_bytes) }}</td>
              <td class="table-num">{{ formatDate(artifact.create_time) }}</td>
              <td><div class="actions"><a class="btn btn-primary btn-sm" :href="artifactDownloadUrl(artifact.id)">下载</a></div></td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>
  </div>
</template>
