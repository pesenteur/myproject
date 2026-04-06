<template>
  <div class="rounded-2xl bg-slate-50 p-4">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div class="text-xs text-slate-500">
        Showing {{ displayedResidues.length }} / {{ residues.length }} residues
      </div>

      <button
          v-if="residues.length > visibleCount"
          @click="expanded = !expanded"
          class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
      >
        {{ expanded ? 'Collapse' : 'Show more' }}
      </button>
    </div>

    <div class="rounded-xl border border-slate-200 bg-white p-3">
      <div class="flex flex-wrap gap-1 font-mono text-[11px] leading-5 text-slate-800">
        <span
            v-for="(item, index) in displayedResidues"
            :key="index"
            class="group relative inline-flex h-6 min-w-6 items-center justify-center rounded border border-slate-200 bg-white px-1"
        >
          <span>
            {{ item.value >= threshold ? item.aa : '-' }}
          </span>

          <span
              class="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-slate-900 px-2 py-1 text-[10px] text-white opacity-0 shadow-lg transition group-hover:opacity-100"
          >
            index: {{ index + 1 }} | value: {{ item.value.toFixed(3) }}
          </span>
        </span>
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
  threshold: {
    type: Number,
    default: 0.5,
  },
  visibleCount: {
    type: Number,
    default: 120,
  },
})

const expanded = ref(false)

const displayedResidues = computed(() => {
  if (expanded.value) return props.residues
  return props.residues.slice(0, props.visibleCount)
})
</script>