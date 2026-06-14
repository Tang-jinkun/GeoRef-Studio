<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import mapboxgl, { type Map as MapboxMap } from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

import {
  createControlPoint,
  deleteControlPoint,
  listControlPoints,
  updateControlPoint,
  type ControlPoint,
} from '@/api/controlPoints'
import { getGeorefPreview, getRms, runGeoref, type GeorefPreviewResult } from '@/api/georef'
import { imageFileUrl } from '@/api/images'
import { getProject, type Project } from '@/api/projects'
import SvgIcon from '@/components/SvgIcon.vue'
import { formatNumber } from '@/utils/format'

const route = useRoute()
const project = ref<Project | null>(null)
const points = ref<ControlPoint[]>([])
const selectedId = ref('')
const loading = ref(false)
const running = ref(false)
const error = ref('')
const message = ref('')
const imageCanvas = ref<HTMLDivElement | null>(null)
const imageScale = ref(1)
const imagePan = reactive({ x: 0, y: 0 })
const imageMouse = ref<{ x: number; y: number } | null>(null)
const mapContainer = ref<HTMLDivElement | null>(null)
const map = shallowRef<MapboxMap | null>(null)
const mapMouse = ref<{ longitude: number; latitude: number } | null>(null)
const mapStyle = ref<'osm' | 'tdt-vector' | 'tdt-image'>('osm')
const mapRevision = ref(0)
const preview = ref<GeorefPreviewResult | null>(null)
const previewVisible = ref(false)
const previewOpacity = ref(0.65)
const imageDrag = ref<{
  startClientX: number
  startClientY: number
  startPanX: number
  startPanY: number
} | null>(null)

const form = reactive({
  pixel_x: 0,
  pixel_y: 0,
  longitude: 0,
  latitude: 0,
})

const tiandituToken = import.meta.env.VITE_TIANDITU_TOKEN as string | undefined

const projectId = computed(() => String(route.params.id))
const selectedPoint = computed(() => points.value.find((point) => point.id === selectedId.value) ?? null)
const enabledCount = computed(() => points.value.filter((point) => point.enabled).length)
const imageSize = computed(() => ({
  width: project.value?.image?.width ?? 0,
  height: project.value?.image?.height ?? 0,
}))
const fittedImage = computed(() => {
  const canvas = imageCanvas.value
  const { width, height } = imageSize.value
  if (!canvas || width <= 0 || height <= 0) {
    return { width: 0, height: 0, left: 0, top: 0, scale: 1 }
  }

  const fitScale = Math.min(canvas.clientWidth / width, canvas.clientHeight / height)
  const displayWidth = width * fitScale * imageScale.value
  const displayHeight = height * fitScale * imageScale.value
  return {
    width: displayWidth,
    height: displayHeight,
    left: (canvas.clientWidth - displayWidth) / 2 + imagePan.x,
    top: (canvas.clientHeight - displayHeight) / 2 + imagePan.y,
    scale: fitScale * imageScale.value,
  }
})
const rms = computed(() => {
  const values = points.value.filter((point) => point.enabled && point.residual !== null)
  if (!values.length) return null
  return Math.sqrt(values.reduce((sum, point) => sum + Number(point.residual) ** 2, 0) / values.length)
})
const mapStyles = computed(() => ({
  osm: {
    version: 8,
    sources: {
      osm: {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors',
      },
    },
    layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
  },
  'tdt-vector': {
    version: 8,
    sources: {
      tdtVector: {
        type: 'raster',
        tiles: [
          `https://t0.tianditu.gov.cn/DataServer?T=vec_w&x={x}&y={y}&l={z}&tk=${tiandituToken ?? ''}`,
          `https://t1.tianditu.gov.cn/DataServer?T=vec_w&x={x}&y={y}&l={z}&tk=${tiandituToken ?? ''}`,
        ],
        tileSize: 256,
        attribution: '© 天地图',
      },
    },
    layers: [{ id: 'tdtVector', type: 'raster', source: 'tdtVector' }],
  },
  'tdt-image': {
    version: 8,
    sources: {
      tdtImage: {
        type: 'raster',
        tiles: [
          `https://t0.tianditu.gov.cn/DataServer?T=img_w&x={x}&y={y}&l={z}&tk=${tiandituToken ?? ''}`,
          `https://t1.tianditu.gov.cn/DataServer?T=img_w&x={x}&y={y}&l={z}&tk=${tiandituToken ?? ''}`,
        ],
        tileSize: 256,
        attribution: '© 天地图',
      },
    },
    layers: [{ id: 'tdtImage', type: 'raster', source: 'tdtImage' }],
  },
}))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [projectResponse, pointsResponse] = await Promise.all([
      getProject(projectId.value),
      listControlPoints(projectId.value),
    ])
    project.value = projectResponse.data
    points.value = pointsResponse.data
    if (!selectedId.value && points.value[0]) selectedId.value = points.value[0].id
    await nextTick()
    fitImage()
    fitMapToPoints()
  } catch {
    error.value = '工作台数据加载失败。'
  } finally {
    loading.value = false
  }
}

