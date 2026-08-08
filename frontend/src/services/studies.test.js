import { beforeEach, describe, expect, it, vi } from "vitest";
import api from "./api";
import { studiesApi } from "./studies";

vi.mock("./api", () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() } }));

describe("studiesApi", () => {
  beforeEach(() => vi.clearAllMocks());

  it("maps every operation to the expected endpoint", () => {
    studiesApi.list({ subject: "Math" });
    studiesApi.get(7);
    studiesApi.create({ subject: "Math" });
    studiesApi.update(7, { subject: "Physics" });
    studiesApi.remove(7);
    studiesApi.calendar({ month: 8, year: 2026 });
    studiesApi.statistics();
    expect(api.get).toHaveBeenNthCalledWith(1, "/studies/", { params: { subject: "Math" } });
    expect(api.get).toHaveBeenNthCalledWith(2, "/studies/7/");
    expect(api.post).toHaveBeenCalledWith("/studies/", { subject: "Math" });
    expect(api.patch).toHaveBeenCalledWith("/studies/7/", { subject: "Physics" });
    expect(api.delete).toHaveBeenCalledWith("/studies/7/");
    expect(api.get).toHaveBeenNthCalledWith(3, "/studies/calendar/", { params: { month: 8, year: 2026 } });
    expect(api.get).toHaveBeenNthCalledWith(4, "/studies/statistics/");
  });
});
