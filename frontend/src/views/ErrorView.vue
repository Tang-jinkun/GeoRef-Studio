<script setup lang="ts">
import { RouterLink } from 'vue-router'

import AppBar from '@/components/AppBar.vue'
import SvgIcon from '@/components/SvgIcon.vue'
</script>

<template>
  <div class="app-bg">
    <AppBar />
    <main class="wrap">
      <section class="panel">
        <div class="state danger">
          <span class="glyph"><SvgIcon name="warn" :size="30" /></span>
          <h3>页面不存在</h3>
          <p>当前地址没有对应的 GeoRef Studio 页面。</p>
          <RouterLink class="btn btn-primary" to="/projects">返回工程列表</RouterLink>
        </div>
      </section>
    </main>
  </div>
</template>
