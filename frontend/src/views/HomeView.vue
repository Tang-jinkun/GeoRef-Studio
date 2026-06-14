<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { listProjects, type Project } from '@/api/projects'
import AppBar from '@/components/AppBar.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { formatDate, statusBadgeClass } from '@/utils/format'

const loading = ref(false)
const error = ref('')
const projects = ref<Project[]>([])
const query = ref('')
const statusFilter = ref('all')

const filteredProjects = computed(() =>
  projects.value.filter((project) => {
    const matchStatus = statusFilter.value === 'all' || project.status === statusFilter.value
    const matchQuery = project.name.toLowerCase().includes(query.value.trim().toLowerCase())
    return matchStatus && matchQuery
  }),
)

async function loadProjects() {
  loading.value = true
  error.value = ''
  try {
    const response = await listProjects()
    projects.value = response.data
  } catch {
    error.value = '无法获取工程列表，请检查后端服务。'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadProjects()
})
</script>

<template>
  <div class="app-bg">
    <AppBar />
    <main class="wrap wrap-wide">
      <div class="between project-heading">
        <div>
          <div class="eyebrow">PROJECTS</div>
          <h1 class="h-page mt-2">工程列表</h1>
        </div>
        <RouterLink class="btn btn-primary" to="/projects/new">
          <SvgIcon name="plus" :size="16" />已配准影像工程 · 快速新建
        </RouterLink>
      </div>

      <div class="between project-toolbar">
        <div class="search project-search">
          <SvgIcon name="search" :size="16" />
          <input v-model="query" class="input" placeholder="按工程名称搜索..." />
        </div>
        <div class="segmented">
          <button
            v-for="item in ['all', '未配准', '已配准', '已导出']"
            :key="item"
            :class="{ active: statusFilter === item }"
            @click="statusFilter = item"
          >
            {{ item === 'all' ? '全部' : item }}
          </button>
        </div>
      </div>

      <section v-if="loading" class="panel">
        <div class="panel-body stack project-loading">
          <div class="skel"></div>
          <div class="skel"></div>
          <div class="skel"></div>
          <div class="skel"></div>
        </div>
      </section>

      <section v-else-if="error" class="panel">
        <div class="state danger">
          <span class="glyph"><SvgIcon name="db" :size="30" /></span>
          <h3>加载失败</h3>
          <p>{{ error }}</p>
          <button class="btn btn-primary" @click="loadProjects">重试</button>
        </div>
      </section>

      <section v-else-if="projects.length === 0" class="panel">
        <div class="state">
          <span class="glyph"><SvgIcon name="folder" :size="30" /></span>
          <h3>还没有任何工程</h3>
          <p>创建你的第一个配准工程，上传一张待配准影像即可开始添加控制点。</p>
          <RouterLink class="btn btn-primary mt-2" to="/projects/new">新建工程</RouterLink>
        </div>
      </section>

      <section v-else class="panel">
        <table class="table">
          <thead>
            <tr>
              <th>工程名称</th>
              <th>状态</th>
              <th>影像文件</th>
              <th>尺寸</th>
              <th>创建时间</th>
              <th>更新时间</th>
              <th style="text-align: right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="project in filteredProjects" :key="project.id">
              <td>
                <RouterLink class="name row gap-2" :to="`/projects/${project.id}`">
                  <SvgIcon name="image" :size="16" />{{ project.name }}
                </RouterLink>
              </td>
              <td>
                <span class="badge" :class="statusBadgeClass(project.status)">
                  <span class="dot"></span>{{ project.status }}
                </span>
              </td>
              <td class="mono project-file">{{ project.image?.original_name ?? '-' }}</td>
              <td class="table-num">
                {{ project.image ? `${project.image.width} x ${project.image.height}` : '-' }}
              </td>
              <td class="table-num project-date">{{ formatDate(project.create_time) }}</td>
              <td class="table-num project-date">{{ formatDate(project.update_time) }}</td>
              <td>
                <div class="actions">
                  <RouterLink class="btn btn-primary btn-sm" :to="`/projects/${project.id}/workbench`">
                    打开
                  </RouterLink>
                  <RouterLink
                    v-if="project.status !== '未配准'"
                    class="btn btn-ghost btn-sm btn-icon"
                    :to="`/projects/${project.id}/export`"
                    title="导出"
                  >
                    <SvgIcon name="download" :size="15" />
                  </RouterLink>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="between project-count">
          <span class="mono">共 {{ filteredProjects.length }} 个工程</span>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.project-heading {
  margin-bottom: var(--space-6);
}

.project-toolbar {
  margin-bottom: var(--space-5);
  gap: var(--space-4);
  flex-wrap: wrap;
}

.project-search {
  flex: 1;
  min-width: 240px;
  max-width: 420px;
}

.project-loading {
  gap: 14px;
}

.project-loading .skel {
  height: 44px;
}

.project-file,
.project-date {
  font-size: var(--text-xs);
}

.project-count {
  padding: var(--space-4);
  font-size: var(--text-xs);
  color: var(--muted);
}
</style>
