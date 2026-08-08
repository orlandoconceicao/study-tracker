import api from "./api";
export const studiesApi = {
  list: (params) => api.get("/studies/", { params }),
  get: (id) => api.get(`/studies/${id}/`),
  create: (data) => api.post("/studies/", data),
  update: (id, data) => api.patch(`/studies/${id}/`, data),
  remove: (id) => api.delete(`/studies/${id}/`),
  calendar: (params) => api.get("/studies/calendar/", { params }),
  statistics: () => api.get("/studies/statistics/"),
};
