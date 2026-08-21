<script setup lang="ts">
import { pt_br } from "@nuxt/ui/locale";
</script>

<template>
  <UApp :locale="pt_br">
    <div class="h-dvh flex flex-col bg-default overflow-hidden">
      <NuxtPage />
    </div>
  </UApp>
</template>
