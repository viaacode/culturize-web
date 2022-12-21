<template>
  <div class="container-xl">
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
        <tr v-for="log in props.logs" :key="log.persistent_url">
          <td>{{ log.datetime }}</td>
          <td>{{ log.persistent_url }}</td>
          <td>{{ log.referer }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
  const props = defineProps(["logs"]);
</script>
