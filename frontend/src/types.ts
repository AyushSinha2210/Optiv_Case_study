export interface StageTransition {
  step: number;
  from_stage: string;
  to_stage: string;
  timestamp: string;
  duration_sec: number;
  message: string;
}

export interface DetectedEntity {
  type: string;
  start: number;
  end: number;
  confidence: number;
  value: string;
  masked_value: string;
}

export interface ProcessResponse {
  document_id: string;
  workflow_status: "success" | "blocked" | "failed" | "incomplete";
  current_stage: string;
  stage_history: StageTransition[];
  started_at: string;
  completed_at: string | null;
  duration_sec: number;
  source_type: string | null;
  pages_count: number;
  char_count: number;
  extraction_status: string | null;
  detection_status: string | null;
  redaction_status: string | null;
  verification_status: string | null;
  release_allowed: boolean;
  category_counts: Record<string, number>;
  redactions_applied: number;
  safe_warnings: string[];
  safe_error: string | null;
  safe_error_code: string | null;
  artifact_ref: string | null;
  extracted_text: string | null;
  redacted_text: string | null;
  entities: DetectedEntity[];
}

export interface ScenarioFixture {
  id: string;
  name: string;
  filename: string;
  file_type: string;
  description: string;
  expected_categories: string[];
  expected_count: number;
  size_bytes: number;
}

export interface AuditEvent {
  event_id: string;
  document_id: string;
  timestamp: string;
  stage: string;
  event_type: string;
  status: string;
  duration_sec?: number;
  entity_count?: number;
  category_counts?: Record<string, number>;
  verification_status?: string;
  release_decision?: boolean;
  error_code?: string;
}

export interface AssistantChatResponse {
  document_id: string;
  query: string | null;
  topic: string;
  explanation: string;
  citations: string[];
  timestamp: string;
}
