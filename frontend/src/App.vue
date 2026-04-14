<template>
  <div class="min-h-screen bg-slate-50">
    <TopNavBar />
    <RouterView />
  </div>
</template>

<script setup>
import TopNavBar from './components/TopNavBar.vue'
</script>