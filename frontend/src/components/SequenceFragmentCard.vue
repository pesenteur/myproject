<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-slate-900">{{ title }}</h2>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          {{ description }}
        </p>
      </div>

      <div class="flex items-center gap-3">
        <label class="text-sm text-slate-600">Threshold</label>
        <input
            v-model.number="threshold"
            type="range"
            min="0"
            max="1"
            step="0.01"
            class="w-40"
        />
        <span class="w-12 text-sm font-medium text-slate-700">
          {{ threshold.toFixed(2) }}
        </span>
      </div>
    </div>

    <div v-if="paginatedItems.length > 0" class="space-y-5">
      <div
          v-for="item in paginatedItems"
          :key="item.id"
          class="rounded-2xl border border-slate-200 bg-white p-4"
      >
        <div class="mb-3 flex items-center justify-between gap-4">
          <div>
            <div class="text-sm font-semibold text-slate-900">
              {{ item.label || `Fragment #${item.id}` }}
            </div>
          </div>

          <div class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
            Evidence region
          </div>
        </div>

        <SequenceValueViewer
            :residues="item.residues"
            :threshold="threshold"
            :visible-count="160"
        />


      </div>

      <div class="flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-4">
        <div class="text-sm text-slate-500">
          Showing {{ startItem }} - {{ endItem }} of {{ items.length }} items
        </div>

        <div class="flex items-center gap-2">
          <button
              @click="prevPage"
              :disabled="currentPage === 1"
              class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-50"
          >
            Previous
          </button>

          <button
              v-for="page in totalPages"
              :key="page"
              @click="goToPage(page)"
              class="rounded-xl px-3 py-2 text-sm font-medium"
              :class="
              currentPage === page
                ? 'bg-slate-900 text-white'
                : 'border border-slate-200 bg-white text-slate-700'
            "
          >
            {{ page }}
          </button>

          <button
              @click="nextPage"
              :disabled="currentPage === totalPages"
              class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <div
        v-else
        class="flex min-h-[220px] items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-500"
    >
      No sequence fragments available.
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import SequenceValueViewer from './SequenceValueViewer.vue'

const props = defineProps({
  title: {
    type: String,
    default: 'Supporting Sequence Fragments',
  },
  description: {
    type: String,
    default: '',
  },
  items: {
    type: Array,
    default: () => [],
  },
})

const currentPage = ref(1)
const pageSize = 2
const threshold = ref(0.5)

const totalPages = computed(() => Math.max(1, Math.ceil(props.items.length / pageSize)))

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return props.items.slice(start, start + pageSize)
})

const startItem = computed(() => {
  if (props.items.length === 0) return 0
  return (currentPage.value - 1) * pageSize + 1
})

const endItem = computed(() => Math.min(currentPage.value * pageSize, props.items.length))

watch(
    () => props.items,
    () => {
      currentPage.value = 1
    }
)

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