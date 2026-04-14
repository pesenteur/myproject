<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-5">
    <div class="mb-5 flex flex-wrap items-start justify-between gap-4">
      <div>
        <div class="text-sm font-semibold tracking-tight text-slate-900">
          Sequence Evidence View
        </div>
        <div class="mt-1 text-xs leading-5 text-slate-500">
          {{ residues.length }} residues · {{ highlightedCount }} highlighted residue<span v-if="highlightedCount !== 1">s</span>
        </div>
      </div>

      <button
        @click="showMaskedView = !showMaskedView"
        class="inline-flex items-center rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
      >
        {{ showMaskedView ? 'Show Full Sequence' : 'Show Masked Values' }}
      </button>
    </div>

    <div>
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div class="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
          {{ showMaskedView ? 'Masked Value View' : 'Full-length Sequence View' }}
        </div>

        <div class="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium text-slate-600">
          Threshold: 0.50
        </div>
      </div>

      <div class="rounded-2xl bg-slate-50 p-3.5">
        <div class="flex flex-wrap gap-1 font-mono text-[11px] leading-5">
          <span
            v-for="(item, index) in residues"
            :key="index"
            class="group relative inline-flex h-7 min-w-7 items-center justify-center rounded-md border px-1 shadow-sm transition"
            :class="getResidueClass(item)"
          >
            <span :class="getResidueTextClass(item)">
              {{ getDisplayedChar(item) }}
            </span>

            <span
              class="pointer-events-none absolute bottom-full left-1/2 z-[100] mb-3 hidden w-max min-w-[180px] -translate-x-1/2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-left font-sans text-[11px] leading-5 text-slate-700 shadow-xl group-hover:block"
            >
              <div class="mb-1 flex items-center justify-between gap-3">
                <span class="font-semibold text-slate-900">
                  Residue {{ item.aa }}
                </span>
                <span
                  class="rounded-full px-2 py-0.5 text-[10px] font-medium"
                  :class="
                    item.value >= 0.5
                      ? 'bg-blue-50 text-blue-700'
                      : 'bg-slate-100 text-slate-600'
                  "
                >
                  {{ item.value >= 0.5 ? 'highlighted' : 'context' }}
                </span>
              </div>
              <div>Index: {{ index + 1 }}</div>
              <div>Value: {{ item.value.toFixed(4) }}</div>
            </span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  residues: {
    type: Array,
    default: () => [],
  },
})

const showMaskedView = ref(false)

const highlightedCount = computed(() => {
  return props.residues.filter((item) => Number(item.value) >= 0.5).length
})

const getDisplayedChar = (item) => {
  if (showMaskedView.value) {
    return Number(item.value) >= 0.5 ? item.aa : '-'
  }
  return item.aa
}

const getResidueClass = (item) => {
  const highlighted = Number(item.value) >= 0.5

  if (showMaskedView.value) {
    return highlighted
      ? 'border-blue-300 bg-blue-50 text-slate-900 ring-1 ring-blue-200 shadow-md'
      : 'border-slate-200 bg-slate-100 text-slate-400'
  }

  return highlighted
    ? 'border-blue-300 bg-blue-50 text-slate-900 ring-1 ring-blue-200 shadow-md'
    : 'border-slate-200 bg-white text-slate-500'
}

const getResidueTextClass = (item) => {
  const highlighted = Number(item.value) >= 0.5

  if (highlighted) {
    return 'font-semibold text-blue-900'
  }

  return 'font-medium text-slate-400'
}
</script>