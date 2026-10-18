export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem("prj221_token");
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(url, { ...options, headers });
}
