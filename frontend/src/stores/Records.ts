import { defineStore } from "pinia";
import { mande } from "mande";
import { culturize_web } from "@/api/api";

export interface Log {
  datetime: string;
  persistent_url: string;
  referer: string;
}
export interface PaginatedLog {
  count: number;
  next: string | undefined;
  previous: string | undefined;
  results: Log[];
}

interface PaginatedLogMap {
  [key: number]: PaginatedLog;
}

export interface CRecord {
  id: number;
  resource_url: string;
  persistent_url: string;
  enabled: boolean;
}
export interface PaginatedRecord {
  count: number;
  next: string | undefined;
  previous: string | undefined;
  results: CRecord[];
}

interface PaginatedRecordMap {
  [key: number]: PaginatedRecord;
}

export interface CRecordLogs {
  click_count: number;
}

interface CRecordMap {
  [index: string]: CRecord;
}

interface CRecordsLogsMap {
  [index: string]: CRecordLogs;
}
export interface ServiceInfo {
  record_count: number;
  enabled_count: number;
  click_count: number;
}


export const useRecordsStore = defineStore("record", {
  state: () => ({
    record_count: 0 as number,
    record_page_size: 0 as number,
    record_page: {} as PaginatedRecordMap,
    record_details: {} as CRecordMap,
    log_count: 0 as number,
    log_page_size: 0 as number,
    log_page: {} as PaginatedLogMap,
    recordLogs: {} as CRecordsLogsMap,
    serviceInfo: {} as ServiceInfo
  }),
  actions: {
    // add page to fetch
    async fetch(page: number) {
      const data = await culturize_web.get<PaginatedRecord>("record", {query: {"page": page}});

      this.record_count = data.count;
      this.record_page[page] = data;
      if (page == 1) {
        this.record_page_size = data.results.length;
      }
    },
    async fetchLogs(page: number) {
      const data = await culturize_web.get<PaginatedLog>("logs", {query: {"page": page}});
      console.log("got logs for page", page);

      this.log_count = data.count;
      this.log_page[page] = data;
      if (page == 1) {
        this.log_page_size = data.results.length;
      }
    },
    async fetchRecord(id: string) {
      const data = await culturize_web.get<CRecord>(`record/${id}`);

      this.record_details[id] = data;
    },
    async fetchRecordLogs(id: string) {
      const data = await culturize_web.get<CRecordLogs>(`logs/${id}`);

      this.recordLogs[id] = data;
    },
    reset() {
      this.$reset();
    },
    async fetchServiceInfo() {
      const data = await culturize_web.get<ServiceInfo>("info");

      this.serviceInfo = data;
    },
    async logCSVDownload() {
      const resp = await culturize_web.get<any>("logexport", { responseAs: "response" });
      const data = await resp.blob();
      const blob = new Blob([data], { type: "text/csv" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "export.csv";
      link.click();
      URL.revokeObjectURL(link.href);
    },

    async toggleEnable(id: string) {
      this.record_details[id].enabled = !this.record_details[id].enabled;
      const data = await culturize_web.put<CRecord>(`record/${id}`, this.record_details[id]);

      this.record_details[id] = data;
    }


  },
});
