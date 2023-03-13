<template>
  <div class="container-xl">
    <div class="w-100">
      <div style="float: left; text-align: center" class="my-2 col w-75">
        <button
          @click="prevPage"
          type="button"
          class="mx-1 culturize btn btn-primary"
        >
          Previous
        </button>
        <button
          @click="nextPage"
          type="button"
          class="mx-1 culturize btn btn-primary"
        >
          Next
        </button>
      </div>
      <div style="float: right" class="col-1 w-25 my-2">
        <button
          @click="logsdownload"
          type="button"
          class="mx-1 btn btn-dark"
        >
          Download Logs
        </button>
      </div>
    </div>

    <table class="table table-hover">
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Persistent URL</th>
          <th>Referer</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="log in store.log_page[state.currentPage].results"
          :key="log.persistent_url">
          <td>{{ log.datetime }}</td>
          <td>{{ log.persistent_url }}</td>
          <td>{{ log.referer }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, ref } from "vue";
import { useRecordsStore } from "@/stores/Records";
const store = useRecordsStore();

const state = reactive({ currentPage: 1})

async function handlePageChange(page: number) {
  await store.fetchLogs(page);
  state.currentPage = page;
}
function prevPage () {
  if (state.currentPage > 1) {
    handlePageChange(state.currentPage-1);
  }
}
function nextPage () {
  if (state.currentPage * store.log_page_size < store.log_count) {
    handlePageChange(state.currentPage+1);
  }
}

const logsdownload = async () => {
  await store.logCSVDownload();
}

</script>

<style scoped>
.culturize {
  background-color: #1CD2A7;
  border-color: #1CD2A7;
}
</style>
