<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container-fluid">
      <a class="navbar-brand" href="http://localhost:8000">Culturize-web</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link :class="['nav-link', (currentPathName === 'home') ? 'active' : '']" aria-current="page" to="/">Home</router-link>
          </li>
          <li class="nav-item">
            <router-link :class="['nav-link', (currentPathName === 'entry' || currentPathName === 'entries') ? 'active' : '']" to="/entries">Entries</router-link>
          </li>
          <li class="nav-item">
            <router-link :class="['nav-link', (currentPathName === 'logs') ? 'active' : '']" to="/logs">Logs</router-link>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
 
const router = useRouter()
const route = useRoute()

const currentPathName = computed(() => {
    return route.name;
})

const refresh = () => {
  window.location.reload()
}
</script>
