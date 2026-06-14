<script setup lang="ts">
import AppBar from '@/components/AppBar.vue'
import SvgIcon from '@/components/SvgIcon.vue'
</script>

<template>
  <div class="app-bg">
    <AppBar />
    <main class="wrap">
      <div class="eyebrow">UPLOAD</div>
      <h1 class="h-page mt-2">上传状态</h1>
      <div class="grid mt-8 upload-grid">
        <div class="panel"><div class="state"><span class="glyph"><SvgIcon name="upload" :size="30" /></span><h3>未选择文件</h3><p>支持 PNG / JPG / JPEG / TIFF / BMP。</p></div></div>
        <div class="panel"><div class="state"><span class="glyph"><span class="spinner lg"></span></span><h3>上传中</h3><p>正在写入本地存储并读取图片元信息。</p></div></div>
        <div class="panel"><div class="state"><span class="glyph"><SvgIcon name="check" :size="30" /></span><h3>上传成功</h3><p>可继续创建工程。</p></div></div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.upload-grid {
  grid-template-columns: repeat(3, 1fr);
}
@media (max-width: 900px) {
  .upload-grid {
    grid-template-columns: 1fr;
  }
}
</style>
