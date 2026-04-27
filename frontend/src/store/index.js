import { defineStore } from "pinia";
import http from "../api/http";

const TOKEN_KEY = "access_token";
const PROFILE_KEY = "user_profile";
const ROLE_KEY = "ui_role";
const USER_ID_KEY = "user_id";

function readProfile() {
  try {
    const raw = window.sessionStorage.getItem(PROFILE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: window.sessionStorage.getItem(TOKEN_KEY) || "",
    demoRole: window.sessionStorage.getItem(ROLE_KEY) || "",
    profile: readProfile()
  }),
  getters: {
    role: (state) => state.demoRole || state.profile?.role || "",
    clinicId: (state) => state.profile?.clinic_id || "",
    userId: (state) => Number(state.profile?.id || 0),
    isLoggedIn: (state) => Boolean(state.token),
    username: (state) => state.profile?.username || "",
    displayName: (state) => {
      const username = state.profile?.username || "";
      const realName = state.profile?.full_name || state.profile?.real_name || state.profile?.name || "";
      const map = {
        receptionist1: "前台小王",
        doctor1: "张医生",
        doctor2: "李医生",
        nurse1: "陈护士",
        pharmacist1: "药房李师傅",
        manager1: "周主任",
        admin: "王院长"
      };
      return realName || map[username] || username || "访客";
    }
  },
  actions: {
    /** 设置登录令牌。 */
    setToken(value) {
      this.token = value;
      if (value) {
        window.sessionStorage.setItem(TOKEN_KEY, value);
        const claims = parseJwtPayload(value);
        if (claims) {
          this.setProfile({
            ...(this.profile || {}),
            id: Number(claims.user_id || this.profile?.id || 0) || undefined,
            username: claims.sub || this.profile?.username || "",
            role: claims.role || this.profile?.role || "",
            clinic_id: claims.clinic_id || this.profile?.clinic_id || ""
          });
        }
      } else {
        window.sessionStorage.removeItem(TOKEN_KEY);
        window.sessionStorage.removeItem(ROLE_KEY);
        window.sessionStorage.removeItem(PROFILE_KEY);
        window.sessionStorage.removeItem(USER_ID_KEY);
        this.demoRole = "";
        this.profile = null;
      }
    },
    /** 设置演示态角色。 */
    setDemoRole(role) {
      this.demoRole = role || "";
      if (this.demoRole) {
        window.sessionStorage.setItem(ROLE_KEY, this.demoRole);
      } else {
        window.sessionStorage.removeItem(ROLE_KEY);
      }
    },
    /** 设置当前用户档案。 */
    setProfile(profile) {
      this.profile = profile;
      if (profile) {
        window.sessionStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
        if (profile.id !== undefined && profile.id !== null) {
          window.sessionStorage.setItem(USER_ID_KEY, String(profile.id));
          // WebSocket 连接使用统一 user_id 键
          window.sessionStorage.setItem("user_id", String(profile.id));
        }
      } else {
        window.sessionStorage.removeItem(PROFILE_KEY);
        window.sessionStorage.removeItem(USER_ID_KEY);
        window.sessionStorage.removeItem("user_id");
      }
    },
    /** 从后端加载当前用户信息。 */
    async loadProfile() {
      if (!this.token) return null;
      const result = await http.get("/auth/me");
      this.setProfile(result.data || null);
      return this.profile;
    },
    /** 判断当前角色是否有权限。 */
    hasRole(roles = []) {
      if (!roles || roles.length === 0) return true;
      const normalizeRole = (value) => {
        if (value === "pharmacy") return "pharmacist";
        return value;
      };
      const currentRole = normalizeRole(this.role);
      return roles.map(normalizeRole).includes(currentRole);
    },
    /** 退出登录。 */
    logout() {
      this.setToken("");
      this.profile = null;
    }
  }
});

function parseJwtPayload(token) {
  try {
    const chunks = String(token).split(".");
    if (chunks.length !== 3) return null;
    const normalized = chunks[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
    const json = decodeURIComponent(
      window
        .atob(padded)
        .split("")
        .map((c) => `%${`00${c.charCodeAt(0).toString(16)}`.slice(-2)}`)
        .join("")
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
}

