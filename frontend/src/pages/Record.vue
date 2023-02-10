<template>
  <div class="container">
    <h1>Record details</h1>
    <table class="table table-hover">
      <tbody>
        <tr>
          <th scope="row">Persistend URL</th>
          <td v-if="state.record !== undefined">{{ state.record.persistent_url }}</td>
        </tr>
        <tr>
          <th scope="row">Resource URL</th>
          <td v-if="state.record !== undefined">{{ state.record.resource_url }}</td>
        </tr>
        <tr>
          <th scope="row">Enabled</th>
          <td v-if="state.record !== undefined">{{ state.record.enabled }}</td>
        </tr>
        <tr>
          <th scope="row">Click count</th>
          <td v-if="state.recordLogs !== undefined">{{ state.recordLogs.click_count }}</td>
        </tr>
      </tbody>
    </table>
  </div>


</template>

<script setup lang="ts">
import { reactive, onMounted } from "vue";
import { mapState } from "pinia";
import { useRoute } from "vue-router";
import { useRecordsStore } from "@/stores/Records";
import type { CRecord, CRecordLogs } from "@/stores/Records";
const route = useRoute();
const id = route.params.id as string;

interface i_state {
  record: CRecord | undefined
  recordLogs: CRecordLogs | undefined
}

const state: i_state = reactive({ record: undefined, recordLogs: undefined });


onMounted( async () => {
  const recordStore = useRecordsStore();
  await Promise.all([recordStore.fetchRecord(id), recordStore.fetchRecordLogs(id)]);
  state.record = recordStore.record_details[id];
  state.recordLogs = recordStore.recordLogs[id];
});

</script>
