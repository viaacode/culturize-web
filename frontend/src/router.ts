import { createRouter, createWebHistory } from "vue-router";
//import { Entrie } from "@/pages/Entry.vue";
//import { Logs } from "@/pages/Logs.vue";
//import { Log } from "@/pages/Log.vue";


const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "root", redirect: "/entries" },
    { path: "/entries", name: "entries", component: () => import("@/pages/Entries.vue") },
    //{ path: "/entries", name: "entries", component: Entries },
    //{ path: "/entry/:id", name: "entry", component: Entrie },
    { path: "/logs", name: "logs", component: () => import("@/pages/Logs.vue") },
    //{ path: "/logs:id", name: "log", component: Log },
  ],
});

export { router };
