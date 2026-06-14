<script setup lang="ts">
import AppBar from '@/components/AppBar.vue'
import SvgIcon from '@/components/SvgIcon.vue'
</script>

<template>
  <div class="app-bg">
    <AppBar />
    <main class="wrap">
      <div class="eyebrow">TASKS</div>
      <h1 class="h-page mt-2">任务进度</h1>
      <section class="panel mt-8">
        <div class="state">
          <span class="glyph"><SvgIcon name="clock" :size="30" /></span>
          <h3>暂无后台任务</h3>
          <p>当前 GeoTIFF 导出为同步接口。瓦片和 MBTiles 阶段会接入任务队列与进度状态。</p>
        </div>
      </section>
    </main>
  </div>
</template>
