// ==========================================
// CADENCE TPRM & ENTERPRISE TYPES
// Authority: Cadence_TPRM_Training.docx
// ==========================================

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  title?: string;
  is_active: boolean;
  is_admin: boolean;
  is_synthetic?: boolean;
  groups: string[];
  group_roles: Record<string, string>;
  roles?: string[];
  permissions?: string[];
  is_respondent?: boolean;
}

export type VendorCategory =
  | 'Service Provider and Vendor'
  | 'Revenue Partner'
  | 'Marketing Partner'
  | 'Staffing Vendor'
  | 'International Vendor';

export type VendorTier = 'Tier 1' | 'Tier 2' | 'Tier 3';

export type VendorType = 'Consulting' | 'Operations' | 'Regulatory' | 'Strategic' | 'Technology' | 'Unknown';

export type Criticality = 'Critical' | 'High' | 'Medium' | 'Low';

export type LifecycleStatus = 'New' | 'In Progress' | 'Live' | 'Review Reject' | 'Offboarding' | 'Closed';

export interface VendorItem {
  id: string;
  name: string;
  type: VendorType;
  criticality: Criticality;
  primary_vendor_contact: string;
  business_owner: string;
  vendor_tier: VendorTier;
  vendor_category: VendorCategory;
  website: string;
  lifecycle_status: LifecycleStatus;
  current_workflow_name: string;
  current_stage: string;
  is_archived?: boolean;
  renewal_status?: string;
  last_assessment_completion_date: string | null;
  next_reassessment_due_date: string | null;
  created_at: string;
}

export interface ContractItem {
  id: string;
  contract_reference: string;
  title: string;
  source: string;
  status: string;
  effective_date: string | null;
  expiration_date: string | null;
}

export interface RiskFindingItem {
  id: string;
  assessment_id?: string;
  vendor_id?: string;
  vendor_name?: string;
  rule_code: string;
  risk_name: string;
  inherent_risk: 'High' | 'Medium' | 'Low';
  control_id: string;
  control_name: string;
  responsible_group: string;
  status: 'Open' | 'Acknowledged' | 'Remediating' | 'Accepted' | 'Closed';
  mitigation_recommendation: string;
  due_date: string;
}

export interface TaskItem {
  id: string;
  vendor_id: string;
  vendor_name: string;
  assessment_id?: string;
  task_type: string;
  title: string;
  description?: string;
  assignee_email?: string;
  collaborator_group?: string;
  due_date: string;
  reminder_date?: string;
  is_overdue: boolean;
  status: 'Pending' | 'In Progress' | 'Completed' | 'Overdue';
  created_at: string;
}

export interface NotificationItem {
  id: string;
  recipient_email?: string;
  subject: string;
  body: string;
  is_read: boolean;
  link_url?: string;
  created_at: string;
}

export interface QuestionItem {
  id: string;
  question_code: string;
  prompt: string;
  question_type: string;
  options?: string[];
  favorable_answer?: string;
  is_required: boolean;
  is_conditional: boolean;
  is_visible: boolean;
  order_index: number;
}

export interface SectionItem {
  id: string;
  section_number: number;
  title: string;
  responsible_group: string;
  questions: QuestionItem[];
}

export interface ConditionalRuleItem {
  rule_code: string;
  section_name?: string;
  condition_logic?: string;
  trigger_question_code: string;
  trigger_operator?: string;
  trigger_response: string;
  primary_shown_question?: string;
  copy_logic_to_questions?: string[];
  shown_question_codes: string[];
  description?: string;
}

export interface RiskRuleSpecItem {
  rule_code: string;
  rule_name: string;
  condition_logic: string;
  trigger_type: string;
  trigger_question_code: string;
  trigger_operator: string;
  trigger_response: string;
  action_type: string;
  risk_name?: string;
  inherent_risk?: string;
  control_id?: string;
  control_name?: string;
  task_name?: string;
  assignee?: string;
  collaborator_group?: string;
  responsible_group?: string;
  result_status?: string;
  result_comments?: string;
  source_notes?: string;
}

export interface TemplateDetail {
  id: string;
  questionnaire_no?: string;
  code: string;
  name: string;
  description: string;
  template_language?: string;
  template_icon?: string;
  source_file_name?: string;
  approver_group?: string;
  version: number;
  status?: string;
  is_published?: boolean;
  sections: SectionItem[];
  conditional_rules: ConditionalRuleItem[];
  risk_rules?: RiskRuleSpecItem[];
}

export interface AssessmentReviewItem {
  id: string;
  user_group_name: string;
  reviewer_email: string;
  status: string;
  notes: string;
  reviewed_at: string;
}

