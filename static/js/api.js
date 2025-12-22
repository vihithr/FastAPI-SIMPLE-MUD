const API_BASE = window.location.origin;

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export async function request(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }
  const res = await fetch(API_BASE + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data;
  try {
    data = await res.json();
  } catch {
    data = await res.text();
  }

  if (!res.ok) {
    throw new ApiError(`HTTP ${res.status}`, res.status, data);
  }
  return data;
}

export const register = (username, password) =>
  request("/register", { method: "POST", body: { username, password } });

export const login = (username, password) =>
  request("/login", { method: "POST", body: { username, password } });

export const createCharacter = (name, token) =>
  request("/character/create", {
    method: "POST",
    body: { name },
    token,
  });

export const getCharacter = (token) =>
  request("/character", { token });

export const healthCheck = () =>
  request("/health");


