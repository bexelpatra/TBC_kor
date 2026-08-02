// 인증 스토어 — 토큰/주체/만료 관리. 토큰은 localStorage 유지.
import { defineStore } from "pinia";
import { api } from "../api/client";

export const useAuth = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("brain_core_kor_token") || "",
    actor: localStorage.getItem("brain_core_kor_actor") || "", // 'user' | 'admin'
    displayName: "",
    role: "",
    level: 0,
    expiresAt: localStorage.getItem("brain_core_kor_expires") || "",
    mustChangePw: false,
  }),
  getters: {
    isAuthed: (s) => !!s.token,
    isAdmin: (s) => s.actor === "admin",
    isUser: (s) => s.actor === "user",
  },
  actions: {
    _persist() {
      localStorage.setItem("brain_core_kor_token", this.token);
      localStorage.setItem("brain_core_kor_actor", this.actor);
      localStorage.setItem("brain_core_kor_expires", this.expiresAt);
    },
    async loginUser(phone_tail, name, password) {
      const d = await api.post("/api/auth/login/user", { phone_tail, name, password });
      this.token = d.access_token;
      this.actor = "user";
      this.expiresAt = d.expires_at;
      this.mustChangePw = d.must_change_pw;
      this._persist();
      await this.fetchMe();
    },
    async loginAdmin(login_id, password) {
      const d = await api.post("/api/auth/login/admin", { login_id, password });
      this.token = d.access_token;
      this.actor = "admin";
      this.expiresAt = d.expires_at;
      this.role = d.role;
      this.level = d.level;
      this.mustChangePw = false;
      this._persist();
      await this.fetchMe();
    },
    async fetchMe() {
      const me = await api.get("/api/auth/me");
      this.displayName = me.display_name;
      this.actor = me.actor;
      this.expiresAt = me.expires_at;
    },
    async changePassword(current, next) {
      await api.post("/api/auth/password", { current, new: next });
      this.mustChangePw = false;
    },
    logout() {
      this.token = "";
      this.actor = "";
      this.displayName = "";
      this.role = "";
      this.level = 0;
      this.expiresAt = "";
      localStorage.removeItem("brain_core_kor_token");
      localStorage.removeItem("brain_core_kor_actor");
      localStorage.removeItem("brain_core_kor_expires");
    },
  },
});
