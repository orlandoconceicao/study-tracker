import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
});
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("study_access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("study_access_token");
      localStorage.removeItem("study_refresh_token");
      window.dispatchEvent(new Event("study-session-expired"));
    }
    return Promise.reject(error);
  },
);
export default api;
