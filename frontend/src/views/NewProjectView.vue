<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { uploadImage, type ImageFile } from '@/api/images'
import { createProject } from '@/api/projects'
import AppBar from '@/components/AppBar.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { formatSize } from '@/utils/format'

const router = useRouter()
const fileInput = ref<HTMLInputElement | null>(null)
const name = ref('')
const description = ref('')
const uploadedImage = ref<ImageFile | null>(null)
const uploading = ref(false)
const submitting = ref(false)
const error = ref('')

function openFilePicker() {
  fileInput.value?.click()
}

async function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  uploading.value = true
  error.value = ''
  try {
    const response = await uploadImage(file)
    uploadedImage.value = response.data
    if (!name.value) name.value = file.name.replace(/\.[^.]+$/, '')
  } catch {
    error.value = '图片上传失败，请确认格式和大小。'
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function submit() {
  if (!name.value.trim()) {
    error.value = '工程名称不能为空。'
    return
  }
  if (!uploadedImage.value) {
    error.value = '请先上传一张影像文件。'
    return
  }

  submitting.value = true
  error.value = ''
  try {
    const response = await createProject({
      name: name.value.trim(),
      description: description.value.trim() || undefined,
      image_id: uploadedImage.value.id,
    })
    await router.push(`/projects/${response.data.id}`)
  } catch {
    error.value = '工程创建失败。'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="app-bg">
    <AppBar />
    <main class="wrap">
      <nav class="crumbs">
        <RouterLink to="/projects">工程列表</RouterLink><span class="sep">/</span><span>新建工程</span>
      </nav>
      <div class="eyebrow">NEW PROJECT</div>
      <h1 class="h-page mt-2">新建配准工程</h1>
      <p class="lead mt-2">
        填写工程信息并上传一张待配准影像。支持 PNG / JPG / JPEG / TIFF / BMP，单文件最大
        500MB。
      </p>

      <div class="grid new-project-grid mt-8">
        <div class="card new-project-card">
          <div class="field">
            <label>工程名称<span class="req">*</span></label>
            <input v-model="name" class="input" placeholder="例如：黄河三角洲_1987航片" />
            <div class="hint">用于在工程列表中标识，建议包含区域与年代。</div>
          </div>

          <div class="field">
            <label>工程描述 <span class="muted">（可选）</span></label>
            <textarea
              v-model="description"
              class="textarea"
              placeholder="影像来源、坐标系预期、用途等备注..."
            ></textarea>
          </div>

          <div class="field">
            <label>影像文件<span class="req">*</span></label>
            <button v-if="!uploadedImage" class="dz" type="button" @click="openFilePicker">
              <span class="dz-ic"><SvgIcon name="upload" :size="30" /></span>
              <span class="dz-title">
                {{ uploading ? '正在上传...' : '拖拽影像到此处，或点击选择文件' }}
              </span>
              <span class="dz-sub mono">PNG · JPG · JPEG · TIFF · BMP | ≤ 500MB</span>
            </button>
            <input
              ref="fileInput"
              class="hide"
              type="file"
              accept=".png,.jpg,.jpeg,.tif,.tiff,.bmp"
              @change="handleFileChange"
            />

            <div v-if="uploadedImage" class="filecard">
              <div class="thumb"><SvgIcon name="image" :size="30" /></div>
              <div class="stack file-info">
                <div class="between">
                  <span class="fname mono">{{ uploadedImage.original_name }}</span>
                  <button type="button" class="btn btn-ghost btn-sm" @click="uploadedImage = null">
                    重新选择
                  </button>
                </div>
                <div class="fmeta">
                  <span>格式 <b class="mono">{{ uploadedImage.format }}</b></span>
                  <span>大小 <b class="mono">{{ formatSize(uploadedImage.size_bytes) }}</b></span>
                  <span>宽 <b class="mono">{{ uploadedImage.width }} px</b></span>
                  <span>高 <b class="mono">{{ uploadedImage.height }} px</b></span>
                </div>
                <span class="upok mono">上传完成</span>
              </div>
            </div>
            <div v-if="error" class="err"><SvgIcon name="warn" :size="13" />{{ error }}</div>
          </div>
        </div>

        <aside class="stack side-help">
          <div class="panel">
            <div class="panel-body">
              <div class="eyebrow rules-title">校验规则</div>
              <ul class="rules">
                <li>工程名称不能为空</li>
                <li>必须选择一张影像文件</li>
                <li>格式需为 PNG/JPG/JPEG/TIFF/BMP</li>
                <li>单文件大小 ≤ 500MB</li>
              </ul>
            </div>
          </div>
          <div class="callout">
            <SvgIcon name="info" :size="18" />
            <span>创建后将进入工程详情页。Affine 配准最少需要 <b class="accent">3</b> 个控制点。</span>
          </div>
        </aside>
      </div>

      <div class="formbar">
        <RouterLink class="btn btn-ghost" to="/projects">取消</RouterLink>
        <button class="btn btn-primary" :disabled="submitting || uploading" @click="submit">
          {{ submitting ? '正在创建...' : '创建工程' }}
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.new-project-grid {
  grid-template-columns: 1fr 360px;
  align-items: start;
}

.new-project-card {
  padding: var(--space-8);
}

.dz {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: var(--space-12) var(--space-6);
  text-align: center;
  border: 1.5px dashed var(--border);
  border-radius: var(--radius-md);
  background: var(--bg);
  color: var(--fg-2);
  cursor: pointer;
}

.dz:hover {
  border-color: var(--accent);
  background: color-mix(in oklab, var(--accent), transparent 94%);
}

.dz-ic {
  color: var(--accent);
}

.dz-title {
  font-size: var(--text-sm);
}

.dz-sub {
  font-size: 11px;
  color: var(--muted);
}

.filecard {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface-warm);
}

.thumb {
  width: 84px;
  height: 84px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  display: grid;
  place-items: center;
  color: var(--accent);
  flex: none;
}

.file-info {
  flex: 1;
  gap: 4px;
  min-width: 0;
}

.fname {
  font-size: var(--text-sm);
  color: var(--fg);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fmeta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  font-size: var(--text-xs);
  color: var(--muted);
}

.upok {
  font-size: 11px;
  color: var(--success);
}

.side-help {
  gap: var(--space-4);
}

.rules-title {
  margin-bottom: 10px;
}

.rules {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: var(--text-sm);
  color: var(--fg-2);
}

.rules li::marker {
  color: var(--accent);
}

.formbar {
  position: sticky;
  bottom: 0;
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) 0;
  margin-top: var(--space-8);
  background: linear-gradient(transparent, var(--bg) 40%);
  border-top: 1px solid var(--border);
}

@media (max-width: 900px) {
  .new-project-grid {
    grid-template-columns: 1fr;
  }
}
</style>
