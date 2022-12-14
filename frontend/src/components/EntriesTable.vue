<template>
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
      <tr v-for="entri in props.entries" :key="entri.persistent_url">
        <td>{{ entri.persistent_url }}</td>
        <td>{{ entri.resource_url }}</td>
        <td>{{ entri.enabled }}</td>
        <td>
          <router-link
            class="nav-link"
            :to="{
              name: 'entri',
              params: { persistent_url: entri.persistent_url },
            }"
          >
            <i class="bi bi-info-circle-fill"></i>
          </router-link>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
  const props = defineProps(["entries"]);
</script>
