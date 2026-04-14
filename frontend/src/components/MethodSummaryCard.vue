<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-slate-900">How OPUS-ResInsight Works</h2>
        <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          OPUS-ResInsight combines sequence-level prediction with residue-level interpretation
          to support explainable enzyme annotation and retrieval.
        </p>
      </div>

      <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
        Method overview
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300 hover:bg-slate-50/80">
        <div class="mb-3 flex items-center gap-3">
          <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-semibold text-white">
            1
          </span>
          <div class="text-sm font-semibold text-slate-900">Predict</div>
        </div>

        <p class="text-sm leading-6 text-slate-600">
          Predict EC numbers from the input protein sequence using sequence-level representations.
        </p>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300 hover:bg-slate-50/80">
        <div class="mb-3 flex items-center gap-3">
          <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-semibold text-white">
            2
          </span>
          <div class="text-sm font-semibold text-slate-900">Interpret</div>
        </div>

        <p class="text-sm leading-6 text-slate-600">
          Localize functionally important residues associated with the predicted labels through residue-level evidence.
        </p>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300 hover:bg-slate-50/80">
        <div class="mb-3 flex items-center gap-3">
          <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-semibold text-white">
            3
          </span>
          <div class="text-sm font-semibold text-slate-900">Retrieve</div>
        </div>

        <p class="text-sm leading-6 text-slate-600">
          Retrieve relevant UniRef50 sequences by aligning the identified critical residues for each predicted EC label.
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
</script>