<template>
  <nav style="padding-left: 10px" aria-label="breadcrumb"></nav>
  <logs-table :logs="store.logs" />
</template>

<script setup lang="ts">
  import LogsTable from "@/components/LogsTable.vue";
  import { useRecordsStore } from "@/stores/Records";
  const store = useRecordsStore();
  store.fetchLogs();
</script>
