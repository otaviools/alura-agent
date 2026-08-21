<script setup lang="ts">
import type { NavigationMenuItem } from "@nuxt/ui";
import type { MensagemChat } from "~/composables/useDocsy";

const {
  documento,
  mensagens,
  erro,
  enviandoArquivo,
  estado,
  carregarArquivo,
  descartarDocumento,
  fazerPergunta,
} = useDocsy();

const SUGESTOES = [
  "Faça um resumo do documento",
  "Quais são os prazos citados?",
  "Liste as obrigações descritas",
];

const open = ref(true);
const arquivo = ref<File | null>(null);
const pergunta = ref("");

watch(arquivo, carregarArquivo);

const acoes = computed<NavigationMenuItem[]>(() =>
  documento.value
    ? [
        { label: documento.value.nomeArquivo, icon: "i-lucide-file-text" },
        {
          label: "Enviar outro PDF",
          icon: "i-lucide-repeat-2",
          onSelect: trocarDocumento,
        },
      ]
    : [
        {
          label: "Envie um PDF",
          icon: "i-lucide-file-up",
          onSelect: () => (open.value = true),
        },
      ],
);

function enviar(texto = pergunta.value) {
  pergunta.value = "";
  fazerPergunta(texto);
}

async function trocarDocumento() {
  await descartarDocumento();
  arquivo.value = null;
}
</script>

<template>
  <div class="flex flex-1 min-h-0 min-w-0 overflow-hidden">
    <USidebar
      v-model:open="open"
      collapsible="icon"
      :style="{
        '--sidebar-width': open ? '18rem' : 'var(--sidebar-width-icon)',
      }"
      :ui="{ container: 'h-full' }"
    >
      <template #header="{ state, close }">
        <span
          class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-inverted"
          aria-hidden="true"
        >
          <UIcon name="i-lucide-file-search" class="size-4" />
        </span>

        <div v-if="state === 'expanded'" class="min-w-0 flex-1">
          <h1 class="text-base px-2 leading-tight text-highlighted">Docsy</h1>
        </div>

        <UButton
          v-if="state === 'expanded'"
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          class="lg:hidden"
          aria-label="Fechar o painel"
          @click="close"
        />
      </template>

      <template #default="{ state }">
        <template v-if="state === 'expanded'">
          <UFileUpload
            v-if="!documento"
            v-model="arquivo"
            accept="application/pdf"
            icon="i-lucide-file-up"
            :label="enviandoArquivo ? 'Lendo o documento' : 'Envie um PDF'"
            :description="
              enviandoArquivo
                ? 'Extraindo o texto pagina a pagina.'
                : 'Arraste o arquivo aqui ou clique para escolher.'
            "
            :disabled="enviandoArquivo"
            :preview="false"
            class="min-h-48"
          />

          <PainelDocumento
            v-else
            :documento="documento"
            @remover="trocarDocumento"
          />
        </template>
        <UNavigationMenu
          :items="acoes"
          :collapsed="state === 'collapsed'"
          orientation="vertical"
          tooltip
          :ui="{ link: 'p-1.5 overflow-hidden' }"
        />
      </template>

      <template #footer="{ state }">
        <p v-if="state === 'expanded'" class="text-xs text-muted">
          Ate 20 MB e 300 paginas. O arquivo não é gravado em disco e some ao
          sair.
        </p>
      </template>
    </USidebar>

    <div class="flex-1 flex flex-col overflow-hidden bg-default min-w-0">
      <div
        class="h-(--ui-header-height) shrink-0 flex items-center gap-2 border-b border-default px-3 sm:px-4"
      >
        <UButton
          icon="i-lucide-panel-left"
          color="neutral"
          variant="ghost"
          aria-label="Mostrar ou esconder o painel do documento"
          @click="open = !open"
        />
        <span class="text-sm text-muted">Chat</span>
      </div>

      <main class="flex flex-1 flex-col min-h-0 min-w-0 w-full">
        <UAlert
          v-if="erro"
          color="error"
          variant="soft"
          icon="i-lucide-circle-alert"
          :description="erro"
          close
          class="m-4 mb-0"
          @update:open="erro = ''"
        />

        <div
          v-if="!documento"
          class="flex flex-1 items-center justify-center px-6 text-center"
        >
          <p class="text-sm text-muted">
            Envie um PDF para liberar a conversa.
          </p>
        </div>

        <div
          v-else
          class="flex flex-1 flex-col min-h-0 min-w-0 w-full max-w-3xl mx-auto"
        >
          <UChatMessages
            v-if="mensagens.length"
            :messages="mensagens"
            :status="estado"
            :auto-scroll="{ color: 'neutral', variant: 'outline' }"
            class="flex-1 min-w-0 overflow-y-auto p-3 sm:p-4"
          >
            <template #content="{ message }: { message: MensagemChat }">
              <UChatReasoning
                v-if="message.raciocinio"
                :text="message.raciocinio"
                :streaming="message.raciocinando"
                class="mb-2"
              />
              <div class="whitespace-pre-wrap wrap-break-word">
                {{ message.parts.map((p) => p.text).join("") }}
              </div>
            </template>
          </UChatMessages>

          <div
            v-else
            class="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center"
          >
            <UIcon name="i-lucide-messages-square" class="size-9 text-dimmed" />
            <p class="text-sm text-muted">
              Faca a primeira pergunta sobre o documento.
            </p>
            <div class="flex flex-wrap justify-center gap-2">
              <UButton
                v-for="sugestao in SUGESTOES"
                :key="sugestao"
                color="neutral"
                variant="outline"
                size="xs"
                :label="sugestao"
                @click="enviar(sugestao)"
              />
            </div>
          </div>

          <div class="px-3 pb-3 sm:px-4 sm:pb-4">
            <UChatPrompt
              v-model="pergunta"
              variant="soft"
              placeholder="Pergunte algo sobre o documento"
              :maxrows="6"
              class="w-full"
              :ui="{ root: 'px-2 py-1.5 gap-1', body: 'px-1 py-1' }"
              @submit="enviar()"
            >
              <UChatPromptSubmit
                :status="estado"
                color="primary"
                size="sm"
                icon="i-lucide-send-horizontal"
              />
            </UChatPrompt>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
