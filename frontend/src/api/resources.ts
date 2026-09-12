import { apiRequest } from "./client";
import {
  parseDoctorDetail,
  parseDoctorList,
  parseHospitalDetail,
  parseHospitalList,
} from "./schemas";
import type {
  DoctorDetailPayload,
  DoctorListPayload,
  HospitalDetailPayload,
  HospitalListPayload,
} from "../types/api";

export function getHospitals(signal?: AbortSignal): Promise<HospitalListPayload> {
  return apiRequest<HospitalListPayload>("/api/v1/hospitals", {
    signal,
    parseData: parseHospitalList,
  });
}

export function getDoctors(
  options: {
    hospitalId?: number;
    hospitalName?: string;
    department?: string;
    title?: string;
    q?: string;
    page?: number;
    pageSize?: number;
    signal?: AbortSignal;
  } = {},
): Promise<DoctorListPayload> {
  const params = new URLSearchParams();
  if (typeof options.hospitalId === "number") params.set("hospital_id", String(options.hospitalId));
  if (options.hospitalName) params.set("hospital_name", options.hospitalName);
  if (options.department) params.set("department", options.department);
  if (options.title) params.set("title", options.title);
  if (options.q?.trim()) params.set("q", options.q.trim());
  if (typeof options.page === "number") params.set("page", String(options.page));
  if (typeof options.pageSize === "number") params.set("page_size", String(options.pageSize));
  const query = params.toString();
  return apiRequest<DoctorListPayload>(`/api/v1/doctors${query ? `?${query}` : ""}`, {
    signal: options.signal,
    parseData: parseDoctorList,
  });
}

export function getHospitalDetail(id: number, signal?: AbortSignal): Promise<HospitalDetailPayload> {
  return apiRequest<HospitalDetailPayload>(`/api/v1/hospitals/${encodeURIComponent(id)}`, {
    signal,
    parseData: parseHospitalDetail,
  });
}

export function getDoctorDetail(id: number, signal?: AbortSignal): Promise<DoctorDetailPayload> {
  return apiRequest<DoctorDetailPayload>(`/api/v1/doctors/${encodeURIComponent(id)}`, {
    signal,
    parseData: parseDoctorDetail,
  });
}
