<template>
  <div class="container-xl">
    <div class="w-100">
      <div style="float: left" class="my-2 col w-25 input-group">
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
      <div style="float: right; text-align: center" class="w-75 my-2 col">
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

const state = reactive({ currentPage: 1, recordSearch: store.search_string})

async function handlePageChange(page: number) {
  await store.fetch(page);
  state.currentPage = page;
}
function prevPage() {
  if (state.currentPage > 1) {
    handlePageChange(state.currentPage - 1);
  }
}
function nextPage() {
  if (state.currentPage * store.record_page_size < store.record_count) {
    handlePageChange(state.currentPage + 1);
  }
}
function searchRecord() {
  console.log(state.recordSearch);
  store.searchRecord(state.recordSearch, 1);
}
</script>

<style scoped>
.culturize {
  background-color: #1CD2A7;
  border-color: #1CD2A7;
}
</style>
