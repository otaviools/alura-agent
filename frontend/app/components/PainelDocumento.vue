<script setup lang="ts">
import type { DocumentoResumo } from "~/services/apiDocsy";

const { documento } = defineProps<{ documento: DocumentoResumo }>();
defineEmits<{ remover: [] }>();

const dados = computed(() => [
  { rotulo: "Paginas", valor: String(documento.totalPaginas) },
  { rotulo: "Paginas com texto", valor: String(documento.paginasComTexto) },
  { rotulo: "Tamanho", valor: formatarTamanho(documento.tamanhoBytes) },
]);

function formatarTamanho(bytes: number): string {
  const mega = bytes / (1024 * 1024);
  return mega >= 1
    ? `${mega.toFixed(1).replace(".", ",")} MB`
    : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}
</script>

<template>
  <UCard :ui="{ body: 'p-4 sm:p-4' }">
    <div class="flex items-start gap-3">
      <UIcon
        name="i-lucide-file-text"
        class="size-5 shrink-0 text-primary mt-0.5"
      />

      <div class="min-w-0 flex-1">
        <h2 class="text-sm text-highlighted break-word">
          {{ documento.nomeArquivo }}
        </h2>

        <dl class="mt-2 space-y-1 text-xs text-muted">
          <div
            v-for="item in dados"
            :key="item.rotulo"
            class="flex justify-between gap-2"
          >
            <dt>{{ item.rotulo }}</dt>
            <dd class="text-default">{{ item.valor }}</dd>
          </div>
        </dl>
      </div>

      <UButton
        icon="i-lucide-x"
        color="neutral"
        variant="ghost"
        size="xs"
        aria-label="Remover documento"
        @click="$emit('remover')"
      />
    </div>

    <UAlert
      v-if="documento.aviso"
      color="warning"
      variant="soft"
      icon="i-lucide-triangle-alert"
      :description="documento.aviso"
      class="mt-4"
      :ui="{ description: 'text-xs' }"
    />
  </UCard>
</template>
