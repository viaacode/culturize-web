import { defineStore } from "pinia"
import { useRecordsStore } from "@/stores/Records";
import { culturize_web } from "@/api/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    apikey: "",
  }),
  getters: {
    async isAuthenticated(state) {
      if (this.apikey !== "") {
        return true;
      }
      const username = localStorage.getItem("username");
      const password = localStorage.getItem("password");
      if (password !== null) {
        this.apikey = password;
        culturize_web.options.headers = { "Culturize-Key": password };
        const recordsStore = useRecordsStore();
        await recordsStore.fetch(1);
        await recordsStore.fetchLogs(1);
        return true;
      }
      return false;
    }
  },
  actions: {
    async login(username: string, password: string) {
      this.apikey = password;
      culturize_web.options.headers = { "Culturize-Key": password };
      try {
        const resp = await culturize_web.post("login", {}, { responseAs: "response" });
        console.log(resp);
        if (resp.status == 200) {
          localStorage.setItem("password", this.apikey);
          localStorage.setItem("username", username);
          const recordsStore = useRecordsStore();
          await recordsStore.fetch(1);
          await recordsStore.fetchLogs(1);
        } else {
          this.apikey = "";
          culturize_web.options.headers = { "Culturize-Key": "" };
        }
      } catch {
        this.apikey = "";
        culturize_web.options.headers = { "Culturize-Key": "" };
      }
    },
    logout() {
      this.apikey = "";
      this.$reset();
      const recordsStore = useRecordsStore();
      recordsStore.reset();
      culturize_web.options.headers = { "Culturize-Key": "" };
      localStorage.removeItem("password");
      localStorage.removeItem("username");
    }

  }
})

