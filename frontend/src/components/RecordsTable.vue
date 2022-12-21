<template>
  <div class="container-xl">
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
        <tr v-for="record in props.records" :key="record.persistent_url">
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
  const props = defineProps(["records"]);
</script>
