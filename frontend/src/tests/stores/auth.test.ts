import { describe, it, expect, vi, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useAuthStore } from "@/stores/Auth";
import { useRecordsStore } from "@/stores/Records";
import { culturize_web } from "@/api/api";

vi.mock("@/api/api", () => ({
  culturize_web: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    options: { headers: {} as Record<string, string> },
  },
}));

// Use vi.hoisted so this object exists before vi.mock's factory is hoisted.
const mockRecordsStore = vi.hoisted(() => ({
  fetch: vi.fn().mockResolvedValue(undefined),
  fetchLogs: vi.fn().mockResolvedValue(undefined),
  reset: vi.fn(),
  $reset: vi.fn(),
}));

vi.mock("@/stores/Records", () => ({
  useRecordsStore: vi.fn(() => mockRecordsStore),
}));

const mockCulturize = vi.mocked(culturize_web);

describe("Auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockCulturize.options.headers = {};
  });

  describe("login()", () => {
    it("sets apikey and persists to localStorage on success", async () => {
      mockCulturize.post = vi.fn().mockResolvedValue({ status: 200 });
      const store = useAuthStore();
      await store.login("user", "secret-key");

      expect(store.apikey).toBe("secret-key");
      expect(localStorage.getItem("password")).toBe("secret-key");
      expect(localStorage.getItem("username")).toBe("user");
    });

    it("sets the Culturize-Key header on success", async () => {
      mockCulturize.post = vi.fn().mockResolvedValue({ status: 200 });
      const store = useAuthStore();
      await store.login("user", "my-api-key");

      expect((mockCulturize.options.headers as Record<string, string>)["Culturize-Key"]).toBe("my-api-key");
    });

    it("clears apikey on non-200 response", async () => {
      mockCulturize.post = vi.fn().mockResolvedValue({ status: 401 });
      const store = useAuthStore();
      await store.login("user", "bad-key");

      expect(store.apikey).toBe("");
      expect(localStorage.getItem("password")).toBeNull();
    });

    it("clears apikey on network error", async () => {
      mockCulturize.post = vi.fn().mockRejectedValue(new Error("Network error"));
      const store = useAuthStore();
      await store.login("user", "any-key");

      expect(store.apikey).toBe("");
    });

    it("fetches records and logs after successful login", async () => {
      mockCulturize.post = vi.fn().mockResolvedValue({ status: 200 });
      const store = useAuthStore();
      await store.login("user", "key");

      // Both auth store and test share the same mockRecordsStore instance
      expect(mockRecordsStore.fetch).toHaveBeenCalledWith(1);
      expect(mockRecordsStore.fetchLogs).toHaveBeenCalledWith(1);
    });
  });

  describe("logout()", () => {
    it("clears apikey and localStorage", async () => {
      localStorage.setItem("password", "key");
      localStorage.setItem("username", "user");
      mockCulturize.post = vi.fn().mockResolvedValue({ status: 200 });
      const store = useAuthStore();
      await store.login("user", "key");

      store.logout();

      expect(store.apikey).toBe("");
      expect(localStorage.getItem("password")).toBeNull();
      expect(localStorage.getItem("username")).toBeNull();
    });

    it("clears the Culturize-Key header", async () => {
      mockCulturize.post = vi.fn().mockResolvedValue({ status: 200 });
      const store = useAuthStore();
      await store.login("user", "key");

      store.logout();

      expect((mockCulturize.options.headers as Record<string, string>)["Culturize-Key"]).toBe("");
    });
  });

  describe("isAuthenticated getter", () => {
    it("returns true when apikey is set", async () => {
      const store = useAuthStore();
      store.apikey = "existing-key";
      expect(await store.isAuthenticated).toBe(true);
    });

    it("returns false when no key and no localStorage", async () => {
      const store = useAuthStore();
      expect(await store.isAuthenticated).toBe(false);
    });

    it("restores from localStorage and returns true", async () => {
      localStorage.setItem("password", "stored-key");
      const store = useAuthStore();
      const result = await store.isAuthenticated;
      expect(result).toBe(true);
      expect(store.apikey).toBe("stored-key");
    });
  });
});
