<template>
  <div class="container">
    <h1>Record details</h1>
    <table class="table table-hover">
      <tbody>
        <tr>
          <th scope="row">Record count</th>
          <td v-if="state.serviceInfo !== undefined">
            {{ state.serviceInfo.record_count }}
          </td>
        </tr>
        <tr>
          <th scope="row">Enabled Records</th>
          <td v-if="state.serviceInfo !== undefined">
            {{ state.serviceInfo.enabled_count }}
          </td>
        </tr>
        <tr>
          <th scope="row">Total link clicks</th>
          <td v-if="state.serviceInfo !== undefined">
            {{ state.serviceInfo.click_count }}
          </td>
        </tr>
        <tr>
          <th scope="row">CultURIze-web version</th>
          <td>
            v1.1
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from "vue";
import { useRecordsStore } from "@/stores/Records";
import type { ServiceInfo } from "@/stores/Records";

interface i_state {
  serviceInfo: ServiceInfo | undefined;
}

const state: i_state = reactive({ serviceInfo: undefined });

onMounted(async () => {
  const recordStore = useRecordsStore();
  await recordStore.fetchServiceInfo();
  state.serviceInfo = recordStore.serviceInfo;
});

</script>
