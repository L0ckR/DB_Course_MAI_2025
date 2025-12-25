const API_BASE = import.meta.env.VITE_API_URL || "/api";

export async function apiFetch(path, options = {}, session = null) {
  const headers = new Headers(options.headers || {});
  if (session?.user_id) {
    headers.set("X-User-Id", session.user_id);
  }

  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const payload = await safeJson(response);
    const message = payload?.detail || response.statusText;
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return safeJson(response);
}

async function safeJson(response) {
  try {
    return await response.json();
  } catch (err) {
    return null;
  }
}
