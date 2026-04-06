<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-slate-900">{{ title }}</h2>
        <p class="mt-2 text-sm leading-6 text-slate-600">
          {{ description }}
        </p>
      </div>

      <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
        {{ currentItems.length }} items
      </div>
    </div>

    <div v-if="groups.length > 0" class="mb-5">
      <label class="mb-2 block text-sm font-medium text-slate-700">
        EC Number
      </label>
      <select
          v-model="selectedEcNumber"
          class="w-full max-w-xs rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-100"
      >
        <option
            v-for="group in groups"
            :key="group.ecNumber"
            :value="group.ecNumber"
        >
          {{ group.ecNumber }} ({{ group.items.length }})
        </option>
      </select>
    </div>

    <div v-if="paginatedItems.length > 0" class="space-y-5">
      <div
          v-for="item in paginatedItems"
          :key="item.id"
          class="rounded-2xl border border-slate-200 bg-white p-5"
      >
        <div class="mb-4 flex flex-wrap items-start justify-between gap-4">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <div class="flex min-w-0 items-center gap-2">
                <div class="truncate text-base font-semibold text-slate-900">
                  {{ item.source }}
                </div>

                <a
                    :href="getUniRefLink(item.source)"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
                    title="Open in UniProt UniRef"
                >
                  <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      class="h-4 w-4"
                  >
                    <path
                        d="M5 5.75A2.75 2.75 0 0 1 7.75 3h2.5a.75.75 0 0 1 0 1.5h-2.5A1.25 1.25 0 0 0 6.5 5.75v6.5A1.25 1.25 0 0 0 7.75 13.5h6.5a1.25 1.25 0 0 0 1.25-1.25v-2.5a.75.75 0 0 1 1.5 0v2.5A2.75 2.75 0 0 1 14.25 15h-6.5A2.75 2.75 0 0 1 5 12.25v-6.5Z"
                    />
                    <path
                        d="M11 3.75A.75.75 0 0 1 11.75 3h4.5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-1.5 0V5.56l-5.97 5.97a.75.75 0 1 1-1.06-1.06l5.97-5.97h-2.69A.75.75 0 0 1 11 3.75Z"
                    />
                  </svg>
                </a>
              </div>

              <span class="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
                External DB
              </span>

              <span class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                {{ item.ecNumber }}
              </span>
            </div>

            <div class="mt-2 text-sm text-slate-500">
              Rank #{{ item.rank }}
            </div>
          </div>

          <div class="grid min-w-[240px] grid-cols-1 gap-2 sm:grid-cols-3">
            <div class="rounded-xl bg-slate-50 px-3 py-2">
              <div class="text-[11px] uppercase tracking-wide text-slate-500">
                Similarity
              </div>
              <div class="mt-1 text-sm font-semibold text-slate-900">
                {{ formatScore(item.similarity) }}
              </div>
            </div>

            <div class="rounded-xl bg-slate-50 px-3 py-2">
              <div class="text-[11px] uppercase tracking-wide text-slate-500">
                OPUS
              </div>
              <div class="mt-1 text-sm font-semibold text-slate-900">
                {{ formatPercent(item.probabilityOpus) }}
              </div>
            </div>

            <div class="rounded-xl bg-slate-50 px-3 py-2">
              <div class="text-[11px] uppercase tracking-wide text-slate-500">
                ESM
              </div>
              <div class="mt-1 text-sm font-semibold text-slate-900">
                {{ formatPercent(item.probabilityEsm) }}
              </div>
            </div>
          </div>
        </div>

        <div class="mb-4">
          <div class="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
            Aligned / Filtered Sequence
          </div>
          <PlainSequenceViewer :sequence="item.sequence" :visible-length="320" />
        </div>

        <div>
          <button
              @click="toggleOriginal(item.id)"
              class="mb-2 inline-flex items-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
          >
            {{ expandedOriginalIds.has(item.id) ? 'Hide Original Sequence' : 'Show Original Sequence' }}
          </button>

          <div v-if="expandedOriginalIds.has(item.id)">
            <div class="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
              Original Sequence
            </div>
            <PlainSequenceViewer :sequence="item.originalSequence" :visible-length="320" />
          </div>
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-4">
        <div class="text-sm text-slate-500">
          Showing {{ startItem }} - {{ endItem }} of {{ currentItems.length }} items
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

    <div
        v-else
        class="flex min-h-[220px] items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-500"
    >
      No external database sequences available.
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import PlainSequenceViewer from './PlainSequenceViewer.vue'

const props = defineProps({
  title: {
    type: String,
    default: 'External Database Sequences',
  },
  description: {
    type: String,
    default: '',
  },
  groups: {
    type: Array,
    default: () => [],
  },
})

const currentPage = ref(1)
const pageSize = 5
const expandedOriginalIds = ref(new Set())
const selectedEcNumber = ref('')

const currentGroup = computed(() => {
  return props.groups.find((g) => g.ecNumber === selectedEcNumber.value) || null
})

const currentItems = computed(() => {
  return currentGroup.value?.items || []
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(currentItems.value.length / pageSize))
})

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return currentItems.value.slice(start, start + pageSize)
})

const startItem = computed(() => {
  if (currentItems.value.length === 0) return 0
  return (currentPage.value - 1) * pageSize + 1
})

const endItem = computed(() => {
  return Math.min(currentPage.value * pageSize, currentItems.value.length)
})

watch(
    () => props.groups,
    (newGroups) => {
      currentPage.value = 1
      expandedOriginalIds.value = new Set()
      selectedEcNumber.value = newGroups.length > 0 ? newGroups[0].ecNumber : ''
    },
    { immediate: true }
)

watch(selectedEcNumber, () => {
  currentPage.value = 1
  expandedOriginalIds.value = new Set()
})

const formatPercent = (value) => `${(Number(value) * 100).toFixed(2)}%`
const formatScore = (value) => Number(value).toFixed(4)
const getUniRefLink = (source) =>
    `https://www.uniprot.org/uniref/${encodeURIComponent(source)}`

const toggleOriginal = (id) => {
  const next = new Set(expandedOriginalIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedOriginalIds.value = next
}

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