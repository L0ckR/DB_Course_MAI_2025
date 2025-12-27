const SESSION_KEY = "runatlas.session";

export function getSession() {
  const raw = localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    const session = JSON.parse(raw);
    if (!session?.access_token) {
      return null;
    }
    return session;
  } catch (err) {
    return null;
  }
}

export function saveSession(session) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}
