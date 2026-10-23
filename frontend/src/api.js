/**
 * B2/B5 — Authenticated fetch wrapper.
 *
 * Attaches the stored JWT as an Authorization: Bearer header to every request.
 * All protected API calls in the application must use apiFetch instead of
 * the raw fetch() function.
 *
 * B7 — Token expiry handling:
 * If the server responds with 401, the stored token and user are cleared and
 * the page reloads so the user is redirected to the login screen.
 * The original Response object is still returned so callers can inspect it.
 */
export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem("prj221_token");
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, { ...options, headers });

  // B7 — Global 401 handler: expired or invalid token → force logout.
  if (response.status === 401) {
    localStorage.removeItem("prj221_token");
    localStorage.removeItem("prj221_user");
    // Reload the page; App.jsx will render AuthPage because currentUser is null.
    window.location.reload();
  }

  return response;
}
