<template>
  <nav style="padding-left: 10px" aria-label="breadcrumb"></nav>
  <records-table :records="store.records" />
</template>

<script setup lang="ts">
import RecordsTable from "@/components/RecordsTable.vue";
import { useRecordsStore } from "@/stores/Records";
const store = useRecordsStore();
</script>
