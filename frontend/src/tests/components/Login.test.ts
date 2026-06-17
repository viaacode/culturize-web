// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createTestingPinia } from "@pinia/testing";
import Login from "@/pages/Login.vue";
import { useAuthStore } from "@/stores/Auth";

// vi.mock is hoisted before variable declarations, so use vi.hoisted() to
// define the spy before the factory runs.
const mockPush = vi.hoisted(() => vi.fn());

vi.mock("@/router", () => ({
  router: { push: mockPush },
}));

function mountLogin(loginImpl?: () => Promise<void>) {
  return mount(Login, {
    global: {
      plugins: [
        createTestingPinia({
          createSpy: vi.fn,
          stubActions: false,
        }),
      ],
    },
  });
}

describe("Login component", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("renders username and password fields", () => {
    const wrapper = mountLogin();
    expect(wrapper.find('input[type="username"]').exists()).toBe(true);
    expect(wrapper.find('input[type="password"]').exists()).toBe(true);
  });

  it("renders a submit button", () => {
    const wrapper = mountLogin();
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it("does not show error message initially", () => {
    const wrapper = mountLogin();
    const alert = wrapper.find(".alert-danger");
    // The alert is hidden when error is empty
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  });

  it("shows error when login fails", async () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: { auth: { apikey: "" } },
          }),
        ],
      },
    });

    const authStore = useAuthStore();
    // login action is stubbed by createTestingPinia — simulate it doing nothing (apikey stays "")
    authStore.login = vi.fn().mockResolvedValue(undefined) as typeof authStore.login;
    (authStore as any).isAuthenticated = Promise.resolve(false);

    await wrapper.find('input[type="username"]').setValue("user");
    await wrapper.find('input[type="password"]').setValue("wrongkey");
    await wrapper.find("form").trigger("submit");
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[role="alert"]').exists()).toBe(true);
    expect(wrapper.find('[role="alert"]').text()).toContain("login failed");
  });

  it("binds v-model to username and password fields", async () => {
    const wrapper = mountLogin();
    await wrapper.find('input[type="username"]').setValue("testuser");
    await wrapper.find('input[type="password"]').setValue("testpass");

    expect((wrapper.vm as any).username).toBe("testuser");
    expect((wrapper.vm as any).password).toBe("testpass");
  });
});
