import axios, { AxiosError } from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  withCredentials: true, // send/receive httpOnly cookies (access_token, refresh_token)
});

// A 401 here means the backend already tried to auto-refresh (see
// get_current_user's dependency logic) and the refresh token itself was
// invalid/expired too — there's no recovering client-side, just send the
// user to login. No manual "call /refresh and retry" logic needed here,
// unlike a typical Express + JWT setup, because the backend handles it.
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Shape of FastAPI's error responses — `detail` is a string for HTTPException,
// but can be an array of validation errors from Pydantic. Narrow it where used.
export interface ApiErrorResponse {
  detail?: string;
}
