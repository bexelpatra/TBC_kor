// API 클라이언트 — fetch 래퍼. Bearer 토큰 자동 첨부, 에러 형식 통일.
import router from "../router";

const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export function fileUrl(path) {
  if (!path) return "";
  return path.startsWith("http") ? path : BASE + path;
}

function authHeader() {
  const t = localStorage.getItem("brain_core_kor_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function handle(res) {
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem("brain_core_kor_token");
      localStorage.removeItem("brain_core_kor_actor");
      localStorage.removeItem("brain_core_kor_expires");
      if (router.currentRoute.value.path !== "/login") {
        router.replace("/login");
      }
      throw Object.assign(new Error(""), { code: "UNAUTHORIZED", status: 401 });
    }
    const err = data?.error || { code: "ERROR", message: `요청 실패 (${res.status})` };
    throw Object.assign(new Error(err.message), { code: err.code, status: res.status });
  }
  return data;
}

export const api = {
  base: BASE,
  get(path) {
    return fetch(BASE + path, { headers: { ...authHeader() } }).then(handle);
  },
  post(path, body) {
    return fetch(BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify(body),
    }).then(handle);
  },
  put(path, body) {
    return fetch(BASE + path, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify(body),
    }).then(handle);
  },
  del(path) {
    return fetch(BASE + path, { method: "DELETE", headers: { ...authHeader() } }).then(handle);
  },
  // multipart (파일 업로드) — Content-Type 미지정(브라우저가 boundary 설정)
  upload(path, formData) {
    return fetch(BASE + path, { method: "POST", headers: { ...authHeader() }, body: formData }).then(handle);
  },
  // 파일 다운로드 (blob)
  async download(path) {
    const res = await fetch(BASE + path, { headers: { ...authHeader() } });
    if (!res.ok) throw new Error("다운로드 실패");
    return res.blob();
  },
  // 파일 다운로드 (POST + JSON body, blob 응답)
  async postDownload(path, body) {
    const res = await fetch(BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("다운로드 실패");
    return res.blob();
  },
};