function initMap() {
  if (!mapContainer.value || map.value) return

  mapboxgl.accessToken = 'not-required-for-raster-sources'
  map.value = new mapboxgl.Map({
    container: mapContainer.value,
    style: mapStyles.value.osm as mapboxgl.StyleSpecification,
    center: [105, 35],
    zoom: 3,
    attributionControl: false,
  })
  map.value.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right')
  map.value.on('mousemove', (event) => {
    mapMouse.value = {
      longitude: Number(event.lngLat.lng.toFixed(6)),
      latitude: Number(event.lngLat.lat.toFixed(6)),
    }
  })
  map.value.on('move', () => {
    mapRevision.value += 1
  })
  map.value.on('mouseleave', () => {
    mapMouse.value = null
  })
  map.value.on('click', (event) => {
    form.longitude = Number(event.lngLat.lng.toFixed(6))
    form.latitude = Number(event.lngLat.lat.toFixed(6))
    message.value = `已选取地图坐标：${form.longitude}, ${form.latitude}。`
  })
  map.value.on('style.load', () => {
    renderPreviewLayer()
  })
}

function switchMapStyle(style: 'osm' | 'tdt-vector' | 'tdt-image') {
  if (style !== 'osm' && !tiandituToken) {
    error.value = '天地图底图需要配置 VITE_TIANDITU_TOKEN。'
    return
  }
  mapStyle.value = style
  map.value?.setStyle(mapStyles.value[style] as mapboxgl.StyleSpecification)
}

function absoluteImageUrl(path: string) {
  if (path.startsWith('http')) return path
  return `${window.location.origin}${path}`
}

function renderPreviewLayer() {
  if (!map.value) return

  if (map.value.getLayer('georef-preview-layer')) {
    map.value.removeLayer('georef-preview-layer')
  }
  if (map.value.getSource('georef-preview-source')) {
    map.value.removeSource('georef-preview-source')
  }
  if (!preview.value || !previewVisible.value) return

  map.value.addSource('georef-preview-source', {
    type: 'image',
    url: absoluteImageUrl(preview.value.image_url),
    coordinates: preview.value.coordinates,
  })
  map.value.addLayer({
    id: 'georef-preview-layer',
    type: 'raster',
    source: 'georef-preview-source',
    paint: {
      'raster-opacity': previewOpacity.value,
    },
  })
}

function updatePreviewOpacity() {
  map.value?.setPaintProperty('georef-preview-layer', 'raster-opacity', previewOpacity.value)
}

function fitMapToPreview() {
  if (!map.value || !preview.value) return
  const bounds = new mapboxgl.LngLatBounds()
  preview.value.coordinates.forEach((coord) => bounds.extend(coord))
  map.value.fitBounds(bounds, { padding: 80, maxZoom: 14 })
}

async function loadPreview() {
  error.value = ''
  try {
    const response = await getGeorefPreview(projectId.value)
    preview.value = response.data
    previewOpacity.value = response.data.opacity
    previewVisible.value = true
    renderPreviewLayer()
    fitMapToPreview()
    message.value = '配准预览已叠加到地图。'
  } catch {
    error.value = '预览生成失败，请先执行配准。'
  }
}

function togglePreview() {
  if (!preview.value) {
    void loadPreview()
    return
  }
  previewVisible.value = !previewVisible.value
  renderPreviewLayer()
}

function fitMapToPoints() {
  const enabled = points.value.filter((point) => point.enabled)
  if (!map.value || enabled.length === 0) return

  const bounds = new mapboxgl.LngLatBounds()
  enabled.forEach((point) => bounds.extend([point.longitude, point.latitude]))
  if (enabled.length === 1) {
    map.value.flyTo({ center: [enabled[0].longitude, enabled[0].latitude], zoom: 10 })
  } else {
    map.value.fitBounds(bounds, { padding: 80, maxZoom: 14 })
  }
}

