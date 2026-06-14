<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { listControlPoints, type ControlPoint } from '@/api/controlPoints'
import { listExportArtifacts, type ExportArtifact } from '@/api/exports'
import { getProject, type Project } from '@/api/projects'
import AppBar from '@/components/AppBar.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { formatDate, formatNumber, formatSize, statusBadgeClass } from '@/utils/format'

const route = useRoute()
const project = ref<Project | null>(null)
const controlPoints = ref<ControlPoint[]>([])
const artifacts = ref<ExportArtifact[]>([])
const loading = ref(true)
const error = ref('')

const projectId = computed(() => String(route.params.id))
const enabledCount = computed(() => controlPoints.value.filter((point) => point.enabled).length)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [projectResponse, pointsResponse, artifactsResponse] = await Promise.all([
      getProject(projectId.value),
      listControlPoints(projectId.value),
      listExportArtifacts(projectId.value),
    ])
    project.value = projectResponse.data
    controlPoints.value = pointsResponse.data
    artifacts.value = artifactsResponse.data
  } catch {
    error.value = '工程详情加载失败。'
  } finally {
    loading.value = false
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
        <span>{{ project?.name ?? '工程详情' }}</span>
      </nav>

      <section v-if="loading" class="panel"><div class="state"><span class="spinner lg"></span></div></section>
      <section v-else-if="error || !project" class="panel">
        <div class="state danger">
          <span class="glyph"><SvgIcon name="warn" :size="30" /></span>
          <h3>加载失败</h3>
          <p>{{ error || '工程不存在。' }}</p>
          <button class="btn btn-primary" @click="load">重试</button>
        </div>
      </section>

      <template v-else>
        <div class="between detail-head">
          <div>
            <div class="row gap-3">
              <h1 class="h-page">{{ project.name }}</h1>
              <span class="badge" :class="statusBadgeClass(project.status)">
                <span class="dot"></span>{{ project.status }}
              </span>
            </div>
            <p class="lead mt-2 detail-desc">{{ project.description || '暂无工程描述。' }}</p>
          </div>
          <div class="wrap-actions">
            <RouterLink class="btn btn-primary" :to="`/projects/${project.id}/workbench`">
              进入配准工作台
            </RouterLink>
            <RouterLink
              v-if="project.status !== '未配准'"
              class="btn btn-ghost"
              :to="`/projects/${project.id}/export`"
            >
              导出成果
            </RouterLink>
          </div>
        </div>

        <div class="grid detail-grid mt-8">
          <div class="panel">
            <div class="img-preview">
              <SvgIcon name="image" :size="48" />
              <span class="badge neutral preview-badge">原始影像</span>
            </div>
            <div class="panel-body">
              <div class="dl">
                <dt>文件名</dt><dd>{{ project.image?.original_name ?? '-' }}</dd>
                <dt>尺寸</dt>
                <dd>{{ project.image ? `${project.image.width} x ${project.image.height} px` : '-' }}</dd>
                <dt>大小</dt><dd>{{ project.image ? formatSize(project.image.size_bytes) : '-' }}</dd>
                <dt>格式</dt><dd>{{ project.image?.format ?? '-' }}</dd>
              </div>
            </div>
          </div>

          <div class="stack detail-panels">
            <div class="panel">
              <div class="panel-head"><h3 class="h-sec">工程信息</h3></div>
              <div class="panel-body">
                <div class="dl detail-dl">
                  <dt>状态</dt>
                  <dd>
                    <span class="badge" :class="statusBadgeClass(project.status)">
                      <span class="dot"></span>{{ project.status }}
                    </span>
                  </dd>
                  <dt>控制点</dt><dd>{{ controlPoints.length }} 个 · 启用 {{ enabledCount }} 个</dd>
                  <dt>创建时间</dt><dd>{{ formatDate(project.create_time) }}</dd>
                  <dt>更新时间</dt><dd>{{ formatDate(project.update_time) }}</dd>
                </div>
              </div>
            </div>

            <div class="panel">
              <div class="panel-head">
                <h3 class="h-sec">配准信息</h3>
                <span class="badge accent transform-badge">Affine Transformation</span>
              </div>
              <div class="panel-body">
                <div class="stat-row">
                  <div class="stat"><div class="k">控制点数量</div><div class="v">{{ controlPoints.length }}<small> / 启用 {{ enabledCount }}</small></div></div>
                  <div class="stat"><div class="k">当前 RMS</div><div class="v accent">{{ formatNumber(project.rms_error, 6) }}</div></div>
                  <div class="stat"><div class="k">GeoTIFF</div><div class="v">{{ artifacts.length ? '已生成' : '未生成' }}</div></div>
                  <div class="stat"><div class="k">配准时间</div><div class="v stat-date">{{ formatDate(project.georef_time) }}</div></div>
                </div>
                <div class="callout mt-4" :class="project.rms_error !== null ? 'ok' : 'warn'">
                  <SvgIcon :name="project.rms_error !== null ? 'check' : 'warn'" :size="18" />
                  <span>
                    {{
                      project.rms_error !== null
                        ? `配准完成，RMS = ${formatNumber(project.rms_error, 6)}。可导出 GeoTIFF。`
                        : enabledCount >= 3
                          ? '已满足最低控制点要求，可进入工作台执行 Affine 配准。'
                          : 'Affine 配准最少需要 3 个启用控制点。'
                    }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.detail-head {
  align-items: flex-start;
}
.detail-desc {
  max-width: 60ch;
}
.detail-grid {
  grid-template-columns: 300px 1fr;
  align-items: start;
}
.img-preview {
  position: relative;
  aspect-ratio: 4 / 3;
  display: grid;
  place-items: center;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  background: repeating-conic-gradient(from 0deg, #13211a 0deg 90deg, #0e1a13 90deg 180deg) 0 0/22px 22px;
}
.preview-badge {
  position: absolute;
  top: 10px;
  left: 10px;
}
.detail-panels {
  gap: var(--space-5);
}
.detail-dl {
  gap: 14px var(--space-8);
}
.transform-badge {
  margin-left: auto;
}
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}
.stat {
  padding: var(--space-4);
  background: var(--bg);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
}
.stat .k {
  font-size: var(--text-xs);
  color: var(--muted);
  margin-bottom: 6px;
}
.stat .v {
  font-family: var(--font-mono);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--fg);
}
.stat .v small,
.stat-date {
  font-size: var(--text-xs);
  color: var(--muted);
  font-weight: 400;
}
@media (max-width: 900px) {
  .detail-grid,
  .stat-row {
    grid-template-columns: 1fr;
  }
}
</style>
