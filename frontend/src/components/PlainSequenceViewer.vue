<template>
  <div class="rounded-2xl bg-slate-50 p-4">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div class="text-xs text-slate-500">
        Sequence length: {{ sequence.length }}
      </div>

      <button
          v-if="sequence.length > visibleLength"
          @click="expanded = !expanded"
          class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
      >
        {{ expanded ? 'Collapse' : 'Show more' }}
      </button>
    </div>

    <div
        class="rounded-xl border border-slate-200 bg-white p-3 font-mono text-[11px] leading-5 text-slate-800 break-all whitespace-pre-wrap"
    >
      {{ displayedSequence }}
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  sequence: {
    type: String,
    default: '',
  },
  visibleLength: {
    type: Number,
    default: 240,
  },
})

const expanded = ref(false)

const displayedSequence = computed(() => {
  if (expanded.value || props.sequence.length <= props.visibleLength) {
    return props.sequence
  }
  return props.sequence.slice(0, props.visibleLength) + '...'
})
</script>