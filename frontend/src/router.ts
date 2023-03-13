import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/Auth";


const router = createRouter({
  history: createWebHistory("/dashboard/"),
  routes: [
    { path: "/", name: "root", component: () => import("@/pages/Root.vue") },
    {
      path: "/records",
      name: "records",
      component: () => import("@/pages/Records.vue")
    },
    {
      path: "/record/:id",
      name: "record",
      component: () => import("@/pages/Record.vue")
    },
    //{ path: "/record/:id", name: "record", component: Record },
    {
      path: "/logs",
      name: "logs",
      component: () => import("@/pages/Logs.vue")
    },
    //{ path: "/logs:id", name: "log", component: Log },
    {
      path: "/login",
      name: "login",
      component: () => import("@/pages/Login.vue")
    },
  ],
});

router.beforeEach(async (to, _) => {
  const authStore = useAuthStore();
  if (to.name !== "login" && await authStore.isAuthenticated == false) {
    console.log("going to login");
    return { name: "login" };
  }
});

export { router };