export interface AssessmentDetail {
  assessment: {
    id: string;
    vendor_id: string;
    vendor_name: string;
    vendor_tier: string;
    vendor_category: string;
    template_code: string;
    status: string;
    overall_score: number | null;
    due_date: string | null;
    submitted_at: string | null;
    completed_at: string | null;
    decision_reason: string | null;
    decision_by: string | null;
  };
  responses: Record<string, string>;
  template: TemplateDetail;
  findings: RiskFindingItem[];
  reviews: AssessmentReviewItem[];
}

export interface DashboardSummary {
  total_vendors: number;
  vendors_by_category: Record<string, number>;
  vendors_by_tier: Record<string, number>;
  vendors_by_status: Record<string, number>;
  vendors_by_stage?: Record<string, number>;
  assessments: {
    total: number;
    pending: number;
    approved: number;
    rejected: number;
  };
  risk_findings: {
    total: number;
    open: number;
    high: number;
    medium: number;
    low: number;
  };
  sla_and_tasks: {
    pending_tasks: number;
    overdue_tasks: number;
    reassessments_due: number;
    renewals_pending?: number;
  };
}

export interface AuditLogItem {
  id: string;
  actor_email: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface WorkflowStageDef {
  name: string;
  badge_color: string;
  description: string;
  is_used: boolean;
}

export interface WorkflowRuleItem {
  rule_code: string;
  source_sr_no: string;
  rule_name: string;
  stage_name: string;
  trigger_name?: string;
  trigger_type?: string;
  rule_type: string;
  description: string;
  condition_expression: string;
  action_expression: string;
  discrepancy_note?: string;
}

export interface SLAConfigItem {
  sla_no: string;
  sla_name: string;
  description: string;
  timeline_days: number;
  effective_deadline_days: number;
  reminder_days: number | null;
}

export interface WorkflowItem {
  id: string;
  name: string;
  description: string;
  status?: string;
  is_default?: boolean;
  is_active: boolean;
  stages?: WorkflowStageDef[];
  rules?: WorkflowRuleItem[];
  instances_count: number;
}

export interface WorkflowTransitionItem {
  id: string;
  actor_email: string;
  from_stage: string;
  to_stage: string;
  trigger_name: string;
  rule_name: string;
  decision_reason: string;
  timestamp: string;
}

// Legacy case study types
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
  detector_method?: string;
  rule_id?: string;
  rationale?: string;
  page?: number;
}

export interface VerificationFinding {
  check: string;
  entity_type?: string;
  count?: number;
  message?: string;
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
  precision?: number;
  recall?: number;
  f1_score?: number;
  false_negative_rate?: number;
  category_counts: Record<string, number>;
  redactions_applied: number;
  safe_warnings: string[];
  safe_error: string | null;
  safe_error_code: string | null;
  artifact_ref: string | null;
  extracted_text: string | null;
  redacted_text: string | null;
  entities: DetectedEntity[];
  verification_findings?: VerificationFinding[];
  structure_score?: number;
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

export interface AssistantChatResponse {
  query?: string;
  explanation: string;
  citations?: string[];
  safe_error?: string | null;
}

export interface AuditEvent {
  event_id?: string;
  document_id?: string;
  timestamp: string;
  stage: string;
  event_type: string;
  status: string;
  error_code?: string;
  duration_sec?: number;
  entity_count?: number;
  verification_status?: string | null;
  release_decision?: boolean;
  step?: number;
  action?: string;
  actor?: string;
  details?: Record<string, any>;
  integrity_hash?: string;
  safe_message?: string;
}

export interface PIIFinding {
  id: string;
  document_id: string;
  finding_index: number;
  type: string;
  start: number;
  end: number;
  confidence: number;
  value: string;
  masked_value: string;
  detector_method: string;
  rule_id: string;
  rationale: string;
  status: string;
  verification_result: string;
  page_or_slide: number;
  risk_level: string;
  created_at?: string;
}

export interface OverviewMetrics {
  documents_received: number;
  processing_runs_completed: number;
  findings_detected: number;
  findings_successfully_masked: number;
  verification_failures: number;
  documents_awaiting_review: number;
  documents_blocked_from_release: number;
  documents_approved_for_release: number;
  category_breakdown: Record<string, number>;
  recent_activity: any[];
}

export interface SystemSettings {
  zero_leakage_mandate: boolean;
  minimum_structure_score: number;
  confidence_threshold: number;
  ocr_confidence_threshold: number;
  enforce_luhn_check: boolean;
  ai_explanation_mode: string;
  retention_policy_days: number;
  supported_formats: string[];
}

