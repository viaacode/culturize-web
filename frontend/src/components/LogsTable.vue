<template>
  <div class="container-xl">
    <div class="w-100">
      <div style="float: left; text-align: center" class="my-2 col w-75">
        <button
          v-for="n in state.pageNumbers"
          :key="n"
          v-on:click="goToPage(n)"
          v-bind:class="n === state.currentPage ? 'curpage' : ''"
          type="button"
          class="mx-1 culturize btn btn-primary"
        >
          {{ n }}
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
          :key="log.persistent_url"
        >
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

const state = reactive({ currentPage: 1, pageNumbers: [1] });

onMounted(() => {
  updatePageNumbers();
});

function updatePageNumbers() {
  if (store.log_page_count <= 7) {
    let pageNumbers = [];
    for (let i = 1; i <= store.log_page_count; i++) {
      pageNumbers.push(i);
    }
    state.pageNumbers = pageNumbers;
  } else {
    let pageNumbers = [];
    pageNumbers.push(1);
    let start = 2;
    let end = store.log_page_count - 1;
    if (state.currentPage >= start + 2 && state.currentPage <= end - 2) {
        start = state.currentPage - 2;
        end = state.currentPage + 2;
    } else if (state.currentPage >= start + 2) {
        // state.currentPage > end - 2 => shift start
        start = end - 4
    } else {
        // state.currentPage < start + 2 => shift end
        end = start + 4 // 6
    }
    for (let i = start; i <= end; i++) {
      pageNumbers.push(i);
    }
    pageNumbers.push(store.log_page_count);
    state.pageNumbers = pageNumbers;
  }
}

async function handlePageChange(page: number) {
  await store.fetchLogs(page);
  state.currentPage = page;
  updatePageNumbers();
}
function goToPage(i: number) {
  if (state.currentPage != i) {
    handlePageChange(i);
  }
}

const logsdownload = async () => {
  await store.logCSVDownload();
};
</script>

<style scoped>
.culturize {
  background-color: #1CD2A7;
  border-color: #1CD2A7;
}
.curpage {
  color: #000000;
}
</style>
