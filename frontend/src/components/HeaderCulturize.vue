<template>
  <nav class="navbar navbar-expand-lg navbar-light culturize">
    <div class="container-fluid">
      <router-link class="navbar-brand" to="/">Culturize-web</router-link>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link
              :class="[
                'nav-link',
                currentPathName === 'record' || currentPathName === 'records'
                  ? 'active'
                  : '',
              ]"
              to="/records"
              >Records
            </router-link>
          </li>
          <li class="nav-item">
            <router-link
              :class="['nav-link', currentPathName === 'logs' ? 'active' : '']"
              to="/logs"
              >Logs
            </router-link>
          </li>
        </ul>
        <div class="d-flex btn-group" role="group" aria-label="Basic example">
          <!-- <button class="btn btn-dark" type="submit" @click="logsdownload">Download Logs</button> -->
          <button class="btn btn-dark" type="submit" @click="refresh">
            <i class="bi bi-arrow-counterclockwise"></i>
          </button>
          <button class="btn btn-dark" type="submit" @click="logout">Logout</button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/Auth";
import { culturize_web } from "@/api/api";
import { useRecordsStore } from "@/stores/Records";
const store = useRecordsStore();

const router = useRouter()
const route = useRoute()

const currentPathName = computed(() => {
  return route.name;
})

const authStore = useAuthStore();

const logout = () => {
  authStore.logout();
  router.push({ name: "login" });
}

const logsdownload = async () => {
  await store.logCSVDownload();
}

const refresh = () => {
  window.location.reload()
}
</script>

<style scoped>
.culturize {
  background-color: #1CD2A7;
}
</style>