function mapPointToCanvas(point: ControlPoint) {
  mapRevision.value
  if (!map.value) {
    return { left: '-999px', top: '-999px' }
  }
  const position = map.value.project([point.longitude, point.latitude])
  return {
    left: `${position.x}px`,
    top: `${position.y}px`,
  }
}

function fitImage() {
  imageScale.value = 1
  imagePan.x = 0
  imagePan.y = 0
}

function zoomImage(delta: number) {
  imageScale.value = Math.min(8, Math.max(0.25, Number((imageScale.value + delta).toFixed(2))))
}

function imagePointToCanvas(point: ControlPoint) {
  const image = fittedImage.value
  return {
    left: `${image.left + point.pixel_x * image.scale}px`,
    top: `${image.top + point.pixel_y * image.scale}px`,
  }
}

function canvasEventToPixel(event: MouseEvent) {
  const canvas = imageCanvas.value
  const { width, height } = imageSize.value
  if (!canvas || width <= 0 || height <= 0) return null

  const rect = canvas.getBoundingClientRect()
  const image = fittedImage.value
  const x = (event.clientX - rect.left - image.left) / image.scale
  const y = (event.clientY - rect.top - image.top) / image.scale

  if (x < 0 || y < 0 || x > width || y > height) return null
  return {
    x: Number(x.toFixed(2)),
    y: Number(y.toFixed(2)),
  }
}

function updateImageMouse(event: MouseEvent) {
  imageMouse.value = canvasEventToPixel(event)
}

function leaveImageCanvas() {
  imageMouse.value = null
}

function pickImagePixel(event: MouseEvent) {
  if ((event.target as HTMLElement).closest('.gcp')) return
  const pixel = canvasEventToPixel(event)
  if (!pixel) return

  form.pixel_x = pixel.x
  form.pixel_y = pixel.y
  message.value = `已选取图片像素：${pixel.x}, ${pixel.y}。`
}

function startImagePan(event: MouseEvent) {
  if (event.button !== 1 && !(event.button === 0 && event.altKey)) return
  event.preventDefault()
  imageDrag.value = {
    startClientX: event.clientX,
    startClientY: event.clientY,
    startPanX: imagePan.x,
    startPanY: imagePan.y,
  }
}

function moveImagePan(event: MouseEvent) {
  updateImageMouse(event)
  if (!imageDrag.value) return

  imagePan.x = imageDrag.value.startPanX + event.clientX - imageDrag.value.startClientX
  imagePan.y = imageDrag.value.startPanY + event.clientY - imageDrag.value.startClientY
}

function stopImagePan() {
  imageDrag.value = null
}

function handleImageWheel(event: WheelEvent) {
  event.preventDefault()
  zoomImage(event.deltaY > 0 ? -0.1 : 0.1)
}

async function addPoint() {
  error.value = ''
  message.value = ''
  try {
    const response = await createControlPoint({
      project_id: projectId.value,
      pixel_x: Number(form.pixel_x),
      pixel_y: Number(form.pixel_y),
      longitude: Number(form.longitude),
      latitude: Number(form.latitude),
    })
    points.value.push(response.data)
    selectedId.value = response.data.id
    message.value = '控制点已新增。'
    fitMapToPoints()
  } catch {
    error.value = '控制点新增失败，请检查坐标范围。'
  }
}

async function togglePoint(point: ControlPoint) {
  const response = await updateControlPoint(point.id, { enabled: !point.enabled })
  points.value = points.value.map((item) => (item.id === point.id ? response.data : item))
  fitMapToPoints()
}

async function removePoint(point: ControlPoint) {
  await deleteControlPoint(point.id)
  points.value = points.value.filter((item) => item.id !== point.id)
  if (selectedId.value === point.id) selectedId.value = points.value[0]?.id ?? ''
  fitMapToPoints()
}

async function executeGeoref() {
  running.value = true
  error.value = ''
  message.value = ''
  try {
    const response = await runGeoref(projectId.value)
    points.value = response.data.control_points
    const rmsResponse = await getRms(projectId.value)
    points.value = rmsResponse.data.control_points
    message.value = `配准完成，RMS = ${formatNumber(response.data.rms, 6)}。`
    await load()
    await loadPreview()
  } catch {
    error.value = '配准失败，至少需要 3 个启用控制点。'
  } finally {
    running.value = false
  }
}

