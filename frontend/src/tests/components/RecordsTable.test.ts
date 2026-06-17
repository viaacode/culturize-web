// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { nextTick } from "vue";
import { mount } from "@vue/test-utils";
import { setActivePinia } from "pinia";
import { createTestingPinia } from "@pinia/testing";
import RecordsTable from "@/components/RecordsTable.vue";
import { useRecordsStore } from "@/stores/Records";
import type { CRecord, PaginatedRecord } from "@/stores/Records";

function makeRecord(id: number, label: string): CRecord {
  return { id, resource_url: `https://${label}.example.com`, persistent_url: `host/${label}`, enabled: true, status: "ONLINE" };
}

function page(results: CRecord[]): PaginatedRecord {
  return { count: results.length, next: undefined, previous: undefined, results };
}

// mountTable is async because onMounted() updates state.pageNumbers reactively;
// Vue flushes that DOM update on the next tick, so callers must await.
async function mountTable(pageCount = 1, records: CRecord[] = [makeRecord(1, "r1")]) {
  const pinia = createTestingPinia({ createSpy: vi.fn });
  setActivePinia(pinia);

  const store = useRecordsStore();
  store.record_page_count = pageCount;
  store.record_page = { 1: page(records) };
  store.search_string = "";
  store.serviceInfo = { last_record_export_filename: "", last_record_export: "" } as any;
  store.recordExporting = false;

  const wrapper = mount(RecordsTable, {
    global: {
      stubs: { RouterLink: { template: "<a><slot /></a>" } },
      plugins: [pinia],
    },
  });
  // onMounted sets state.pageNumbers; wait for Vue to flush that to the DOM.
  await nextTick();
  return wrapper;
}

describe("RecordsTable component", () => {
  describe("table rendering", () => {
    it("renders one row per record", async () => {
      const records = [makeRecord(1, "apple"), makeRecord(2, "orange")];
      const wrapper = await mountTable(1, records);
      expect(wrapper.findAll("tbody tr")).toHaveLength(2);
    });

    it("displays persistent_url and resource_url in row cells", async () => {
      const wrapper = await mountTable(1, [makeRecord(1, "apple")]);
      expect(wrapper.find("tbody tr").text()).toContain("host/apple");
      expect(wrapper.find("tbody tr").text()).toContain("apple.example.com");
    });

    it("displays record status", async () => {
      const record = { ...makeRecord(1, "r1"), status: "OFFLINE" };
      const wrapper = await mountTable(1, [record]);
      expect(wrapper.find("tbody tr").text()).toContain("OFFLINE");
    });
  });

  describe("search", () => {
    it("calls store.searchRecord when search button is clicked", async () => {
      const wrapper = await mountTable();
      const store = useRecordsStore();
      await wrapper.find("input#recordSearch").setValue("apple");
      await wrapper.find("button#search-button").trigger("click");
      expect(store.searchRecord).toHaveBeenCalledWith("apple", 1);
    });

    it("calls store.searchRecord on Enter key in search field", async () => {
      const wrapper = await mountTable();
      const store = useRecordsStore();
      await wrapper.find("input#recordSearch").setValue("mango");
      await wrapper.find("input#recordSearch").trigger("keyup.enter");
      expect(store.searchRecord).toHaveBeenCalledWith("mango", 1);
    });
  });

  describe("pagination buttons", () => {
    it("renders one button per page when ≤7 pages", async () => {
      const wrapper = await mountTable(5);
      const pageButtons = wrapper.findAll("button.culturize");
      expect(pageButtons).toHaveLength(5);
      expect(pageButtons[0].text()).toBe("1");
      expect(pageButtons[4].text()).toBe("5");
    });

    it("renders 7 buttons when >7 pages (windowed)", async () => {
      const wrapper = await mountTable(20);
      const pageButtons = wrapper.findAll("button.culturize");
      // 1 + 5 middle + last = 7
      expect(pageButtons).toHaveLength(7);
      expect(pageButtons[0].text()).toBe("1");
      expect(pageButtons[pageButtons.length - 1].text()).toBe("20");
    });

    it("renders a single button for a single page", async () => {
      const wrapper = await mountTable(1);
      const pageButtons = wrapper.findAll("button.culturize");
      expect(pageButtons).toHaveLength(1);
      expect(pageButtons[0].text()).toBe("1");
    });

    it("clicking a page button calls store.fetch", async () => {
      const wrapper = await mountTable(3, [makeRecord(1, "r1")]);
      const store = useRecordsStore();
      // Override the stub so navigating to page 2 also populates record_page[2].
      // Without this, handlePageChange sets state.currentPage=2 and Vue crashes
      // trying to render store.record_page[2].results, leaking into later tests.
      (store.fetch as ReturnType<typeof vi.fn>).mockImplementation(async (p: number) => {
        store.record_page[p] = page([makeRecord(p, `page${p}`)]);
      });
      const buttons = wrapper.findAll("button.culturize");
      await buttons[1].trigger("click");
      await nextTick();
      expect(store.fetch).toHaveBeenCalledWith(2);
    });
  });

  describe("export buttons", () => {
    it("shows Generate button when not exporting", async () => {
      const wrapper = await mountTable();
      expect(wrapper.find("button.btn-dark").text()).toContain("Generate");
    });

    it("shows spinner when recordExporting is true", async () => {
      const pinia = createTestingPinia({ createSpy: vi.fn });
      setActivePinia(pinia);
      const store = useRecordsStore();
      store.record_page_count = 1;
      store.record_page = { 1: page([makeRecord(1, "r1")]) };
      store.serviceInfo = { last_record_export_filename: "", last_record_export: "" } as any;
      store.recordExporting = true;

      const wrapper = mount(RecordsTable, {
        global: {
          stubs: { RouterLink: { template: "<a><slot /></a>" } },
          plugins: [pinia],
        },
      });
      await nextTick();
      expect(wrapper.find(".spinner-border").exists()).toBe(true);
    });

    it("calls store.triggerRecordExport when Generate is clicked", async () => {
      const wrapper = await mountTable();
      const store = useRecordsStore();
      await wrapper.findAll("button.btn-dark")[0].trigger("click");
      expect(store.triggerRecordExport).toHaveBeenCalledOnce();
    });
  });
});
