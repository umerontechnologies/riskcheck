const API_BASE = import.meta.env.VITE_API_BASE || "";

async function httpJson(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let data = null;
  const text = await res.text().catch(() => "");
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    const message =
      (data && data.detail && (typeof data.detail === "string" ? data.detail : null)) ||
      (data && data.error) ||
      `HTTP ${res.status}`;
    throw new Error(message);
  }
  return data;
}

export async function createCheck(payload) {
  return httpJson("/api/check", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function submitCommunityReport(payload) {
  return httpJson("/api/community/report", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function uploadFile(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(API_BASE + "/api/upload", {
    method: "POST",
    body: fd,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = (data && data.detail) || `Upload failed (HTTP ${res.status})`;
    throw new Error(message);
  }
  return data;
}

export function reportPdfUrl(id) {
  return API_BASE + `/api/report/${id}/pdf`;
}

export function fileUrl(sha256) {
  return API_BASE + `/api/file/${sha256}`;
}
