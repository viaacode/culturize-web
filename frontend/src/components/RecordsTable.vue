<template>
  <div class="container-xl">
    <div>
      <div style="text-align: center" class="my-2 col">
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

const state = reactive({ currentPage: 1})

async function handlePageChange(page: number) {
  await store.fetch(page);
  state.currentPage = page;
}
function prevPage () {
  if (state.currentPage > 1) {
    handlePageChange(state.currentPage-1);
  }
}
function nextPage () {
  if (state.currentPage * store.record_page_size < store.record_count) {
    handlePageChange(state.currentPage+1);
  }
}
</script>

<style scoped>
.culturize {
  background-color: #1CD2A7;
  border-color: #1CD2A7;
}
</style>
