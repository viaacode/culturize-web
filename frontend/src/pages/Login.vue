<template>
  <div class="container">
    <div class="div-center">
      <div class="form-content">
        <img class="mb-5" src="@/img/logo-culturize.png" />
        <h1>Login</h1>
        <hr />
        <div v-if="error != ''" class="alert alert-danger" role="alert">
          <span v-if="error !== ''">{{ error }}</span>
        </div>
        <form @submit.prevent="submitLoginForm">
          <div class="form-group mb-3">
            <label class="mb-1" for="username">Username</label>
            <input
              type="username"
              v-model="username"
              class="form-control"
              id="username"
              required
            />
          </div>
          <div class="form-group mb-3">
            <label class="mb-1" for="password">Password</label>
            <input
              type="password"
              v-model="password"
              class="form-control"
              id="password"
              required
            />
          </div>
          <button type="submit" class="btn btn-light culturize">Submit</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { useAuthStore } from "@/stores/Auth";
import { router } from "@/router";
export default {
  data() {
    return {
      username: "",
      password: "",
      error: "",
    };
  },
  methods: {
    async submitLoginForm() {
      // Perform login action here
      const authStore = useAuthStore();
      await authStore.login(this.username, this.password);
      if (await authStore.isAuthenticated) {
        router.push({ name: "records" });
      } else {
        this.error = "login failed";
      }
    },
  },
};
</script>

<style scoped>
.culturize {
  background-color: #1CD2A7;
}
.div-center {
  width: 400px;
  height: 400px;
  background-color: #fff;
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  margin: auto;
  max-width: 100%;
  max-height: 100%;
  overflow: auto;
  padding: 1em 2em;
  display: table;
}

div.form-content {
  display: table-cell;
  vertical-align: middle;
}
</style>
