// frontend/src/api.js
const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(
      `API ${path} failed: ${res.status} ${res.statusText} — ${text}`
    );
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  health() {
    return request("/health");
  },
  stats() {
    return request("/stats");
  },
  students(limit = 500) {
    return request(`/students?limit=${limit}`);
  },
  bookings(limit = 500) {
    return request(`/bookings?limit=${limit}`);
  },
  sessions(limit = 500) {
    return request(`/sessions?limit=${limit}`);
  },
  orders(limit = 500) {
    return request(`/orders?limit=${limit}`);
  },

  // inline editing of students
  updateStudent(id, patch) {
    return request(`/students/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    });
  },

  // ARC import hook
  importStudentCerts(id) {
    return request(`/students/${id}/import_certs`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },
};