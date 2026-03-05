<script setup lang="ts">
// PDAM Chatbot AI - Main App Entry
useHead({
  titleTemplate: (titleChunk) => {
    return titleChunk ? `${titleChunk} | PDAM Chatbot` : 'PDAM Chatbot AI'
  }
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
