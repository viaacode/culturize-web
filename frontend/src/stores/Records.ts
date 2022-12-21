import { defineStore } from "pinia";
import { mande } from "mande";
import { culturize_web } from "@/api/api";

export interface Log {
  datetime: string;
  persistent_url: string;
  referer: string;
}
export interface CRecord {
  id: number;
  resource_url: string;
  persistent_url: string;
  enabled: boolean;
}
export interface CRecordLogs {
  click_count: number;
}

interface CRecordsMap {
  [index: string]: CRecord;
}

interface CRecordsLogsMap {
  [index: string]: CRecordLogs;
}


export const useRecordsStore = defineStore("record", {
  state: () => ({
    records: {} as CRecordsMap,
    logs: [] as Array<Log>,
    recordLogs: {} as CRecordsLogsMap,
  }),
  actions: {
    async fetch() {
      const data = await culturize_web.get<CRecord[]>("record");

      for (const record of data) {
        this.records[record.id] = record;
      }
    },
    async fetchLogs() {
      const data = await culturize_web.get<
        { persistent_url: string; datetime: string; referer: string }[]
      >("logs");

      this.logs = data;
    },
    async fetchRecordLogs(id: string) {
      const data = await culturize_web.get<CRecordLogs>(`logs/${id}`);

      this.recordLogs[id] = data;
    },
    reset() {
      this.$reset();
    }
  },
});
