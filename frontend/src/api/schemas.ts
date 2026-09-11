import type {
  CitySummary,
  DataQualityEvidence,
  EvidenceDataset,
  FollowupAnswer,
  EvidencePayload,
  DoctorDetailPayload,
  MapHospitalRecord,
  MapMarkerType,
  MapPayload,
  ModelSplitMetrics,
  FollowupPayload,
  FollowupOption,
  FollowupQuestion,
  FollowupResponse,
  DoctorListPayload,
  DoctorRecord,
  HospitalDetailPayload,
  HospitalListPayload,
  HospitalRecord,
  RecommendationPayload,
  RecommendedDoctor,
  RecommendedHospital,
  ResourceStrategy,
  ResourceProvenance,
  ResourceDetailPayload,
  TriagePayload,
  TriageStatus,
} from "../types/api";
import { ApiError } from "./client";

const TRIAGE_STATUSES: TriageStatus[] = [
  "EMERGENCY",
  "URGENT",
  "ROUTINE",
  "INSUFFICIENT_INFORMATION",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function requiredString(value: unknown, field: string): string {
  if (typeof value !== "string") {
    throw new ApiError("INVALID_RESPONSE", `服务响应缺少有效的 ${field}。`);
  }
  return value;
}

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function optionalNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function nullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function parseQuestion(value: unknown): FollowupQuestion | null {
  if (!isRecord(value) || typeof value.id !== "string" || typeof value.question !== "string") {
    return null;
  }
  const options: FollowupOption[] = Array.isArray(value.options)
    ? value.options
        .map((option): FollowupOption | null => {
          if (typeof option === "string") return { label: option, value: option };
          if (!isRecord(option) || typeof option.label !== "string" || typeof option.value !== "string") return null;
          return { label: option.label, value: option.value };
        })
        .filter((option): option is FollowupOption => option !== null)
    : [];
  return {
    id: value.id,
    question: value.question,
    options,
    reason: optionalString(value.reason),
  };
}

function parseFollowupAnswers(value: unknown): FollowupAnswer[] | undefined {
  if (!Array.isArray(value)) return undefined;
  return value
    .filter(isRecord)
    .filter((answer) => typeof answer.question_id === "string")
    .map((answer) => ({
      question_id: answer.question_id as string,
      ...(typeof answer.value === "string" ? { value: answer.value } : {}),
      ...(typeof answer.text_answer === "string" ? { text_answer: answer.text_answer } : {}),
    }));
}

export function parseFollowup(value: unknown, field = "followup"): FollowupPayload {
  if (!isRecord(value)) {
    throw new ApiError("INVALID_RESPONSE", `服务响应缺少有效的 ${field}。`);
  }
  const questions = Array.isArray(value.questions)
    ? value.questions.map(parseQuestion).filter((question): question is FollowupQuestion => question !== null)
    : [];
  return {
    needed: value.needed === true,
    confidence: optionalString(value.confidence) ?? "unknown",
    missing_slots: Array.isArray(value.missing_slots)
      ? value.missing_slots.filter((slot): slot is string => typeof slot === "string")
      : [],
    questions,
    topk_comparison: isRecord(value.topk_comparison)
      ? {
          need_compare: value.topk_comparison.need_compare === true,
          focus: Array.isArray(value.topk_comparison.focus)
            ? value.topk_comparison.focus.filter((item): item is string => typeof item === "string")
            : [],
          distinguish_questions: Array.isArray(value.topk_comparison.distinguish_questions)
            ? value.topk_comparison.distinguish_questions
                .map(parseQuestion)
                .filter((question): question is FollowupQuestion => question !== null)
            : [],
        }
      : undefined,
  };
}

export function parseTriagePayload(value: unknown): TriagePayload {
  if (!isRecord(value)) {
    throw new ApiError("INVALID_RESPONSE", "分诊响应格式无法识别。");
  }
  const status = value.triage_status;
  if (typeof status !== "string" || !TRIAGE_STATUSES.includes(status as TriageStatus)) {
    throw new ApiError("INVALID_RESPONSE", "分诊响应缺少有效的安全状态。");
  }
  return {
    condition: requiredString(value.condition, "condition"),
    original_condition: optionalString(value.original_condition),
    followup_answers: parseFollowupAnswers(value.followup_answers),
    matched_department:
      typeof value.matched_department === "string" ? value.matched_department : null,
    triage_status: status as TriageStatus,
    triage: isRecord(value.triage)
      ? {
          ...value.triage,
          followup: isRecord(value.triage.followup)
            ? parseFollowup(value.triage.followup, "triage.followup")
            : undefined,
          red_flag_tags: Array.isArray(value.triage.red_flag_tags)
            ? value.triage.red_flag_tags.filter((tag): tag is string => typeof tag === "string")
            : undefined,
          reasons: Array.isArray(value.triage.reasons)
            ? value.triage.reasons.filter((reason): reason is string => typeof reason === "string")
            : undefined,
        }
      : undefined,
    htriage_analysis: isRecord(value.htriage_analysis)
      ? value.htriage_analysis
      : undefined,
    disease_prediction: value.disease_prediction,
  };
}

export function parseFollowupResponse(value: unknown): FollowupResponse {
  if (!isRecord(value)) {
    throw new ApiError("INVALID_RESPONSE", "追问响应格式无法识别。");
  }
  const status = value.triage_status;
  if (typeof status !== "string" || !TRIAGE_STATUSES.includes(status as TriageStatus)) {
    throw new ApiError("INVALID_RESPONSE", "追问响应缺少有效的安全状态。");
  }
  return {
    condition: requiredString(value.condition, "condition"),
    original_condition: optionalString(value.original_condition),
    followup_answers: parseFollowupAnswers(value.followup_answers),
    matched_department: typeof value.matched_department === "string" ? value.matched_department : null,
    triage_status: status as TriageStatus,
    triage_label: optionalString(value.triage_label),
    followup: parseFollowup(value.followup),
    known_disease: isRecord(value.known_disease) ? value.known_disease : undefined,
    htriage_analysis: isRecord(value.htriage_analysis) ? value.htriage_analysis : undefined,
  };
}

function parseHospital(value: unknown): HospitalRecord {
  if (!isRecord(value)) {
    throw new ApiError("INVALID_RESPONSE", "推荐医院数据格式无法识别。");
  }
  return {
    ...value,
    id: typeof value.id === "number" ? value.id : undefined,
    name: optionalString(value.name),
    alias: optionalString(value.alias),
    level: optionalString(value.level),
    type: optionalString(value.type),
    address: optionalString(value.address),
    phone: optionalString(value.phone),
    emergency: typeof value.emergency === "boolean" ? value.emergency : undefined,
    departments: Array.isArray(value.departments)
      ? value.departments.filter((item): item is string => typeof item === "string")
      : undefined,
    strengths: Array.isArray(value.strengths)
      ? value.strengths.filter((item): item is string => typeof item === "string")
      : undefined,
    derived_capability_areas: Array.isArray(value.derived_capability_areas)
      ? value.derived_capability_areas.filter((item): item is string => typeof item === "string")
      : undefined,
    derived_capability_scores: isRecord(value.derived_capability_scores)
      ? Object.fromEntries(
          Object.entries(value.derived_capability_scores)
            .filter(([, score]) => typeof score === "number")
            .map(([key, score]) => [key, score as number]),
        )
      : undefined,
  };
}

function parseDoctorRecord(value: unknown): DoctorRecord {
  if (!isRecord(value)) {
    throw new ApiError("INVALID_RESPONSE", "医生资料格式无法识别。");
  }
  return {
    ...value,
    id: typeof value.id === "number" ? value.id : undefined,
    name: optionalString(value.name),
    title: optionalString(value.title),
    position: optionalString(value.position),
    department: optionalString(value.department),
    hospital_name: optionalString(value.hospital_name),
    specialty: optionalString(value.specialty),
    outpatient_time: optionalString(value.outpatient_time),
    photo_url: optionalString(value.photo_url),
    specialties: Array.isArray(value.specialties)
      ? value.specialties.filter((item): item is string => typeof item === "string")
      : undefined,
  };
}

function parseResourceList(value: unknown, field: "医院" | "医生") {
  if (!isRecord(value) || !Array.isArray(value.items)) {
    throw new ApiError("INVALID_RESPONSE", `${field}资源响应格式无法识别。`);
  }
  return {
    items: value.items,
    count: typeof value.count === "number" && Number.isFinite(value.count) ? value.count : value.items.length,
    source: optionalString(value.source) ?? "unknown",
  };
}

export function parseHospitalList(value: unknown): HospitalListPayload {
  const parsed = parseResourceList(value, "医院");
  return {
    ...parsed,
    items: parsed.items.map(parseHospital),
  };
}

export function parseDoctorList(value: unknown): DoctorListPayload {
  const parsed = parseResourceList(value, "医生");
  return {
    ...parsed,
    items: parsed.items.map(parseDoctorRecord),
  };
}

function parseResourceProvenance(value: unknown): ResourceProvenance {
  if (!isRecord(value)) {
    throw new ApiError("INVALID_RESPONSE", "资源详情缺少来源登记。" );
  }
  return {
    source_class: requiredString(value.source_class, "provenance.source_class"),
    status: requiredString(value.status, "provenance.status"),
    last_updated: typeof value.last_updated === "string" ? value.last_updated : null,
    license_status: requiredString(value.license_status, "provenance.license_status"),
    field_level_status: requiredString(value.field_level_status, "provenance.field_level_status"),
    notice: requiredString(value.notice, "provenance.notice"),
    catalog_status: optionalString(value.catalog_status),
    unsupported_fields: Array.isArray(value.unsupported_fields)
      ? value.unsupported_fields.filter((item): item is string => typeof item === "string")
      : undefined,
  };
}

function parseResourceDetailBase(value: unknown): Record<string, unknown> {
  if (!isRecord(value) || !isRecord(value.provenance)) {
    throw new ApiError("INVALID_RESPONSE", "资源详情响应格式无法识别。" );
  }
  return {
    source: requiredString(value.source, "resource detail.source"),
    provenance: parseResourceProvenance(value.provenance),
  };
}

export function parseHospitalDetail(value: unknown): HospitalDetailPayload {
  if (!isRecord(value) || value.resource_type !== "hospital" || !isRecord(value.related)) {
    throw new ApiError("INVALID_RESPONSE", "医院详情响应格式无法识别。" );
  }
  return {
    ...parseResourceDetailBase(value),
    resource_type: "hospital",
    resource: parseHospital(value.resource),
    related: {
      doctor_count: optionalNumber(value.related.doctor_count) ?? 0,
      doctors: Array.isArray(value.related.doctors)
        ? value.related.doctors.map(parseDoctorRecord)
        : undefined,
    },
    derived_capability: isRecord(value.derived_capability)
      ? {
          areas: Array.isArray(value.derived_capability.areas)
            ? value.derived_capability.areas.filter((item): item is string => typeof item === "string")
            : [],
          scores: isRecord(value.derived_capability.scores)
            ? Object.fromEntries(
                Object.entries(value.derived_capability.scores)
                  .filter(([, score]) => typeof score === "number")
                  .map(([key, score]) => [key, score as number]),
              )
            : {},
          status: optionalString(value.derived_capability.status) ?? "unknown",
          formula_version: optionalString(value.derived_capability.formula_version) ?? "unknown",
          notice: optionalString(value.derived_capability.notice) ?? "派生字段仅供参考。",
        }
      : undefined,
  } as HospitalDetailPayload;
}

export function parseDoctorDetail(value: unknown): DoctorDetailPayload {
  if (!isRecord(value) || value.resource_type !== "doctor" || !isRecord(value.related)) {
    throw new ApiError("INVALID_RESPONSE", "医生详情响应格式无法识别。" );
  }
  return {
    ...parseResourceDetailBase(value),
    resource_type: "doctor",
    resource: parseDoctorRecord(value.resource),
    related: {
      hospital: value.related.hospital === null ? null : parseHospital(value.related.hospital),
    },
  } as DoctorDetailPayload;
}

export function parseResourceDetail(value: unknown): ResourceDetailPayload {
  if (isRecord(value) && value.resource_type === "hospital") return parseHospitalDetail(value);
  if (isRecord(value) && value.resource_type === "doctor") return parseDoctorDetail(value);
  throw new ApiError("INVALID_RESPONSE", "资源详情类型无法识别。" );
}

function parseRecommendedHospital(value: unknown): RecommendedHospital {
  if (!isRecord(value)) {
    throw new ApiError("INVALID_RESPONSE", "推荐医院条目格式无法识别。");
  }
  return {
    ...value,
    hospital: parseHospital(value.hospital),
    matched_department: optionalString(value.matched_department),
    distance: nullableNumber(value.distance),
    explanations: Array.isArray(value.explanations)
      ? value.explanations.filter((item): item is string => typeof item === "string")
      : [],
    traffic_access: isRecord(value.traffic_access) ? value.traffic_access : undefined,
    composite_score: optionalNumber(value.composite_score),
    ranking_model: optionalString(value.ranking_model),
  };
}

function parseDoctor(value: unknown): RecommendedDoctor {
  if (!isRecord(value) || !isRecord(value.doctor)) {
    throw new ApiError("INVALID_RESPONSE", "推荐医生条目格式无法识别。");
  }
  const doctor = parseDoctorRecord(value.doctor);
  return {
    ...value,
    doctor,
    matched_dept: optionalString(value.matched_dept),
    reasons: Array.isArray(value.reasons)
      ? value.reasons.filter((item): item is string => typeof item === "string")
      : [],
    hospital_distance_km: nullableNumber(value.hospital_distance_km),
    visit_path: optionalString(value.visit_path),
    match_score: optionalNumber(value.match_score),
  };
}

export function parseRecommendations(value: unknown): RecommendationPayload {
  if (!isRecord(value)) {
    throw new ApiError("INVALID_RESPONSE", "推荐响应格式无法识别。");
  }
  if (!Array.isArray(value.recommended_hospitals) || !Array.isArray(value.recommended_doctors)) {
    throw new ApiError("INVALID_RESPONSE", "推荐响应缺少医院或医生列表。");
  }
  const strategy: ResourceStrategy | undefined = isRecord(value.resource_strategy)
    ? value.resource_strategy
    : undefined;
  return {
    ...value,
    condition: requiredString(value.condition, "condition"),
    matched_department: typeof value.matched_department === "string" ? value.matched_department : null,
    triage: isRecord(value.triage) ? value.triage : undefined,
    recommended_hospitals: value.recommended_hospitals.map(parseRecommendedHospital),
    recommended_doctors: value.recommended_doctors.map(parseDoctor),
    resource_strategy: strategy,
    data_source: optionalString(value.data_source),
    effective_scenario: optionalString(value.effective_scenario),
    user_location: isRecord(value.user_location)
      ? {
          district: typeof value.user_location.district === "string" ? value.user_location.district : null,
          lat: nullableNumber(value.user_location.lat),
          lng: nullableNumber(value.user_location.lng),
          source: optionalString(value.user_location.source) ?? "unknown",
        }
      : undefined,
    feature_availability: isRecord(value.feature_availability)
      ? {
          location: value.feature_availability.location === true,
          distance: value.feature_availability.distance === true,
          transit: value.feature_availability.transit === true,
        }
      : undefined,
    ranking_notice: optionalString(value.ranking_notice),
    followup_answers: parseFollowupAnswers(value.followup_answers),
  };
}

function parseMetric(value: unknown, field: string) {
  if (!isRecord(value) || typeof value.value !== "number") {
    throw new ApiError("INVALID_RESPONSE", `城市摘要缺少有效的 ${field} 指标。`);
  }
  return {
    value: value.value,
    label: requiredString(value.label, `${field}.label`),
    source_class: requiredString(value.source_class, `${field}.source_class`),
    status: requiredString(value.status, `${field}.status`),
  };
}

export function parseCitySummary(value: unknown): CitySummary {
  if (!isRecord(value) || !isRecord(value.region) || !isRecord(value.metrics)) {
    throw new ApiError("INVALID_RESPONSE", "城市摘要响应格式无法识别。");
  }
  const region = value.region;
  return {
    region: {
      code: requiredString(region.code, "region.code"),
      name: requiredString(region.name, "region.name"),
      status: requiredString(region.status, "region.status"),
      region_pack_version: requiredString(
        region.region_pack_version,
        "region.region_pack_version",
      ),
    },
    metrics: {
      hospitals: parseMetric(value.metrics.hospitals, "hospitals"),
      doctors: parseMetric(value.metrics.doctors, "doctors"),
      bus_routes: parseMetric(value.metrics.bus_routes, "bus_routes"),
      districts: parseMetric(value.metrics.districts, "districts"),
    },
    generated_from: isRecord(value.generated_from)
      ? {
          region_pack_version: requiredString(
            value.generated_from.region_pack_version,
            "generated_from.region_pack_version",
          ),
          dataset_status: requiredString(
            value.generated_from.dataset_status,
            "generated_from.dataset_status",
          ),
        }
      : {
          region_pack_version: "unknown",
          dataset_status: "unknown",
        },
  };
}

function parseEvidenceDataset(value: unknown, field = "dataset") : EvidenceDataset {
  if (!isRecord(value)) {
    throw new ApiError("INVALID_RESPONSE", `可信证据缺少有效的 ${field}。`);
  }
  return {
    path: requiredString(value.path, `${field}.path`),
    sha256: requiredString(value.sha256, `${field}.sha256`),
    format: requiredString(value.format, `${field}.format`),
    record_count: nullableNumber(value.record_count),
    collections: isRecord(value.collections) ? value.collections : {},
  };
}

function parseOptionalEvidenceDataset(value: unknown, field: string): EvidenceDataset | null {
  return value === null || value === undefined ? null : parseEvidenceDataset(value, field);
}

function parseModelSplit(value: unknown): ModelSplitMetrics | undefined {
  if (!isRecord(value)) return undefined;
  return {
    test_rows: optionalNumber(value.test_rows) ?? 0,
    accuracy: nullableNumber(value.accuracy),
    covered_accuracy: nullableNumber(value.covered_accuracy),
    top3_accuracy: nullableNumber(value.top3_accuracy),
    macro_precision: nullableNumber(value.macro_precision),
    macro_recall: nullableNumber(value.macro_recall),
    macro_f1: nullableNumber(value.macro_f1),
    coverage: nullableNumber(value.coverage),
    abstention_rate: nullableNumber(value.abstention_rate),
    per_class_recall: isRecord(value.per_class_recall)
      ? Object.fromEntries(
          Object.entries(value.per_class_recall)
            .filter(([, score]) => typeof score === "number")
            .map(([label, score]) => [label, score as number]),
        )
      : undefined,
    confusion_matrix: isRecord(value.confusion_matrix)
      ? value.confusion_matrix as Record<string, Record<string, number>>
      : undefined,
  };
}

export function parseEvidence(value: unknown): EvidencePayload {
  if (
    !isRecord(value) ||
    !isRecord(value.region) ||
    !isRecord(value.versions) ||
    !isRecord(value.safety) ||
    !isRecord(value.model) ||
    !isRecord(value.data_quality) ||
    !Array.isArray(value.dataset_manifest)
  ) {
    throw new ApiError("INVALID_RESPONSE", "可信证据响应格式无法识别。");
  }

  const safety = value.safety;
  const model = value.model;
  const quality = value.data_quality as Record<string, unknown>;
  return {
    disclaimer: requiredString(value.disclaimer, "disclaimer"),
    status: requiredString(value.status, "status"),
    region: {
      code: requiredString(value.region.code, "region.code"),
      pack_version: requiredString(value.region.pack_version, "region.pack_version"),
      source: parseOptionalEvidenceDataset(value.region.source, "region.source"),
    },
    versions: {
      app: requiredString(value.versions.app, "versions.app"),
      ranking: requiredString(value.versions.ranking, "versions.ranking"),
      triage_rules: requiredString(value.versions.triage_rules, "versions.triage_rules"),
      model: requiredString(value.versions.model, "versions.model"),
      dataset: requiredString(value.versions.dataset, "versions.dataset"),
    },
    safety: {
      available: safety.available === true,
      schema_version: optionalString(safety.schema_version) ?? "unknown",
      case_count: optionalNumber(safety.case_count) ?? 0,
      red_flag_count: optionalNumber(safety.red_flag_count) ?? 0,
      red_flag_recall: nullableNumber(safety.red_flag_recall),
      under_triage_rate: nullableNumber(safety.under_triage_rate),
      over_triage_rate: nullableNumber(safety.over_triage_rate),
      emergency_false_negative: nullableNumber(safety.emergency_false_negative),
      insufficient_information_count: optionalNumber(safety.insufficient_information_count) ?? 0,
      insufficient_information_matches: optionalNumber(safety.insufficient_information_matches) ?? 0,
      review_required: Array.isArray(safety.review_required)
        ? safety.review_required.filter((item): item is string => typeof item === "string")
        : [],
      report_source: requiredString(safety.report_source, "safety.report_source"),
      label: requiredString(safety.label, "safety.label"),
    },
    model: {
      available: model.available === true,
      label: requiredString(model.label, "model.label"),
      model_type: optionalString(model.model_type) ?? "unknown",
      training_rows: nullableNumber(model.training_rows),
      test_rows: nullableNumber(model.test_rows),
      class_count: optionalNumber(model.class_count) ?? 0,
      vocabulary_size: optionalNumber(model.vocabulary_size) ?? 0,
      top1_accuracy: nullableNumber(model.top1_accuracy),
      top3_accuracy: nullableNumber(model.top3_accuracy),
      evaluation_scope: requiredString(model.evaluation_scope, "model.evaluation_scope"),
      model_source: parseOptionalEvidenceDataset(model.model_source, "model.model_source"),
      training_data_source: parseOptionalEvidenceDataset(
        model.training_data_source,
        "model.training_data_source",
      ),
      random_baseline: parseModelSplit(model.random_baseline),
      grouped_fingerprint: parseModelSplit(model.grouped_fingerprint),
      near_duplicate_audit: isRecord(model.near_duplicate_audit)
        ? {
            jaccard_threshold: optionalNumber(model.near_duplicate_audit.jaccard_threshold) ?? 0,
            pair_count: optionalNumber(model.near_duplicate_audit.pair_count) ?? 0,
            cross_label_pair_count: optionalNumber(model.near_duplicate_audit.cross_label_pair_count) ?? 0,
            note: optionalString(model.near_duplicate_audit.note) ?? "",
          }
        : undefined,
      split_manifest: optionalString(model.split_manifest),
    },
    data_quality: {
      available: quality.available === true,
      report_source: requiredString(quality.report_source, "data_quality.report_source"),
      schema_version: optionalString(quality.schema_version) ?? "unknown",
      dataset_count: optionalNumber(quality.dataset_count) ?? 0,
      issue_count: optionalNumber(quality.issue_count) ?? 0,
      status: requiredString(quality.status, "data_quality.status"),
    } satisfies DataQualityEvidence,
    dataset_manifest: value.dataset_manifest.map((item, index) =>
      parseEvidenceDataset(item, `dataset_manifest[${index}]`),
    ),
    limitations: Array.isArray(value.limitations)
      ? value.limitations.filter((item): item is string => typeof item === "string")
      : [],
    hospital_data: isRecord(value.hospital_data)
      ? {
          available: value.hospital_data.available === true,
          dataset_id: optionalString(value.hospital_data.dataset_id) ?? "unknown",
          status: optionalString(value.hospital_data.status) ?? "unknown",
          source_class: optionalString(value.hospital_data.source_class) ?? "unknown",
          source_url: typeof value.hospital_data.source_url === "string" ? value.hospital_data.source_url : null,
          last_verified_at: typeof value.hospital_data.last_verified_at === "string" ? value.hospital_data.last_verified_at : null,
          license_status: optionalString(value.hospital_data.license_status) ?? "unknown",
          deidentified: value.hospital_data.deidentified === true,
          record_count: optionalNumber(value.hospital_data.record_count) ?? 0,
          public_fact_fields: Array.isArray(value.hospital_data.public_fact_fields)
            ? value.hospital_data.public_fact_fields.filter((item): item is string => typeof item === "string")
            : [],
          derived_fields: isRecord(value.hospital_data.derived_fields)
            ? Object.fromEntries(
                Object.entries(value.hospital_data.derived_fields)
                  .filter(([, item]) => isRecord(item))
                  .map(([key, item]) => [key, {
                    status: optionalString((item as Record<string, unknown>).status) ?? "unknown",
                    formula_version: optionalString((item as Record<string, unknown>).formula_version) ?? "unknown",
                  }]),
              )
            : {},
          unsupported_fields: Array.isArray(value.hospital_data.unsupported_fields)
            ? value.hospital_data.unsupported_fields.filter((item): item is string => typeof item === "string")
            : [],
          notice: optionalString(value.hospital_data.notice) ?? "医院资料状态待核验。",
        }
      : undefined,
  };
}

function parseMapHospital(value: unknown): MapHospitalRecord {
  if (!isRecord(value) || !isRecord(value.map_point)) {
    throw new ApiError("INVALID_RESPONSE", "地图医院条目格式无法识别。");
  }
  const markerType = value.marker_type;
  if (markerType !== "EMERGENCY_CAPABLE" && markerType !== "NORMAL") {
    throw new ApiError("INVALID_RESPONSE", "地图医院条目缺少有效的 marker 类型。");
  }
  const lat = optionalNumber(value.lat);
  const lng = optionalNumber(value.lng);
  const x = optionalNumber(value.map_point.x);
  const y = optionalNumber(value.map_point.y);
  if (lat === undefined || lng === undefined || x === undefined || y === undefined) {
    throw new ApiError("INVALID_RESPONSE", "地图医院条目缺少有效坐标。");
  }
  return {
    id: typeof value.id === "number" ? value.id : undefined,
    name: optionalString(value.name),
    alias: optionalString(value.alias),
    level: optionalString(value.level),
    type: optionalString(value.type),
    address: optionalString(value.address),
    lat,
    lng,
    emergency: value.emergency === true,
    marker_type: markerType as MapMarkerType,
    map_reason: requiredString(value.map_reason, "map_reason"),
    distance_km: nullableNumber(value.distance_km),
    map_point: { x, y },
  };
}

export function parseMap(value: unknown): MapPayload {
  if (!isRecord(value) || !isRecord(value.region) || !Array.isArray(value.items)) {
    throw new ApiError("INVALID_RESPONSE", "地图资源响应格式无法识别。");
  }
  return {
    region: {
      code: requiredString(value.region.code, "map.region.code"),
      name: requiredString(value.region.name, "map.region.name"),
      region_pack_version: requiredString(
        value.region.region_pack_version,
        "map.region.region_pack_version",
      ),
    },
    items: value.items.map(parseMapHospital),
    count: optionalNumber(value.count) ?? value.items.length,
    source: optionalString(value.source) ?? "unknown",
    distance_method: value.distance_method === null ? null : optionalString(value.distance_method) ?? null,
    notice: requiredString(value.notice, "map.notice"),
    provenance: isRecord(value.provenance)
      ? {
          status: optionalString(value.provenance.status) ?? "unknown",
          source_class: optionalString(value.provenance.source_class) ?? "unknown",
          last_updated: typeof value.provenance.last_updated === "string" ? value.provenance.last_updated : null,
          license_status: optionalString(value.provenance.license_status) ?? "unknown",
        }
      : undefined,
    user_location: isRecord(value.user_location)
      ? {
          lat: nullableNumber(value.user_location.lat),
          lng: nullableNumber(value.user_location.lng),
          source: optionalString(value.user_location.source) ?? "unknown",
        }
      : undefined,
  };
}
