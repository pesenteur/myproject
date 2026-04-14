<template>
  <header class="sticky top-0 z-30 border-b border-slate-200 bg-white/85 backdrop-blur-md">
    <div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
      <!-- Brand -->
      <div class="flex items-center gap-3">
        <div class="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-sm font-semibold text-white shadow-sm">
          OG
        </div>

        <div>
          <div class="text-sm font-semibold tracking-tight text-slate-900">
            OPUS-ResInsight
          </div>
          <div class="text-xs text-slate-500">
            Explainable enzyme annotation
          </div>
        </div>
      </div>

      <!-- Nav -->
      <nav class="flex items-center gap-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="rounded-xl px-4 py-2 text-sm font-medium transition"
          :class="isActive(item.to)
            ? 'bg-blue-50 text-blue-700 shadow-sm ring-1 ring-blue-100'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { label: 'Server', to: '/server' },
  { label: 'About', to: '/about' },
  { label: 'Guide', to: '/guide' },
]

const isActive = (path) => route.path === path
</script>