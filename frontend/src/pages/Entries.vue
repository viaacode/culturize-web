<template>
<nav style="padding-left: 10px;" aria-label="breadcrumb">
</nav>
  <entries-table :entries="store.entries" />
</template>

<script setup lang="ts">
  import EntriesTable from "@/components/EntriesTable.vue";
  import { useEntriesStore } from "@/stores/Entries";
  const store = useEntriesStore();
  store.fetch();
</script>
