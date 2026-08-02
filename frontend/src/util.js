// 표시용 날짜 포맷 (KST). 입력은 ISO 문자열.
export function fmtDateTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("ko-KR", { timeZone: "Asia/Seoul", dateStyle: "medium", timeStyle: "short" });
}
export function fmtDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("ko-KR", { timeZone: "Asia/Seoul" });
}
// datetime-local 입력값(로컬) → ISO. 검색 쿼리용.
export function toISO(local) {
  return local ? new Date(local).toISOString() : "";
}
