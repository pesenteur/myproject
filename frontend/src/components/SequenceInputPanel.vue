<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold tracking-tight text-slate-900">
          Input Protein Sequence
        </h2>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Enter a protein sequence using one-letter amino acid codes only.
          FASTA headers are not supported in this interface.
        </p>
      </div>

      <div class="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
        Sequence input
      </div>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-slate-50 p-3">
      <textarea
        :value="modelValue"
        @input="handleInput"
        class="min-h-[220px] w-full rounded-2xl border bg-white px-4 py-4 font-mono text-sm leading-6 text-slate-800 outline-none transition focus:ring-4"
        :class="
          errorMessage
            ? 'border-red-300 focus:border-red-400 focus:ring-red-100'
            : 'border-slate-200 focus:border-blue-400 focus:ring-blue-100'
        "
        placeholder="Example:
MSIQEHVILVNDQGEVVGTQEKYAAHTSHTSLHLAFSSWLFNDRGQCLVTRRALSKIAWPGVWTNSVCGHPQIGETTEQAIARRCRFEVGVEIAQLTPIAADFRYCEIDPSGIVENEICPVFAAQIVSPLKVNPDEVMDYQWVELTSLLRALEATPWAFSPWMVSEAANASEKLKHFADNVKA"
        spellcheck="false"
      ></textarea>

      <div class="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div class="text-xs leading-5 text-slate-500">
          Allowed letters: A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y, B, Z, X, U, O
        </div>

        <div class="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
          Length: {{ normalizedLength }}
        </div>
      </div>
    </div>

    <div
      v-if="errorMessage"
      class="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700"
    >
      {{ errorMessage }}
    </div>

    <div class="mt-5 flex flex-wrap gap-3">
      <button
        @click="$emit('fill-example')"
        class="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
      >
        Load Example
      </button>

      <button
        @click="$emit('clear')"
        class="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
      >
        Clear
      </button>

      <button
        @click="handleSubmit"
        :disabled="loading"
        class="rounded-2xl bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {{ loading ? 'Running...' : 'Run OPUS-ResInsight Prediction' }}
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'submit', 'fill-example', 'clear'])

const normalizeSequence = (value) => {
  return value.toUpperCase().replace(/\s+/g, '')
}

const normalizedValue = computed(() => normalizeSequence(props.modelValue))
const normalizedLength = computed(() => normalizedValue.value.length)

const validateSequence = (rawValue) => {
  const value = rawValue.trim()

  if (!value) {
    return 'Sequence cannot be empty.'
  }

  if (value.includes('>')) {
    return 'FASTA headers are not allowed. Please input only the protein sequence.'
  }

  const normalized = normalizeSequence(value)

  if (!normalized) {
    return 'Sequence cannot be empty.'
  }

  const validProteinRegex = /^[ACDEFGHIKLMNPQRSTVWYBXZUO]+$/i
  if (!validProteinRegex.test(normalized)) {
    return 'Invalid sequence format. Only one-letter amino acid codes are allowed.'
  }

  if (normalized.length < 10) {
    return 'Sequence is too short. Please input a complete protein sequence.'
  }

  return ''
}

const errorMessage = computed(() => {
  if (!props.modelValue) return ''
  return validateSequence(props.modelValue)
})

const handleInput = (event) => {
  emit('update:modelValue', event.target.value)
}

const handleSubmit = () => {
  const error = validateSequence(props.modelValue)
  if (error) return

  const normalized = normalizeSequence(props.modelValue)
  emit('update:modelValue', normalized)
  emit('submit')
}
</script>