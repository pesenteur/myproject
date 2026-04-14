<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-white/55 backdrop-blur-[2px]">
    <div class="mx-4 w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-xl">
      <div class="flex items-start gap-4">
        <div class="relative mt-0.5 h-10 w-10 flex-shrink-0">
          <div class="absolute inset-0 rounded-full border-2 border-slate-200"></div>
          <div class="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-blue-600"></div>
        </div>

        <div class="min-w-0 flex-1">
          <div class="text-base font-semibold text-slate-900">
            {{ title }}
          </div>

          <div class="mt-1 text-sm leading-6 text-slate-600">
            {{ message }}
          </div>

          <!-- Moving progress bar -->
          <div class="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div class="loading-track h-full w-full">
              <div class="loading-bar h-full rounded-full bg-blue-600"></div>
            </div>
          </div>

          <!-- Rotating stage text -->
          <div class="mt-3 text-xs leading-5 text-slate-500">
            {{ currentStage }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

defineProps({
  title: {
    type: String,
    default: 'Running OPUS-ResInsight prediction',
  },
  message: {
    type: String,
    default:
      'Generating sequence features, localizing residue-level evidence, and retrieving relevant UniRef50 matches.',
  },
})

const stages = [
  'Encoding sequence features...',
  'Inferring EC labels...',
  'Localizing residue-level evidence...',
  'Retrieving relevant UniRef50 matches...',
]

const stageIndex = ref(0)
let timer = null

const currentStage = computed(() => stages[stageIndex.value])

onMounted(() => {
  timer = setInterval(() => {
    stageIndex.value = (stageIndex.value + 1) % stages.length
  }, 7000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.loading-track {
  position: relative;
}

.loading-bar {
  width: 35%;
  animation: loading-slide 1.4s ease-in-out infinite;
}

@keyframes loading-slide {
  0% {
    transform: translateX(-120%);
  }
  100% {
    transform: translateX(320%);
  }
}
</style>