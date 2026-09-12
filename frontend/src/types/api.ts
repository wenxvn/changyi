export type TriageStatus =
  | "EMERGENCY"
  | "URGENT"
  | "ROUTINE"
  | "INSUFFICIENT_INFORMATION";

export interface ApiMeta {
  request_id: string;
  model_version: string;
  region_code: string;
  app_version?: string;
  ranking_version?: string;
  triage_rules_version?: string;
  dataset_version?: string;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiEnvelope<T> {
  data: T | null;
  meta: ApiMeta;
  error: ApiErrorPayload | null;
}

export interface FollowupQuestion {
  id: string;
  question: string;
  options: FollowupOption[];
  reason?: string;
}

export interface FollowupOption {
  label: string;
  value: string;
}

export interface FollowupAnswer {
  question_id: string;
  value?: string;
  text_answer?: string;
}

export interface FollowupPayload {
  needed: boolean;
  confidence: string;
  missing_slots: string[];
  questions: FollowupQuestion[];
  topk_comparison?: {
    need_compare?: boolean;
    focus?: string[];
    distinguish_questions?: FollowupQuestion[];
  };
}

export interface TriagePayload {
  condition: string;
  original_condition?: string;
  followup_answers?: FollowupAnswer[];
  matched_department?: string | null;
  triage_status: TriageStatus;
  triage?: {
    label?: string;
    level?: string;
    followup?: FollowupPayload;
    red_flag_tags?: string[];
    reasons?: string[];
    disclaimer?: string;
    [key: string]: unknown;
  };
  htriage_analysis?: Record<string, unknown>;
  disease_prediction?: unknown;
}

export interface FollowupResponse {
  condition: string;
  original_condition?: string;
  followup_answers?: FollowupAnswer[];
  matched_department?: string | null;
  triage_status: TriageStatus;
  triage_label?: string | null;
  followup: FollowupPayload;
  known_disease?: Record<string, unknown>;
  htriage_analysis?: Record<string, unknown>;
}

export interface HospitalRecord {
  id?: number;
  name?: string;
  alias?: string;
  level?: string;
  type?: string;
  address?: string;
  district?: string | null;
  phone?: string;
  description?: string;
  lat?: number;
  lng?: number;
  emergency?: boolean;
  departments?: string[];
  strengths?: string[];
  derived_capability_areas?: string[];
  derived_capability_scores?: Record<string, number>;
  [key: string]: unknown;
}

export interface RecommendedHospital {
  hospital: HospitalRecord;
  matched_department?: string | null;
  distance?: number | null;
  explanations?: string[];
  traffic_access?: { summary?: string; used_in_ranking?: boolean; [key: string]: unknown };
  composite_score?: number;
  ranking_model?: string;
  [key: string]: unknown;
}

export interface DoctorRecord {
  id?: number;
  name?: string;
  title?: string;
  position?: string;
  department?: string;
  hospital_name?: string;
  specialties?: string[];
  specialty?: string;
  outpatient_time?: string;
  photo_url?: string;
  photo_provenance_status?: string;
  source_image_url?: string;
  doctor_page_url?: string;
  [key: string]: unknown;
}

export interface RecommendedDoctor {
  doctor: DoctorRecord;
  matched_dept?: string | null;
  reasons?: string[];
  hospital_distance_km?: number | null;
  visit_path?: string;
  match_score?: number;
  [key: string]: unknown;
}

export interface ResourceStrategy {
  code?: string;
  title?: string;
  visit_path?: string;
  notice?: string;
  expert_enabled?: boolean;
  [key: string]: unknown;
}

export interface RecommendationPayload {
  condition: string;
  matched_department?: string | null;
  triage?: TriagePayload["triage"];
  recommended_hospitals: RecommendedHospital[];
  recommended_doctors: RecommendedDoctor[];
  resource_strategy?: ResourceStrategy;
  data_source?: string;
  effective_scenario?: string;
  user_location?: {
    district: string | null;
    lat: number | null;
    lng: number | null;
    source: "unknown" | "geolocation" | "district" | string;
  };
  feature_availability?: {
    location?: boolean;
    distance?: boolean;
    transit?: boolean;
  };
  ranking_notice?: string;
  [key: string]: unknown;
}

export interface HospitalListPayload {
  items: HospitalRecord[];
  count: number;
  source: string;
}

export interface DoctorListPayload {
  items: DoctorRecord[];
  count: number;
  source: string;
}

export interface ResourceProvenance {
  source_class: string;
  status: string;
  last_updated: string | null;
  license_status: string;
  field_level_status: string;
  notice: string;
  catalog_status?: string;
  unsupported_fields?: string[];
}

export interface HospitalDetailPayload {
  resource_type: "hospital";
  resource: HospitalRecord;
  source: string;
  provenance: ResourceProvenance;
  derived_capability?: {
    areas: string[];
    scores: Record<string, number>;
    status: string;
    formula_version: string;
    notice: string;
  };
  related: { doctor_count: number; doctors?: DoctorRecord[] };
}

export interface DoctorDetailPayload {
  resource_type: "doctor";
  resource: DoctorRecord;
  source: string;
  provenance: ResourceProvenance;
  related: { hospital: HospitalRecord | null };
}

export type ResourceDetailPayload = HospitalDetailPayload | DoctorDetailPayload;

export interface MetricSummary {
  value: number;
  label: string;
  source_class: string;
  status: string;
}

export interface CitySummary {
  region: {
    code: string;
    name: string;
    status: string;
    region_pack_version: string;
  };
  metrics: {
    hospitals: MetricSummary;
    doctors: MetricSummary;
    bus_routes: MetricSummary;
    districts: MetricSummary;
  };
  generated_from: {
    region_pack_version: string;
    dataset_status: string;
  };
}

export interface RegionSummary {
  region_code: string;
  name: string;
  status: string;
  region_pack_version: string;
  districts: Array<{ code: string; name: string; lat?: number; lng?: number }>;
}

export interface EvidenceDataset {
  path: string;
  sha256: string;
  format: string;
  record_count: number | null;
  collections: Record<string, unknown>;
}

export interface SafetyEvidence {
  available: boolean;
  schema_version: string;
  case_count: number;
  red_flag_count: number;
  red_flag_recall: number | null;
  under_triage_rate: number | null;
  over_triage_rate: number | null;
  emergency_false_negative: number | null;
  insufficient_information_count: number;
  insufficient_information_matches: number;
  review_required: string[];
  report_source: string;
  label: string;
}

export interface ModelEvidence {
  available: boolean;
  label: string;
  model_type: string;
  training_rows: number | null;
  test_rows: number | null;
  class_count: number;
  vocabulary_size: number;
  top1_accuracy: number | null;
  top3_accuracy: number | null;
  evaluation_scope: string;
  model_source: EvidenceDataset | null;
  training_data_source: EvidenceDataset | null;
  random_baseline?: ModelSplitMetrics;
  grouped_fingerprint?: ModelSplitMetrics;
  near_duplicate_same_label?: ModelSplitMetrics;
  near_duplicate_global?: ModelSplitMetrics;
  near_duplicate_components?: {
    same_label?: Record<string, unknown>;
    global?: Record<string, unknown>;
  };
  primary_split?: string;
  near_duplicate_audit?: {
    jaccard_threshold: number;
    pair_count: number;
    cross_label_pair_count: number;
    note: string;
  };
  strict_near_duplicate_isolation?: {
    label: string;
    test_samples: number | null;
    present_classes: number | null;
    total_classes: number | null;
    cross_split_near_duplicates: number | null;
    seed: number | null;
    jaccard_threshold: number | null;
    comparable_to_random_split: boolean;
    explanation: string;
  };
  split_manifest?: string;
}

export interface ModelSplitMetrics {
  test_rows: number;
  accuracy: number | null;
  covered_accuracy?: number | null;
  top3_accuracy: number | null;
  macro_precision: number | null;
  macro_recall: number | null;
  macro_f1: number | null;
  coverage: number | null;
  present_class_count?: number | null;
  abstention_rate: number | null;
  per_class_recall?: Record<string, number>;
  confusion_matrix?: Record<string, Record<string, number>>;
  cross_split_near_duplicates?: {
    pair_count: number;
    cross_label_pair_count: number;
  };
}

export interface DataQualityEvidence {
  available: boolean;
  report_source: string;
  schema_version: string;
  dataset_count: number;
  issue_count: number;
  status: string;
}

export interface EvidencePayload {
  disclaimer: string;
  status: string;
  region: {
    code: string;
    pack_version: string;
    source: EvidenceDataset | null;
  };
  versions: {
    app: string;
    ranking: string;
    triage_rules: string;
    model: string;
    dataset: string;
  };
  safety: SafetyEvidence;
  model: ModelEvidence;
  data_quality: DataQualityEvidence;
  dataset_manifest: EvidenceDataset[];
  limitations: string[];
  hospital_data?: {
    available: boolean;
    dataset_id: string;
    status: string;
    source_class: string;
    source_url: string | null;
    last_verified_at: string | null;
    license_status: string;
    deidentified: boolean;
    record_count: number;
    public_fact_fields: string[];
    derived_fields: Record<string, { status: string; formula_version: string }>;
    unsupported_fields: string[];
    notice: string;
  };
}

export type MapMarkerType = "EMERGENCY_CAPABLE" | "NORMAL";

export interface MapHospitalRecord {
  id?: number;
  name?: string;
  alias?: string;
  level?: string;
  type?: string;
  address?: string;
  lat: number;
  lng: number;
  emergency: boolean;
  marker_type: MapMarkerType;
  map_reason: string;
  distance_km: number | null;
  map_point: { x: number; y: number };
}

export interface MapPayload {
  region: {
    code: string;
    name: string;
    region_pack_version: string;
  };
  items: MapHospitalRecord[];
  count: number;
  source: string;
  distance_method: string | null;
  notice: string;
  provenance?: { status: string; source_class: string; last_updated: string | null; license_status: string };
  user_location?: { lat: number | null; lng: number | null; source: string };
}
