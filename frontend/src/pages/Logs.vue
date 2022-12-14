<template>
<nav style="padding-left: 10px;" aria-label="breadcrumb">
</nav>
  <logs-table :logs="store.logs" />
</template>

<script setup lang="ts">
  import LogsTable from "@/components/LogsTable.vue";
  import { useEntriesStore } from "@/stores/Entries";
  const store = useEntriesStore();
  store.fetchLogs();
</script>
