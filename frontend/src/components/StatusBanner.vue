<template>
  <div
    class="rounded-2xl border px-4 py-3"
    :class="wrapperClass"
  >
    <div class="flex items-start gap-3">
      <div
        class="mt-0.5 inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-semibold"
        :class="iconClass"
      >
        {{ iconText }}
      </div>

      <div class="min-w-0 flex-1">
        <div class="text-sm font-semibold" :class="titleClass">
          {{ title }}
        </div>
        <div class="mt-1 text-sm leading-6" :class="messageClass">
          {{ message }}
        </div>
      </div>

      <button
        v-if="dismissible"
        @click="$emit('close')"
        class="rounded-lg p-1 text-slate-400 transition hover:bg-white/70 hover:text-slate-600"
        aria-label="Close"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="h-4 w-4"
        >
          <path
            fill-rule="evenodd"
            d="M4.22 4.22a.75.75 0 0 1 1.06 0L10 8.94l4.72-4.72a.75.75 0 1 1 1.06 1.06L11.06 10l4.72 4.72a.75.75 0 1 1-1.06 1.06L10 11.06l-4.72 4.72a.75.75 0 0 1-1.06-1.06L8.94 10 4.22 5.28a.75.75 0 0 1 0-1.06Z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'error', // error | info | success
  },
  title: {
    type: String,
    default: '',
  },
  message: {
    type: String,
    default: '',
  },
  dismissible: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close'])

const wrapperClass = computed(() => {
  if (props.variant === 'success') return 'border-emerald-200 bg-emerald-50'
  if (props.variant === 'info') return 'border-blue-200 bg-blue-50'
  return 'border-red-200 bg-red-50'
})

const iconClass = computed(() => {
  if (props.variant === 'success') return 'bg-emerald-100 text-emerald-700'
  if (props.variant === 'info') return 'bg-blue-100 text-blue-700'
  return 'bg-red-100 text-red-700'
})

const titleClass = computed(() => {
  if (props.variant === 'success') return 'text-emerald-900'
  if (props.variant === 'info') return 'text-blue-900'
  return 'text-red-900'
})

const messageClass = computed(() => {
  if (props.variant === 'success') return 'text-emerald-800'
  if (props.variant === 'info') return 'text-blue-800'
  return 'text-red-800'
})

const iconText = computed(() => {
  if (props.variant === 'success') return '✓'
  if (props.variant === 'info') return 'i'
  return '!'
})
</script>