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
  last_record_export: string;
  last_record_export_filename: string;
  last_log_export: string;
  last_log_export_filename: string;
}


export const useRecordsStore = defineStore("record", {
  state: () => ({
    search_string: "" as string,
    record_count: 0 as number,
    record_page_size: 100 as number,
    record_page: {} as PaginatedRecordMap,
    record_page_count: 1 as number,
    record_details: {} as CRecordMap,
    log_count: 0 as number,
    log_page_size: 100 as number,
    log_page_count: 1 as number,
    log_page: {} as PaginatedLogMap,
    recordLogs: {} as CRecordsLogsMap,
    serviceInfo: {} as ServiceInfo,
    recordExporting: false as boolean,
    logExporting: false as boolean,
    recordIntervalID: 0 as number,
    logIntervalID: 0 as number
  }),
  actions: {
    // add page to fetch
    async fetch(page: number) {
      const data = await culturize_web.get<PaginatedRecord>("record", {query: {"page": page, "search": this.search_string}});

      this.record_count = data.count;
      this.record_page[page] = data;
      if (page == 1) {
        this.record_page_size = data.results.length;
      }
      if (this.record_count == 0) {
        this.record_page_count = 1;
      } else {
        this.record_page_count = Math.ceil(this.record_count / this.record_page_size);
      }
    },
    async searchRecord(search: string, page: number) {
      this.search_string = search;
      await this.fetch(page);
    },
    async fetchLogs(page: number) {
      const data = await culturize_web.get<PaginatedLog>("logs", {query: {"page": page}});
      console.log("got logs for page", page);

      this.log_count = data.count;
      this.log_page[page] = data;
      if (page == 1) {
        this.log_page_size = data.results.length;
      }
      this.log_page_count = Math.ceil(this.log_count / this.log_page_size);
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
    async triggerLogExport() {
      const resp = await culturize_web.get<any>("logexport", { responseAs: "response" });
      this.logExporting = true;
      this.logIntervalID = setInterval(this.waitForNewExport, 2000, "log");
      console.log(resp);
    },

    async triggerRecordExport() {
      const resp = await culturize_web.get<any>("recordexport", { responseAs: "response" });
      this.recordExporting = true;
      this.recordIntervalID = setInterval(this.waitForNewExport, 2000, "record");
      console.log(resp);
    },

    waitForNewExport(category: string) {
      const prom = culturize_web.get<ServiceInfo>("info");
      
      prom.then((data) => {
        if (category === "record") {
            if (data.last_record_export != this.serviceInfo.last_record_export) {
                // cancel interval call
                this.serviceInfo = data;
                this.recordExporting = false;
                clearInterval(this.recordIntervalID);
            }
        }
        if (category === "log") {
            if (data.last_log_export != this.serviceInfo.last_log_export) {
                // cancel interval call
                this.serviceInfo = data;
                this.logExporting = false;
                clearInterval(this.logIntervalID);
            }
        }
      });
    },

    async toggleEnable(id: string) {
      this.record_details[id].enabled = !this.record_details[id].enabled;
      const data = await culturize_web.put<CRecord>(`record/${id}`, this.record_details[id]);

      this.record_details[id] = data;
    }


  },
});
