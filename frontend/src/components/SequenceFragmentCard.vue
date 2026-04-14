<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-slate-900">{{ title }}</h2>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          {{ description }}
        </p>
      </div>

      <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
        {{ visibleItems.length }} items
      </div>
    </div>

    <div
      v-if="hiddenItems.length > 0"
      class="mb-5 rounded-2xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm leading-6 text-blue-800"
    >
      <div class="font-medium text-blue-900">
        {{ hiddenItems.length }} residue-level evidence entr{{ hiddenItems.length === 1 ? 'y is' : 'ies are' }} hidden
      </div>
      <div class="mt-1">
        The following predicted labels are not shown because fewer than 5 residues exceeded the residue-level confidence threshold of 0.5:
        <span class="font-medium">{{ hiddenLabelsText }}</span>.
      </div>
    </div>

    <div v-if="paginatedItems.length > 0" class="space-y-5">
      <div
        v-for="item in paginatedItems"
        :key="item.id"
        class="rounded-2xl border border-slate-200 bg-white p-4"
      >
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="text-base font-semibold tracking-tight text-slate-900">
              {{ item.label || `Fragment #${item.id}` }}
            </div>
            <div class="mt-1 text-xs leading-5 text-slate-500">
              Functionally relevant residue pattern localized for this predicted label.
            </div>
          </div>

          <span class="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
            Residue evidence
          </span>
        </div>

        <SequenceValueViewer :residues="item.residues" />
      </div>

      <div
        v-if="totalPages > 1"
        class="flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-4"
      >
        <div class="text-sm text-slate-500">
          Showing {{ startItem }} - {{ endItem }} of {{ visibleItems.length }} items
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
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import SequenceValueViewer from './SequenceValueViewer.vue'

const props = defineProps({
  title: {
    type: String,
    default: 'Residue-level Evidence',
  },
  description: {
    type: String,
    default: 'Functionally important residues localized by OPUS-ResInsight for the predicted EC labels.',
  },
  items: {
    type: Array,
    default: () => [],
  },
})

const currentPage = ref(1)
const pageSize = 2

const visibleItems = computed(() => {
  return props.items.filter((item) => {
    const count = (item.residues || []).filter((residue) => Number(residue.value) >= 0.5).length
    return count >= 5
  })
})

const hiddenItems = computed(() => {
  return props.items.filter((item) => {
    const count = (item.residues || []).filter((residue) => Number(residue.value) >= 0.5).length
    return count < 5
  })
})

const hiddenLabelsText = computed(() => {
  return hiddenItems.value
    .map((item) => item.label || `Fragment #${item.id}`)
    .join(', ')
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(visibleItems.value.length / pageSize))
})

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return visibleItems.value.slice(start, start + pageSize)
})

const startItem = computed(() => {
  if (visibleItems.value.length === 0) return 0
  return (currentPage.value - 1) * pageSize + 1
})

const endItem = computed(() => {
  return Math.min(currentPage.value * pageSize, visibleItems.value.length)
})

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