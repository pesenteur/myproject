<template>
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-7xl px-6 py-10 lg:px-8">
      <section class="mb-8 overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-sky-50 via-white to-blue-50 p-8 shadow-sm">
        <div class="mb-4 inline-flex rounded-full border border-blue-200 bg-white/85 px-4 py-1 text-sm font-medium text-blue-700">
          OPUS-GO Web Server
        </div>

        <div class="grid gap-8 lg:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)] lg:items-start">
          <div>
            <h1 class="text-4xl font-semibold tracking-tight text-slate-900">
              Explainable EC Prediction from Protein Sequences
            </h1>

            <p class="mt-4 max-w-3xl text-base leading-8 text-slate-600">
              OPUS-GO predicts EC numbers from protein sequences, identifies functionally
              important residues associated with the predicted labels, and retrieves relevant
              UniRef50 sequences based on alignments of the identified critical residues.
            </p>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-white/85 p-5 backdrop-blur-sm">
            <div class="text-sm font-semibold text-slate-900">
              Core capabilities
            </div>

            <div class="mt-4 space-y-3 text-sm leading-6 text-slate-600">
              <div class="flex items-start gap-3">
                <span class="mt-[7px] h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"></span>
                <span>Predict EC numbers from input protein sequences using sequence-level representations.</span>
              </div>

              <div class="flex items-start gap-3">
                <span class="mt-[7px] h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"></span>
                <span>Localize residue-level evidence associated with predicted functional labels.</span>
              </div>

              <div class="flex items-start gap-3">
                <span class="mt-[7px] h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"></span>
                <span>Retrieve relevant UniRef50 sequences grouped by EC number.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="space-y-8">
        <LoadingOverlay v-if="loading" />

        <SequenceInputPanel
          v-model="sequenceText"
          :loading="loading"
          @submit="submitSequence"
          @fill-example="fillExample"
          @clear="clearInput"
        />

        <StatusBanner
          v-if="errorMessage"
          variant="error"
          title="Prediction request failed"
          :message="errorMessage"
          dismissible
          @close="errorMessage = ''"
        />

        <StatusBanner
          v-if="showNoConfidentPredictionBothMessage"
          variant="info"
          title="No confident EC prediction available"
          message="Neither the ESM branch nor the OPUS branch assigned any EC number with probability greater than 50% for this sequence. In line with the interpretability-oriented design of OPUS-GO, confident sequence-level annotation, residue-level interpretation, and retrieval results are not shown when prediction support is insufficient."
          dismissible
          @close="dismissNoPredictionMessages"
        />

        <StatusBanner
          v-if="showNoConfidentPredictionEsmMessage"
          variant="info"
          title="No confident ESM prediction available"
          message="The ESM branch did not assign any EC number with probability greater than 50% for this sequence. Only confidently supported predictions are displayed."
          dismissible
          @close="dismissNoPredictionMessages"
        />

        <StatusBanner
          v-if="showNoConfidentPredictionOpusMessage"
          variant="info"
          title="No confident OPUS prediction available"
          message="The OPUS branch did not assign any EC number with probability greater than 50% for this sequence. Only confidently supported predictions are displayed."
          dismissible
          @close="dismissNoPredictionMessages"
        />

        <StatusBanner
          v-if="showNoEvidenceMessage"
          variant="info"
          title="Limited residue-level evidence"
          message="Some residue-level evidence entries are hidden because fewer than 5 residues exceeded the residue-level confidence threshold of 0.5. Following the interpretability-oriented design of OPUS-GO, only labels with sufficient residue-level support are displayed."
          dismissible
          @close="dismissNoEvidenceMessage"
        />

        <MethodSummaryCard />

        <EcPredictionCard
          v-if="hasAnyConfidentPredictions"
          :items="confidentPredictions"
        />

        <SequenceFragmentCard
          v-if="hasMeaningfulEvidence"
          title="Residue-level Evidence"
          description="Functionally important residues localized by OPUS-GO for the predicted EC labels."
          :items="fragments"
        />

        <StatusBanner
          v-if="showNoUniRefRetrievalMessage"
          variant="info"
          title="No UniRef50 retrieval available"
          message="We only keep EC categories with sequence counts ranging from 50 to 100,000 for inclusion in the server database."
        />

        <ExternalDatabaseCard
          v-if="hasMeaningfulEvidence && hasExternalRetrievalResults"
          title="UniRef50 Retrieval"
          description="Relevant UniRef50 sequences grouped by EC number, retrieved using alignments of the identified critical residues."
          :groups="externalSequenceGroups"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import SequenceInputPanel from '../components/SequenceInputPanel.vue'
import MethodSummaryCard from '../components/MethodSummaryCard.vue'
import EcPredictionCard from '../components/EcPredictionCard.vue'
import SequenceFragmentCard from '../components/SequenceFragmentCard.vue'
import ExternalDatabaseCard from '../components/ExternalDatabaseCard.vue'
import StatusBanner from '../components/StatusBanner.vue'
import LoadingOverlay from '../components/LoadingOverlay.vue'

const sequenceText = ref('')
const loading = ref(false)

const predictions = ref([])
const fragments = ref([])
const externalSequenceGroups = ref([])