onMounted(async () => {
  await load()
  await nextTick()
  initMap()
  fitMapToPoints()
})

onBeforeUnmount(() => {
  map.value?.remove()
  map.value = null
})

watch(selectedPoint, (point) => {
  if (!point || !map.value) return
  map.value.easeTo({ center: [point.longitude, point.latitude], duration: 300 })
})

watch(previewOpacity, () => {
  updatePreviewOpacity()
})
</script>

<template>
  <div class="workbench app-bg">
    <header class="wb-bar">
      <RouterLink class="tbtn" :to="`/projects/${projectId}`" title="返回工程">
        <SvgIcon name="back" :size="18" />
      </RouterLink>
      <div class="wb-title">
        {{ project?.name ?? '配准工作台' }}
        <span class="badge" :class="project?.status === '已配准' ? 'ok' : 'neutral'">
          <span class="dot"></span>{{ project?.status ?? '加载中' }}
        </span>
      </div>
      <div class="sep"></div>
      <button class="tbtn" title="刷新" @click="load"><SvgIcon name="refresh" :size="18" /></button>
      <button class="tbtn" title="图片全图显示" @click="fitImage"><SvgIcon name="open" :size="18" /></button>
      <button class="tbtn active" title="新增控制点"><SvgIcon name="pin" :size="18" /></button>
      <button class="btn btn-primary btn-sm" :disabled="running || enabledCount < 3" @click="executeGeoref">
        <SvgIcon name="play" :size="15" />{{ running ? '执行中' : '执行配准' }}
      </button>
      <button class="btn btn-ghost btn-sm" :disabled="!project?.rms_error && !preview" @click="togglePreview">
        <SvgIcon name="eye" :size="15" />{{ previewVisible ? '隐藏预览' : '预览' }}
      </button>
      <RouterLink class="btn btn-ghost btn-sm" :to="`/projects/${projectId}/export`">
        <SvgIcon name="download" :size="15" />导出
      </RouterLink>
    </header>

    <main class="wb-body">
      <aside class="wb-col wb-left">
        <section class="col-sec">
          <div class="eyebrow">PROJECT</div>
          <h1 class="h-sec mt-2">{{ project?.name ?? '-' }}</h1>
          <p class="muted mt-2">{{ project?.image?.original_name ?? '未加载影像' }}</p>
        </section>
        <section class="col-sec">
          <div class="eyebrow">LAYERS</div>
          <div class="layer mt-4"><SvgIcon name="image" :size="16" /><span class="t">原始影像</span></div>
          <div class="layer"><SvgIcon name="map" :size="16" /><span class="t">Mapbox 底图</span></div>
          <div class="layer"><SvgIcon name="layers" :size="16" /><span class="t">配准预览</span></div>
        </section>
        <section class="col-sec">
          <div class="eyebrow">ADD GCP</div>
          <p class="hint-text mt-2">点击图片可回填 PixelX / PixelY。按住 Alt 拖拽或鼠标中键可平移图片，滚轮缩放。</p>
          <div class="grid gap-3 mt-4">
            <input v-model.number="form.pixel_x" class="input mono" placeholder="PixelX" />
            <input v-model.number="form.pixel_y" class="input mono" placeholder="PixelY" />
            <input v-model.number="form.longitude" class="input mono" placeholder="Longitude" />
            <input v-model.number="form.latitude" class="input mono" placeholder="Latitude" />
            <button class="btn btn-primary" @click="addPoint"><SvgIcon name="plus" :size="16" />新增控制点</button>
          </div>
        </section>
      </aside>

      <section class="wb-col wb-center">
        <div class="dual">
          <div class="win">
            <div class="win-head">
              <span class="t"><SvgIcon name="image" :size="15" />图片窗口</span>
              <div class="win-tools">
                <button class="tbtn mini" title="缩小" @click="zoomImage(-0.2)">-</button>
                <button class="tbtn mini" title="全图显示" @click="fitImage">1:1</button>
                <button class="tbtn mini" title="放大" @click="zoomImage(0.2)">+</button>
              </div>
            </div>
            <div
              ref="imageCanvas"
              class="win-canvas canvas-img"
              :class="{ panning: imageDrag }"
              @click="pickImagePixel"
              @mousedown="startImagePan"
              @mousemove="moveImagePan"
              @mouseup="stopImagePan"
              @mouseleave="leaveImageCanvas(); stopImagePan()"
              @wheel="handleImageWheel"
            >
              <div
                v-if="project?.image"
                class="image-stage"
                :style="{
                  width: `${fittedImage.width}px`,
                  height: `${fittedImage.height}px`,
                  transform: `translate(${fittedImage.left}px, ${fittedImage.top}px)`,
                }"
              >
                <img
                  class="work-image"
                  :src="imageFileUrl(project.image.id)"
                  :alt="project.image.original_name"
                  draggable="false"
                />
              </div>
              <button
                v-for="(point, index) in points"
                :key="`img-${point.id}`"
                class="gcp"
                :class="{ sel: selectedId === point.id, disabled: !point.enabled }"
                :style="imagePointToCanvas(point)"
                @click="selectedId = point.id"
              >
                <span class="ring"></span><span class="lbl">{{ index + 1 }}</span>
              </button>
              <span class="zoom-badge">{{ Math.round(imageScale * 100) }}%</span>
              <span class="coord-badge">
                PX {{ imageMouse?.x ?? selectedPoint?.pixel_x ?? '-' }} /
                {{ imageMouse?.y ?? selectedPoint?.pixel_y ?? '-' }}
              </span>
            </div>
          </div>
          <div class="win">
            <div class="win-head">
              <span class="t"><SvgIcon name="map" :size="15" />地图窗口</span>
              <div class="segmented map-segment">
                <button :class="{ active: mapStyle === 'osm' }" @click="switchMapStyle('osm')">OSM</button>
                <button
                  :class="{ active: mapStyle === 'tdt-vector' }"
                  :title="tiandituToken ? '天地图矢量' : '需配置 VITE_TIANDITU_TOKEN'"
                  @click="switchMapStyle('tdt-vector')"
                >
                  天地图矢量
                </button>
                <button
                  :class="{ active: mapStyle === 'tdt-image' }"
                  :title="tiandituToken ? '天地图影像' : '需配置 VITE_TIANDITU_TOKEN'"
                  @click="switchMapStyle('tdt-image')"
                >
                  天地图影像
                </button>
              </div>
            </div>
            <div class="win-canvas canvas-map">
              <div ref="mapContainer" class="mapbox-host"></div>
              <button
                v-for="(point, index) in points"
                :key="`map-${point.id}`"
                class="gcp"
                :class="{ sel: selectedId === point.id, disabled: !point.enabled }"
                :style="mapPointToCanvas(point)"
                @click="selectedId = point.id"
              >
                <span class="ring"></span><span class="lbl">{{ index + 1 }}</span>
              </button>
              <span class="zoom-badge">{{ mapStyle === 'osm' ? 'OSM' : '天地图' }}</span>
              <span class="coord-badge">
                LL {{ mapMouse?.longitude ?? selectedPoint?.longitude ?? '-' }} /
                {{ mapMouse?.latitude ?? selectedPoint?.latitude ?? '-' }}
              </span>
              <div v-if="preview" class="preview-ctl">
                <button class="btn btn-ghost btn-sm" @click="togglePreview">
                  <SvgIcon :name="previewVisible ? 'eye' : 'image'" :size="15" />
                  {{ previewVisible ? '隐藏' : '显示' }}
                </button>
                <div class="slider">
                  <span>透明度</span>
                  <input v-model.number="previewOpacity" type="range" min="0" max="1" step="0.05" />
                  <span class="mono">{{ Math.round(previewOpacity * 100) }}%</span>
                </div>
                <button class="btn btn-ghost btn-sm" @click="fitMapToPreview">定位</button>
              </div>
            </div>
          </div>
        </div>
        <div class="wb-status">
          <span>控制点 <b>{{ points.length }}</b></span>
          <span>启用 <b>{{ enabledCount }}</b></span>
          <span>RMS <b>{{ formatNumber(rms, 6) }}</b></span>
          <span>鼠标像素 <b>{{ imageMouse ? `${imageMouse.x}, ${imageMouse.y}` : '-' }}</b></span>
          <span>地图坐标 <b>{{ mapMouse ? `${mapMouse.longitude}, ${mapMouse.latitude}` : '-' }}</b></span>
          <span class="mode">{{ loading ? '加载中' : imageDrag ? '图片平移' : '新增控制点模式' }}</span>
        </div>
      </section>

      <aside class="wb-col wb-right">
        <section class="col-sec">
          <div class="between">
            <div><div class="eyebrow">CONTROL POINTS</div><h2 class="h-sec mt-2">控制点</h2></div>
            <span class="badge accent">{{ enabledCount }} / {{ points.length }}</span>
          </div>
        </section>

        <div v-if="points.length === 0" class="state">
          <span class="glyph"><SvgIcon name="pin" :size="30" /></span>
          <h3>暂无控制点</h3>
          <p>使用左侧表单录入像素坐标和经纬度。</p>
        </div>
        <div v-else class="gcp-list">
          <div
            v-for="(point, index) in points"
            :key="point.id"
            class="gcp-item"
            :class="{ sel: selectedId === point.id, off: !point.enabled }"
            @click="selectedId = point.id"
          >
            <div class="id">#{{ index + 1 }}</div>
            <div class="coords">PX {{ point.pixel_x }}, {{ point.pixel_y }}</div>
            <div class="res">{{ formatNumber(point.residual, 6) }}</div>
            <div class="geo">LL {{ point.longitude }}, {{ point.latitude }}</div>
            <div class="acts">
              <button class="btn btn-ghost btn-sm" @click.stop="togglePoint(point)">
                {{ point.enabled ? '禁用' : '启用' }}
              </button>
              <button class="btn btn-danger btn-sm" @click.stop="removePoint(point)">删除</button>
            </div>
          </div>
        </div>

        <section class="acc">
          <div class="acc-grid">
            <div class="acc-cell"><div class="k">RMS</div><div class="v">{{ formatNumber(rms, 6) }}</div></div>
            <div class="acc-cell"><div class="k">最低要求</div><div class="v">{{ enabledCount }} / 3</div></div>
          </div>
          <div v-if="error" class="callout danger"><SvgIcon name="warn" :size="18" />{{ error }}</div>
          <div v-else-if="message" class="callout ok"><SvgIcon name="check" :size="18" />{{ message }}</div>
          <div v-else class="callout"><SvgIcon name="info" :size="18" />推荐使用 4-10 个均匀分布的控制点。</div>
        </section>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.workbench {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.wb-bar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 54px;
  padding: 0 var(--space-4);
  background: color-mix(in oklab, var(--bg), black 8%);
  border-bottom: 1px solid var(--border);
  flex: none;
}
.wb-bar .sep {
  width: 1px;
  height: 24px;
  background: var(--border);
  margin: 0 4px;
}
.wb-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: var(--text-sm);
}
.wb-body {
  flex: 1;
  display: grid;
  grid-template-columns: 236px 1fr 320px;
  min-height: 0;
}
.wb-col {
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.wb-left,
.wb-right {
  background: var(--surface);
}
.wb-left {
  border-right: 1px solid var(--border);
}
.wb-right {
  border-left: 1px solid var(--border);
}
.col-sec {
  border-bottom: 1px solid var(--border-soft);
  padding: var(--space-4);
}
.layer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: var(--radius-sm);
}
.layer:hover {
  background: var(--surface-warm);
}
.layer .t {
  font-size: var(--text-sm);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hint-text {
  color: var(--muted);
  font-size: var(--text-xs);
  line-height: 1.5;
}
.dual {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--border);
  min-height: 0;
}
.win {
  background: var(--bg);
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.win-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: color-mix(in oklab, var(--surface), black 4%);
  border-bottom: 1px solid var(--border);
  flex: none;
}
.win-head .t {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--fg-2);
  display: flex;
  align-items: center;
  gap: 6px;
}
.win-tools {
  margin-left: auto;
  display: flex;
  gap: 4px;
}
.map-segment {
  margin-left: auto;
}
.map-segment button {
  padding: 5px 8px;
  font-size: 11px;
}
.tbtn.mini {
  width: 30px;
  height: 28px;
  font-family: var(--font-mono);
  font-size: 11px;
}
.win-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  cursor: crosshair;
}
.win-canvas.panning {
  cursor: grabbing;
}
.canvas-img {
  background: repeating-conic-gradient(from 0deg, #13211a 0deg 90deg, #0e1a13 90deg 180deg) 0 0/26px 26px;
}
.image-stage {
  position: absolute;
  left: 0;
  top: 0;
  transform-origin: 0 0;
  border: 1px solid color-mix(in oklab, var(--accent), transparent 70%);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.12);
}
.work-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: fill;
  opacity: 0.88;
  user-select: none;
  pointer-events: none;
}
.canvas-map {
  background-color: #0a1410;
}
.mapbox-host {
  position: absolute;
  inset: 0;
  z-index: 1;
}
.canvas-map .gcp,
.canvas-map .zoom-badge,
.canvas-map .coord-badge {
  z-index: 3;
}
.preview-ctl {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 40px;
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  background: color-mix(in oklab, var(--surface), transparent 6%);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--elev-raised);
}
.preview-ctl .slider {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--text-xs);
  color: var(--muted);
}
.preview-ctl input[type='range'] {
  flex: 1;
  min-width: 80px;
}
.gcp {
  position: absolute;
  width: 24px;
  height: 24px;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 4;
  background: transparent;
  border: 0;
}
.gcp .ring {
  position: absolute;
  inset: 0;
  border: 2px solid var(--accent);
  border-radius: 50%;
  background: color-mix(in oklab, var(--accent), transparent 80%);
}
.gcp .lbl {
  position: absolute;
  top: -7px;
  left: -7px;
  width: 16px;
  height: 16px;
  background: var(--accent);
  color: var(--accent-on);
  border-radius: 50%;
  font-size: 9px;
  font-weight: 700;
  display: grid;
  place-items: center;
  font-family: var(--font-mono);
}
.gcp.sel .ring {
  border-color: #fff;
  box-shadow: 0 0 0 4px color-mix(in oklab, var(--accent), transparent 60%);
}
.gcp.disabled .ring {
  border-color: var(--muted);
  background: transparent;
}
.gcp.disabled .lbl {
  background: var(--muted);
}
.zoom-badge,
.coord-badge {
  position: absolute;
  z-index: 3;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--fg-2);
  background: color-mix(in oklab, var(--surface), transparent 10%);
  border: 1px solid var(--border);
  padding: 4px 8px;
  border-radius: var(--radius-pill);
}
.zoom-badge {
  left: 10px;
  bottom: 10px;
}
.coord-badge {
  right: 10px;
  bottom: 10px;
  color: var(--meta);
}
.wb-status {
  flex: none;
  height: 30px;
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: 0 var(--space-4);
  background: color-mix(in oklab, var(--bg), black 10%);
  border-top: 1px solid var(--border);
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted);
}
.wb-status b {
  color: var(--fg-2);
}
.wb-status .mode {
  margin-left: auto;
  color: var(--accent);
}
.gcp-list {
  flex: 1;
  overflow: auto;
}
.gcp-item {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-soft);
  cursor: pointer;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 4px 10px;
  align-items: center;
}
.gcp-item:hover {
  background: var(--surface-warm);
}
.gcp-item.sel {
  background: color-mix(in oklab, var(--accent), transparent 90%);
  box-shadow: inset 3px 0 0 var(--accent);
}
.gcp-item .id,
.gcp-item .coords,
.gcp-item .geo,
.gcp-item .res {
  font-family: var(--font-mono);
}
.gcp-item .id {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  grid-row: span 2;
}
.gcp-item.off .id {
  color: var(--muted);
}
.gcp-item .coords {
  font-size: 11px;
  color: var(--fg-2);
}
.gcp-item .geo {
  font-size: 10px;
  color: var(--muted);
}
.gcp-item .res {
  font-size: 11px;
  font-weight: 600;
  grid-row: span 2;
  text-align: right;
}
.gcp-item .acts {
  grid-column: 2 / 4;
  display: flex;
  gap: 4px;
  margin-top: 4px;
}
.acc {
  padding: var(--space-4);
  border-top: 1px solid var(--border);
  background: color-mix(in oklab, var(--bg), transparent 30%);
}
.acc-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 12px;
}
.acc-cell {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  padding: 10px;
}
.acc-cell .k {
  font-size: 10px;
  color: var(--muted);
  margin-bottom: 4px;
}
.acc-cell .v {
  font-family: var(--font-mono);
  font-size: var(--text-lg);
  font-weight: 700;
}
@media (max-width: 1100px) {
  .wb-body {
    grid-template-columns: 1fr;
  }
  .wb-left,
  .wb-right {
    display: none;
  }
  .dual {
    grid-template-columns: 1fr;
  }
}
</style>
