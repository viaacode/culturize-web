import { defineStore } from "pinia";
import { mande } from "mande";

export const culturize_web = mande("http://localhost:1337/api");
culturize_web.options.headers = { "Culturize-Key": "meemoosecretbeerstash" };

export const useEntriesStore = defineStore("entries", {
  state: () => ({
    entries: {},
    logs: {},
  }),
  actions: {
    async fetch() {
      const data = await culturize_web.get<
        { persistent_url: string; resource_url: string; enabled: boolean }[]
      >("record");

      this.entries = data;
    },
    async fetchLogs() {
      const data = await culturize_web.get<
        { persistent_url: string; datetime: string; referer: string }[]
      >("logs");

      this.logs = data;
    },
  },
});
