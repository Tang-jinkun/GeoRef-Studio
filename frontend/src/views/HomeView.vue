<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getHealth, type HealthPayload } from '@/api/health'
import { uploadImage, type ImageFile } from '@/api/images'
import { createProject, listProjects, type Project } from '@/api/projects'

const health = ref<HealthPayload | null>(null)
const healthLoading = ref(false)
const uploadLoading = ref(false)
const projectLoading = ref(false)
const error = ref('')
const uploadedImage = ref<ImageFile | null>(null)
const projects = ref<Project[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const projectForm = ref({
  name: '',
  description: '',
})

async function loadHealth() {
  healthLoading.value = true
  error.value = ''

  try {
    const response = await getHealth()
    health.value = response.data
  } catch {
    error.value = '后端健康检查暂不可用'
  } finally {
    healthLoading.value = false
  }
}

async function loadProjects() {
  projectLoading.value = true

  try {
    const response = await listProjects()
    projects.value = response.data
  } catch {
    ElMessage.warning('工程列表加载失败')
  } finally {
    projectLoading.value = false
  }
}

async function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  uploadLoading.value = true

  try {
    const response = await uploadImage(file)
    uploadedImage.value = response.data
    if (!projectForm.value.name) {
      projectForm.value.name = file.name.replace(/\.[^.]+$/, '')
    }
    ElMessage.success('图片上传成功')
  } catch {
    ElMessage.error('图片上传失败')
  } finally {
    uploadLoading.value = false
    input.value = ''
  }
}

function openFilePicker() {
  fileInput.value?.click()
}

async function submitProject() {
  if (!uploadedImage.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  if (!projectForm.value.name.trim()) {
    ElMessage.warning('请输入工程名称')
    return
  }

  projectLoading.value = true

  try {
    await createProject({
      name: projectForm.value.name.trim(),
      description: projectForm.value.description.trim() || undefined,
      image_id: uploadedImage.value.id,
    })
    projectForm.value = { name: '', description: '' }
    uploadedImage.value = null
    await loadProjects()
    ElMessage.success('工程创建成功')
  } catch {
    ElMessage.error('工程创建失败')
  } finally {
    projectLoading.value = false
  }
}

function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} B`
}

onMounted(() => {
  void loadHealth()
  void loadProjects()
})
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
        <el-button :loading="healthLoading" @click="loadHealth">刷新</el-button>
      </div>

      <el-alert v-if="error" :title="error" type="warning" :closable="false" />

      <section class="workspace">
        <div class="panel">
          <div class="panel-header">
            <h2>图片上传</h2>
            <el-button :loading="uploadLoading" @click="openFilePicker">选择图片</el-button>
            <input
              ref="fileInput"
              class="file-input"
              type="file"
              accept=".png,.jpg,.jpeg,.tif,.tiff,.bmp"
              @change="handleFileChange"
            />
          </div>

          <dl v-if="uploadedImage" class="metadata">
            <div>
              <dt>名称</dt>
              <dd>{{ uploadedImage.original_name }}</dd>
            </div>
            <div>
              <dt>尺寸</dt>
              <dd>{{ uploadedImage.width }} x {{ uploadedImage.height }}</dd>
            </div>
            <div>
              <dt>大小</dt>
              <dd>{{ formatSize(uploadedImage.size_bytes) }}</dd>
            </div>
            <div>
              <dt>格式</dt>
              <dd>{{ uploadedImage.format }}</dd>
            </div>
          </dl>

          <el-form class="project-form" label-position="top">
            <el-form-item label="工程名称">
              <el-input v-model="projectForm.name" maxlength="255" />
            </el-form-item>
            <el-form-item label="工程描述">
              <el-input v-model="projectForm.description" type="textarea" :rows="3" />
            </el-form-item>
            <el-button type="primary" :loading="projectLoading" @click="submitProject">
              创建工程
            </el-button>
          </el-form>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h2>工程列表</h2>
            <el-button :loading="projectLoading" @click="loadProjects">刷新</el-button>
          </div>

          <el-table v-loading="projectLoading" :data="projects" class="project-table">
            <el-table-column prop="name" label="工程名称" min-width="160" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column label="图片" min-width="180">
              <template #default="{ row }">
                {{ row.image?.original_name ?? '-' }}
              </template>
            </el-table-column>
            <el-table-column label="创建时间" min-width="180">
              <template #default="{ row }">
                {{ new Date(row.create_time).toLocaleString() }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>
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

.workspace {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 20px;
  margin-top: 20px;
}

.panel {
  padding: 18px;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  background: #ffffff;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.3;
  letter-spacing: 0;
}

.file-input {
  display: none;
}

.metadata {
  display: grid;
  gap: 10px;
  margin: 0 0 18px;
  padding: 12px;
  border-radius: 6px;
  background: #f6f8fb;
}

.metadata div {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 8px;
}

dt {
  color: #66788f;
}

dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.project-form {
  margin-top: 16px;
}

.project-table {
  width: 100%;
}

@media (max-width: 720px) {
  .home {
    padding: 20px;
  }

  .title-row,
  .status-panel,
  .workspace {
    grid-template-columns: 1fr;
  }

  .title-row {
    display: grid;
  }
}
</style>
