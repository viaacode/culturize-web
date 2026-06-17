import { config } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, vi } from "vitest";

config.global.stubs = {
  RouterLink: { template: "<a><slot /></a>" },
  RouterView: { template: "<div />" },
};

// Provide a localStorage implementation that works in any Vitest environment
// (Node.js v22 exposes localStorage as undefined without --localstorage-file).
let _storage: Record<string, string> = {};
const localStorageMock = {
  getItem:    (k: string) => _storage[k] ?? null,
  setItem:    (k: string, v: string) => { _storage[k] = v; },
  removeItem: (k: string) => { delete _storage[k]; },
  clear:      () => { _storage = {}; },
  get length() { return Object.keys(_storage).length; },
  key:        (i: number) => Object.keys(_storage)[i] ?? null,
};

beforeEach(() => {
  _storage = {};
  vi.stubGlobal("localStorage", localStorageMock);
  setActivePinia(createPinia());
  vi.clearAllMocks();
});
