<template>
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-7xl px-6 py-10 lg:px-8">
      <section class="mb-8 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div class="mb-4 inline-flex rounded-full bg-blue-50 px-4 py-1 text-sm font-medium text-blue-700">
          Protein Enzyme Classification
        </div>

        <h1 class="text-4xl font-semibold tracking-tight text-slate-900">
          Protein Sequence Server
        </h1>

        <p class="mt-4 max-w-3xl text-base leading-8 text-slate-600">
          Submit a protein sequence to obtain EC predictions, supporting sequence fragments,
          and UniRef50 external database matches grouped by EC number.
        </p>
      </section>

      <div class="space-y-8">
        <SequenceInputPanel
            v-model="sequenceText"
            :loading="loading"
            @submit="submitSequence"
            @fill-example="fillExample"
            @clear="clearInput"
        />

        <EcPredictionCard :items="predictions" />

        <SequenceFragmentCard
            title="Supporting Sequence Fragments"
            description="Residue-level evidence regions associated with OPUS predictions."
            :items="fragments"
        />

        <ExternalDatabaseCard
            title="External Database Sequences"
            description="UniRef50 matches grouped by EC number."
            :groups="externalSequenceGroups"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SequenceInputPanel from '../components/SequenceInputPanel.vue'
import EcPredictionCard from '../components/EcPredictionCard.vue'
import SequenceFragmentCard from '../components/SequenceFragmentCard.vue'
import ExternalDatabaseCard from '../components/ExternalDatabaseCard.vue'

const sequenceText = ref('')
const loading = ref(false)

const predictions = ref([])
const fragments = ref([])
const externalSequenceGroups = ref([])

const fillExample = () => {
  sequenceText.value = 'MRIIYLISTVLLIYTNATVLRTKESIQNKVTYDKYGFQPLCISCTGLISVASFFLKFDVSEPVILEFATIVCKLFAKQPWAVCDGISSQFRDEFFYVFRRLANESPSQICGIILPDCADPTDPSESGWMVALPPKPKRTRISKKKVQKKPNMSMSQNLNVLQLTDLHVDFEYKYPSEANCDDPVCCRVSVSEPKKAAGYWGSVGKCDIPFWTVENMLSHINKTHMIDMVIMTGDYINHVDWEYSIEEHLSVLRKLHRLVQNTFPSTPIYWALGNHEGVPVNSFAPHSVDERFWPTWLYKEFQTMSGPWLSEGAKDSLLKRGSYSTQVMDGLKLITLNTGFCEVTNFFLYLNQSDPDSSMSWFVKELFESEKKGEQVYVLAHIPPGDSECLEGWAFNYYRVIQRFSSTIAAQFFGHDHLDYFTVFYEDMHNVSSKPISVGYASPSVTTFEYQNPAYRIYEIDPYNKFKIVDFTTYYADLEKATEDKKPVWEKLYSARQAHGMDDLSPLSWNKVIQKLFTSEKKREKFYQYAFRNFSPQCDSTCQMQLMCNLRMGHHNSTLYCPTF'
}

const clearInput = () => {
  sequenceText.value = ''
  predictions.value = []
  fragments.value = []
  externalSequenceGroups.value = []
}

const submitSequence = async () => {
  if (!sequenceText.value.trim()) {
    alert('Please input an amino acid sequence first.')
    return
  }

  loading.value = true

  predictions.value = []
  fragments.value = []
  externalSequenceGroups.value = []

  try {
    const response = await fetch('http://8.130.190.195:8000/api/predict', {
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
    console.log('后端返回 data =', data)

    predictions.value = Array.isArray(data.predictions)
        ? data.predictions
        : []

    fragments.value = Array.isArray(data.fragments)
        ? data.fragments
        : []

    externalSequenceGroups.value = Array.isArray(data.externalSequenceGroups)
        ? data.externalSequenceGroups
        : []
  } catch (error) {
    console.error('请求失败：', error)
    alert('Prediction failed. Please check FastAPI backend.')
  } finally {
    loading.value = false
  }
}
</script>