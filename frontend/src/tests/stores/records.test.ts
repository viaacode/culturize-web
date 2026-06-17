import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { flushPromises } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";
import { useRecordsStore, type PaginatedRecord, type CRecord } from "@/stores/Records";
import { culturize_web } from "@/api/api";

vi.mock("@/api/api", () => ({
  culturize_web: {
    get: vi.fn(),
    put: vi.fn(),
    options: { headers: {} },
  },
}));

const mockCulturize = vi.mocked(culturize_web);

function makeRecord(overrides: Partial<CRecord> = {}): CRecord {
  return {
    id: 1,
    resource_url: "https://example.com",
    persistent_url: "host.example/r1",
    enabled: true,
    status: "ONLINE",
    ...overrides,
  };
}

function makePaginatedRecord(results: CRecord[], count = results.length): PaginatedRecord {
  return { count, next: undefined, previous: undefined, results };
}

describe("Records store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("fetch()", () => {
    it("populates record_page for the requested page", async () => {
      const records = [makeRecord({ id: 1 }), makeRecord({ id: 2, persistent_url: "host.example/r2" })];
      mockCulturize.get = vi.fn().mockResolvedValue(makePaginatedRecord(records));

      const store = useRecordsStore();
      await store.fetch(1);

      expect(store.record_page[1].results).toHaveLength(2);
      expect(store.record_count).toBe(2);
    });

    it("calculates page count correctly", async () => {
      // fetch() sets record_page_size = results.length on page 1.
      // Return 2 results so page_size becomes 2 → 250/2 = 125 pages.
      const results = [makeRecord({ id: 1 }), makeRecord({ id: 2, persistent_url: "host.example/r2" })];
      mockCulturize.get = vi.fn().mockResolvedValue({ count: 250, next: undefined, previous: undefined, results });

      const store = useRecordsStore();
      await store.fetch(1);

      expect(store.record_page_count).toBe(125);
    });

    it("sets page_count to 1 when there are no records", async () => {
      mockCulturize.get = vi.fn().mockResolvedValue(makePaginatedRecord([], 0));
      const store = useRecordsStore();
      await store.fetch(1);
      expect(store.record_page_count).toBe(1);
    });

    it("can cache multiple pages independently", async () => {
      const page1Records = [makeRecord({ id: 1 })];
      const page2Records = [makeRecord({ id: 2, persistent_url: "host.example/r2" })];
      mockCulturize.get = vi.fn()
        .mockResolvedValueOnce(makePaginatedRecord(page1Records, 2))
        .mockResolvedValueOnce(makePaginatedRecord(page2Records, 2));

      const store = useRecordsStore();
      await store.fetch(1);
      await store.fetch(2);

      expect(store.record_page[1].results[0].id).toBe(1);
      expect(store.record_page[2].results[0].id).toBe(2);
    });
  });

  describe("searchRecord()", () => {
    it("sets search_string before fetching", async () => {
      mockCulturize.get = vi.fn().mockResolvedValue(makePaginatedRecord([]));
      const store = useRecordsStore();
      await store.searchRecord("apple", 1);
      expect(store.search_string).toBe("apple");
      expect(mockCulturize.get).toHaveBeenCalledOnce();
    });

    it("passes search string in the query", async () => {
      mockCulturize.get = vi.fn().mockResolvedValue(makePaginatedRecord([]));
      const store = useRecordsStore();
      await store.searchRecord("orange", 1);
      expect(mockCulturize.get).toHaveBeenCalledWith("record", {
        query: { page: 1, search: "orange" },
      });
    });
  });

  describe("fetchLogs()", () => {
    it("populates log_page for the requested page", async () => {
      const logData = {
        count: 1,
        next: undefined,
        previous: undefined,
        results: [{ datetime: "2024-01-01T00:00:00Z", persistent_url: "host.example/r1", referer: "" }],
      };
      mockCulturize.get = vi.fn().mockResolvedValue(logData);
      const store = useRecordsStore();
      await store.fetchLogs(1);
      expect(store.log_page[1].results).toHaveLength(1);
      expect(store.log_count).toBe(1);
    });
  });

  describe("fetchRecord()", () => {
    it("stores single record in record_details", async () => {
      const record = makeRecord({ id: 42, persistent_url: "host.example/detail" });
      mockCulturize.get = vi.fn().mockResolvedValue(record);
      const store = useRecordsStore();
      await store.fetchRecord("42");
      expect(store.record_details["42"].persistent_url).toBe("host.example/detail");
    });
  });

  describe("fetchServiceInfo()", () => {
    it("updates serviceInfo state", async () => {
      const info = {
        record_count: 10,
        enabled_count: 8,
        click_count: 100,
        last_record_export: "2024-01-01",
        last_record_export_filename: "records.zip",
        last_log_export: "2024-01-01",
        last_log_export_filename: "logs.zip",
      };
      mockCulturize.get = vi.fn().mockResolvedValue(info);
      const store = useRecordsStore();
      await store.fetchServiceInfo();
      expect(store.serviceInfo.record_count).toBe(10);
      expect(store.serviceInfo.last_record_export_filename).toBe("records.zip");
    });
  });

  describe("toggleEnable()", () => {
    it("flips enabled and sends PUT", async () => {
      const record = makeRecord({ id: 5, enabled: true });
      mockCulturize.put = vi.fn().mockResolvedValue({ ...record, enabled: false });

      const store = useRecordsStore();
      store.record_details["5"] = record;
      await store.toggleEnable("5");

      expect(mockCulturize.put).toHaveBeenCalledWith("record/5", expect.objectContaining({ enabled: false }));
      expect(store.record_details["5"].enabled).toBe(false);
    });
  });

  describe("waitForNewExport()", () => {
    it("clears interval and sets recordExporting=false when export timestamp changes", async () => {
      const store = useRecordsStore();
      store.serviceInfo = {
        record_count: 0, enabled_count: 0, click_count: 0,
        last_record_export: "old-timestamp",
        last_record_export_filename: "old.zip",
        last_log_export: "", last_log_export_filename: "",
      };
      store.recordExporting = true;
      store.recordIntervalID = 99 as unknown as number;

      const newInfo = { ...store.serviceInfo, last_record_export: "new-timestamp" };
      mockCulturize.get = vi.fn().mockResolvedValue(newInfo);

      const clearSpy = vi.spyOn(globalThis, "clearInterval").mockImplementation(() => {});
      store.waitForNewExport("record");
      // Flush all pending microtasks so the .then() chain inside waitForNewExport runs
      await flushPromises();

      expect(clearSpy).toHaveBeenCalledWith(99);
      expect(store.recordExporting).toBe(false);
      clearSpy.mockRestore();
    });
  });

  describe("reset()", () => {
    it("resets all state to initial values", async () => {
      mockCulturize.get = vi.fn().mockResolvedValue(makePaginatedRecord([makeRecord()]));
      const store = useRecordsStore();
      await store.fetch(1);
      expect(store.record_count).toBe(1);

      store.reset();
      expect(store.record_count).toBe(0);
      expect(store.record_page).toEqual({});
    });
  });
});
