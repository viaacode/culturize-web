<template>
  <div class="container-xl">
    <div class="w-100 row">
      <div style="float: left" class="my-2 col-1 w-25 input-group">
        <input
          v-model="state.recordSearch"
          class="form-control border-end-0 border"
          type="search"
          id="recordSearch"
          @keyup.enter="searchRecord"
        >
        <span class="input-group-append">
          <button
            @click="searchRecord"
            class="btn btn-outline-secondary bg-white border-start-0 border ms-n5"
            type="button"
          >
            <i class="bi bi-search"></i>
          </button>
        </span>

        <!-- <input type="search" class="form-control" id="recordSearch"> -->
      </div>
      <div style="float: right; text-align: center" class="w-50 my-2 col">
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
      <div style="float: right; text-align: center" class="col-6 w-25 my-2">
        <button
          @click="recordsdownload"
          type="button"
          class="mx-1 btn btn-dark"
        >
          Download Records
        </button>
      </div>
    </div>

    <table class="table table-hover">
      <thead>
        <tr>
          <th>Persistent URL</th>
          <th>Resource URL</th>
          <th>Enabled</th>
          <th>Actions</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="record in store.record_page[state.currentPage].results"
          :key="record.persistent_url"
        >
          <td>{{ record.persistent_url }}</td>
          <td>{{ record.resource_url }}</td>
          <td>{{ record.enabled }}</td>
          <td>
            <router-link
              class="nav-link"
              :to="{
                name: 'record',
                params: { id: record.id },
              }"
            >
              <i class="bi bi-info-circle-fill"></i>
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, ref } from "vue";
import { useRecordsStore } from "@/stores/Records";
const store = useRecordsStore();

const state = reactive({ currentPage: 1, pageNumbers: [1], recordSearch: store.search_string})

onMounted(() => {
  updatePageNumbers();
});

function updatePageNumbers() {
  if (store.record_page_count <= 7) {
    let pageNumbers = [];
    for (let i = 1; i <= store.record_page_count; i++) {
      pageNumbers.push(i);
    }
    state.pageNumbers = pageNumbers;
  } else {
    let pageNumbers = [];
    pageNumbers.push(1);
    let start = 2;
    let end = store.record_page_count - 1;
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
    pageNumbers.push(store.record_page_count);
    state.pageNumbers = pageNumbers;
  }
}

async function handlePageChange(page: number) {
  await store.fetch(page);
  state.currentPage = page;
  updatePageNumbers();
}

function goToPage(i: number) {
  if (state.currentPage != i) {
    handlePageChange(i);
  }
}
function searchRecord() {
  console.log(state.recordSearch);
  store.searchRecord(state.recordSearch, 1);
}

const recordsdownload = async () => {
  await store.recordCSVDownload();
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
