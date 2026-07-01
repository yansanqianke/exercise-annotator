<!-- 根组件 — 区分认证页（独立布局）和业务页（全局布局） -->
<script setup>
import { useRoute } from 'vue-router'
import AppLayout from './components/AppLayout.vue'

const route = useRoute()
</script>

<template>
  <AppLayout v-if="!route.meta.guest">
    <router-view />
  </AppLayout>
  <router-view v-else />
</template>
