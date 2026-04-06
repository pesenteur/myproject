<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-slate-900">EC Predictions</h2>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          All predicted EC entries above threshold, with source labels from ESM or OPUS.
        </p>
      </div>

      <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
        {{ limitedItems.length }} items
      </div>
    </div>

    <div v-if="limitedItems.length > 0" class="space-y-4">
      <div
          v-for="(item, index) in paginatedItems"
          :key="`${item.source}-${item.ecNumber}-${index}`"
          class="rounded-2xl border border-slate-200 bg-slate-50 p-4"
      >
        <div class="mb-3 flex items-start justify-between gap-4">
          <div>
            <div class="flex items-center gap-2">
              <div class="text-lg font-semibold text-slate-900">
                {{ item.ecNumber }}
              </div>

              <span
                  class="rounded-full px-2.5 py-1 text-xs font-medium"
                  :class="
                  item.source === 'ESM'
                    ? 'bg-blue-50 text-blue-700'
                    : 'bg-emerald-50 text-emerald-700'
                "
              >
                {{ item.source }}
              </span>
            </div>
          </div>

          <div class="text-right">
            <div class="text-xs font-medium uppercase tracking-wide text-slate-500">
              Probability
            </div>
            <div class="mt-1 text-lg font-semibold text-slate-900">
              {{ formatPercent(item.probability) }}
            </div>
          </div>
        </div>

        <div class="h-2 w-full rounded-full bg-slate-200">
          <div
              class="h-2 rounded-full transition-all"
              :class="item.source === 'ESM' ? 'bg-blue-600' : 'bg-emerald-600'"
              :style="{ width: `${item.probability * 100}%` }"
          ></div>
        </div>
      </div>

      <div
          v-if="totalPages > 1"
          class="flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-4"
      >
        <div class="text-sm text-slate-500">
          Showing {{ startItem }} - {{ endItem }} of {{ limitedItems.length }} items
          <span v-if="items.length > maxItems" class="ml-2 text-slate-400">
            (capped from {{ items.length }})
          </span>
        </div>

        <div class="flex items-center gap-2">
          <button
              @click="prevPage"
              :disabled="currentPage === 1"
              class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Previous
          </button>

          <button
              v-for="page in totalPages"
              :key="page"
              @click="goToPage(page)"
              class="rounded-xl px-3 py-2 text-sm font-medium transition"
              :class="
              currentPage === page
                ? 'bg-slate-900 text-white'
                : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
            "
          >
            {{ page }}
          </button>

          <button
              @click="nextPage"
              :disabled="currentPage === totalPages"
              class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

      <div
          v-else
          class="text-sm text-slate-500"
      >
        Showing {{ limitedItems.length }} items
        <span v-if="items.length > maxItems" class="ml-2 text-slate-400">
          (capped from {{ items.length }})
        </span>
      </div>
    </div>

    <div
        v-else
        class="flex min-h-[180px] items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-500"
    >
      Submit a sequence to view predictions.
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})

const currentPage = ref(1)

/**
 * 最多保留多少条 prediction，防止页面被极端结果撑爆
 * 你可以按需要改成 50 / 100 / 200
 */
const maxItems = 100

/**
 * 每页显示多少条
 */
const pageSize = 10

const limitedItems = computed(() => {
  return props.items.slice(0, maxItems)
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(limitedItems.value.length / pageSize))
})

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return limitedItems.value.slice(start, start + pageSize)
})

const startItem = computed(() => {
  if (limitedItems.value.length === 0) return 0
  return (currentPage.value - 1) * pageSize + 1
})

const endItem = computed(() => {
  return Math.min(currentPage.value * pageSize, limitedItems.value.length)
})

watch(
    () => props.items,
    () => {
      currentPage.value = 1
    }
)

const formatPercent = (value) => `${(value * 100).toFixed(2)}%`

const goToPage = (page) => {
  currentPage.value = page
}

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}
</script>