const errorMessage = ref('')
const noPredictionMessagesDismissed = ref(false)
const noEvidenceMessageDismissed = ref(false)
const hasSubmitted = ref(false)

const fillExample = () => {
  sequenceText.value =
    'MNNIRRVAILSLLVAVATGAHSQSLQQAAANSAFAGTTVNVGSKDYLVINGEAGKSTTTNQSLDFAQQVLAAKQGVEVVVDDPAPNATKPQAAEQLN'
}

const clearInput = () => {
  sequenceText.value = ''
  predictions.value = []
  fragments.value = []
  externalSequenceGroups.value = []
  errorMessage.value = ''
  noPredictionMessagesDismissed.value = false
  noEvidenceMessageDismissed.value = false
  hasSubmitted.value = false
}

const confidentPredictions = computed(() => {
  return predictions.value.filter((item) => Number(item.probability) > 0.5)
})

const confidentEsmPredictions = computed(() => {
  return predictions.value.filter(
    (item) => item.source === 'ESM' && Number(item.probability) > 0.5
  )
})

const confidentOpusPredictions = computed(() => {
  return predictions.value.filter(
    (item) => item.source === 'OPUS' && Number(item.probability) > 0.5
  )
})

const hasAnyConfidentPredictions = computed(() => {
  return confidentPredictions.value.length > 0
})

const hasConfidentEsmPredictions = computed(() => {
  return confidentEsmPredictions.value.length > 0
})

const hasConfidentOpusPredictions = computed(() => {
  return confidentOpusPredictions.value.length > 0
})

const hasMeaningfulEvidence = computed(() => {
  return fragments.value.some((fragment) => {
    const highlightedCount = (fragment.residues || []).filter(
      (residue) => Number(residue.value) >= 0.5
    ).length
    return highlightedCount >= 5
  })
})

const hasExternalRetrievalResults = computed(() => {
  return externalSequenceGroups.value.some(
    (group) => Array.isArray(group.items) && group.items.length > 0
  )
})

const showNoConfidentPredictionBothMessage = computed(() => {
  if (
    !hasSubmitted.value ||
    loading.value ||
    errorMessage.value ||
    noPredictionMessagesDismissed.value
  ) {
    return false
  }

  return !hasConfidentEsmPredictions.value && !hasConfidentOpusPredictions.value
})

const showNoConfidentPredictionEsmMessage = computed(() => {
  if (
    !hasSubmitted.value ||
    loading.value ||
    errorMessage.value ||
    noPredictionMessagesDismissed.value
  ) {
    return false
  }

  return !showNoConfidentPredictionBothMessage.value &&
    !hasConfidentEsmPredictions.value &&
    hasConfidentOpusPredictions.value
})

const showNoConfidentPredictionOpusMessage = computed(() => {
  if (
    !hasSubmitted.value ||
    loading.value ||
    errorMessage.value ||
    noPredictionMessagesDismissed.value
  ) {
    return false
  }

  return !showNoConfidentPredictionBothMessage.value &&
    hasConfidentEsmPredictions.value &&
    !hasConfidentOpusPredictions.value
})

const showNoEvidenceMessage = computed(() => {
  if (
    !hasSubmitted.value ||
    loading.value ||
    errorMessage.value ||
    noEvidenceMessageDismissed.value
  ) {
    return false
  }

  if (!hasAnyConfidentPredictions.value) {
    return false
  }

  const hiddenCount = fragments.value.filter((fragment) => {
    const highlightedCount = (fragment.residues || []).filter(
      (residue) => Number(residue.value) >= 0.5
    ).length
    return highlightedCount < 5
  }).length

  return hiddenCount > 0
})

const showNoUniRefRetrievalMessage = computed(() => {
  if (
    !hasSubmitted.value ||
    loading.value ||
    errorMessage.value
  ) {
    return false
  }

  return hasAnyConfidentPredictions.value &&
    hasMeaningfulEvidence.value &&
    !hasExternalRetrievalResults.value
})

const dismissNoPredictionMessages = () => {
  noPredictionMessagesDismissed.value = true
}

const dismissNoEvidenceMessage = () => {
  noEvidenceMessageDismissed.value = true
}

const submitSequence = async () => {
  if (!sequenceText.value.trim()) {
    errorMessage.value = 'Please input an amino acid sequence first.'
    return
  }

  loading.value = true
  hasSubmitted.value = true
  errorMessage.value = ''
  noPredictionMessagesDismissed.value = false
  noEvidenceMessageDismissed.value = false

  predictions.value = []
  fragments.value = []
  externalSequenceGroups.value = []

  try {
    const response = await fetch('/api/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sequence: sequenceText.value,
      }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }

    const data = await response.json()

    predictions.value = Array.isArray(data.predictions) ? data.predictions : []
    fragments.value = Array.isArray(data.fragments) ? data.fragments : []
    externalSequenceGroups.value = Array.isArray(data.externalSequenceGroups)
      ? data.externalSequenceGroups
      : []
  } catch (error) {
    console.error('请求失败：', error)
    errorMessage.value =
      error?.message || 'Prediction failed. Please check the backend service.'
  } finally {
    loading.value = false
  }
}
</script>