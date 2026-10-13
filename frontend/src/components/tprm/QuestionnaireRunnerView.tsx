import React, { useState, useEffect } from 'react';
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Send,
  Save,
  ChevronDown,
  ChevronRight,
  UserCheck,
} from 'lucide-react';
import type { AssessmentDetail, UserProfile, RiskFindingItem } from '../../types';

interface QuestionnaireRunnerViewProps {
  currentUser: UserProfile;
  initialAssessmentId?: string | null;
  onNavigateToVendor?: (vendorId: string) => void;
}

export const QuestionnaireRunnerView: React.FC<QuestionnaireRunnerViewProps> = ({
  currentUser,
  initialAssessmentId,
  onNavigateToVendor,
}) => {
  const [assessmentsList, setAssessmentsList] = useState<any[]>([]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string | null>(initialAssessmentId || null);
  const [detail, setDetail] = useState<AssessmentDetail | null>(null);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [reviewNote, setReviewNote] = useState<string>('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  // Fetch list of assessments
  const fetchAssessments = async () => {
    try {
      const res = await fetch('/api/tprm/v1/assessments');
      if (res.ok) {
        const data = await res.json();
        setAssessmentsList(data.items || []);
        if (!selectedAssessmentId && data.items && data.items.length > 0) {
          setSelectedAssessmentId(data.items[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load assessments', err);
    }
  };

  // Fetch detail for selected assessment
  const fetchDetail = async (id: string) => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`/api/tprm/v1/assessments/${id}`);
      if (res.ok) {
        const data: AssessmentDetail = await res.json();
        setDetail(data);
        setResponses(data.responses || {});
        // expand all sections by default
        const exp: Record<string, boolean> = {};
        data.template?.sections?.forEach((s) => {
          exp[s.id] = true;
        });
        setExpandedSections(exp);
      } else {
        setMessage({ type: 'error', text: 'Failed to load assessment details' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Error connecting to server' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessments();
  }, []);

  useEffect(() => {
    if (selectedAssessmentId) {
      fetchDetail(selectedAssessmentId);
    }
  }, [selectedAssessmentId]);

  // Compute visibility of questions using conditional rules (CL.1 - CL.14)
  const isQuestionVisible = (qCode: string): boolean => {
    if (!detail?.template) return true;
    const rules = detail.template.conditional_rules || [];
    
    // Check if this question is governed by any conditional rule
    const governingRules = rules.filter((r) => r.shown_question_codes.includes(qCode));
    if (governingRules.length === 0) {
      return true; // Not conditional, always visible
    }

    // Must satisfy all or any governing rule? If any rule trigger condition is met, show it.
    return governingRules.some((r) => {
      const triggerAnswer = responses[r.trigger_question_code] || '';
      return triggerAnswer.trim().toLowerCase() === r.trigger_response.trim().toLowerCase();
    });
  };

  const handleResponseChange = (qCode: string, value: string) => {
    setResponses((prev) => ({
      ...prev,
      [qCode]: value,
    }));
  };

  const handleSaveDraft = async () => {
    if (!selectedAssessmentId) return;
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch(`/api/tprm/v1/assessments/${selectedAssessmentId}/responses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses }),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: 'Draft saved successfully' });
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Failed to save draft' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error saving draft' });
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedAssessmentId) return;
    setSubmitting(true);
    setMessage(null);
    try {
      // Save responses first
      await fetch(`/api/tprm/v1/assessments/${selectedAssessmentId}/responses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses }),
      });

      // Submit assessment & trigger risk calculation
      const res = await fetch(`/api/tprm/v1/assessments/${selectedAssessmentId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        setMessage({
          type: 'success',
          text: 'Questionnaire submitted successfully! Automated risk engine evaluated all Appendix E rules.',
        });
        await fetchDetail(selectedAssessmentId);
        await fetchAssessments();
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Submission failed' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error submitting assessment' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReviewAction = async (status: 'Approved' | 'Rejected') => {
    if (!selectedAssessmentId) return;
    // Find reviewer's relevant group
    const reviewerGroup = currentUser.groups[0] || 'Vendor Risk Management';
    try {
      const res = await fetch(`/api/tprm/v1/assessments/${selectedAssessmentId}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_group_name: reviewerGroup,
          status,
          notes: reviewNote || `${status} by ${currentUser.full_name} (${reviewerGroup})`,
        }),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: `Review recorded: ${status}` });
        setReviewNote('');
        await fetchDetail(selectedAssessmentId);
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Failed to record review' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error recording review' });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Selection Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FileText className="w-6 h-6 text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">Due Diligence Questionnaire Runner</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Dynamic questionnaire engine enforcing Table 12 conditional logic (CL.1–CL.14) and automated Table 14 risk scoring (QR.1–QR.90).
          </p>
        </div>

        {/* Assessment Dropdown Picker */}
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold text-slate-700 whitespace-nowrap">Assessment:</label>
          <select
            className="text-xs border border-slate-300 rounded-md px-3 py-2 bg-slate-50 text-slate-900 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none min-w-[280px]"
            value={selectedAssessmentId || ''}
            onChange={(e) => setSelectedAssessmentId(e.target.value)}
          >
            {assessmentsList.map((a) => (
              <option key={a.id} value={a.id}>
                {a.vendor_name} ({a.template_code}) — {a.status}
              </option>
            ))}
          </select>
        </div>
      </div>

      {message && (
        <div
          className={`p-4 rounded-md border text-sm flex items-center gap-3 ${
            message.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {loading && !detail && (
        <div className="p-12 text-center text-slate-500 bg-white border border-slate-200 rounded-lg">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-3"></div>
          <p className="text-sm">Loading questionnaire template and response matrix...</p>
        </div>
      )}

      {detail && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Questionnaire Form (3 cols) */}
          <div className="lg:col-span-3 space-y-6">
            {/* Header Card */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                    Template: {detail.template.name} (v{detail.template.version})
                  </span>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-bold text-slate-900 mt-2">
                      Vendor: {detail.assessment.vendor_name}
                    </h2>
                    {onNavigateToVendor && (
                      <button
                        onClick={() => onNavigateToVendor(detail.assessment.vendor_id)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold mt-2 hover:underline"
                      >
                        (View Profile)
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                    <span>Tier: <strong>{detail.assessment.vendor_tier}</strong></span>
                    <span>•</span>
                    <span>Category: <strong>{detail.assessment.vendor_category}</strong></span>
                    <span>•</span>
                    <span>Status: <strong className="text-indigo-600">{detail.assessment.status}</strong></span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSaveDraft}
                    disabled={saving || detail.assessment.status === 'Approved'}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-md transition-colors disabled:opacity-50"
                  >
                    <Save className="w-3.5 h-3.5" />
                    {saving ? 'Saving...' : 'Save Draft'}
                  </button>

                  <button
                    onClick={handleSubmit}
                    disabled={submitting || detail.assessment.status === 'Approved'}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors shadow-sm disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    {submitting ? 'Submitting...' : 'Submit & Score'}
                  </button>
                </div>
              </div>

              {/* Sections Accordion */}
              <div className="mt-6 space-y-6">
                {detail.template.sections.map((section) => {
                  const isExpanded = expandedSections[section.id] !== false;
                  // Questions in this section
                  const sectionQuestions = section.questions.filter((q) => isQuestionVisible(q.question_code));

                  return (
                    <div
                      key={section.id}
                      className="border border-slate-200 rounded-lg overflow-hidden bg-slate-50/50"
                    >
                      <button
                        onClick={() =>
                          setExpandedSections((prev) => ({
                            ...prev,
                            [section.id]: !isExpanded,
                          }))
                        }
                        className="w-full text-left px-4 py-3 bg-slate-100 hover:bg-slate-200/80 flex items-center justify-between border-b border-slate-200 transition-colors"
                      >
                        <div className="flex items-center gap-2.5">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-slate-500" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-slate-500" />
                          )}
                          <span className="text-xs font-bold text-slate-800">
                            Section {section.section_number}: {section.title}
                          </span>
                          <span className="text-[10px] font-semibold text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                            Reviewer: {section.responsible_group}
                          </span>
                        </div>
                        <span className="text-xs text-slate-500">
                          {sectionQuestions.length} visible questions
                        </span>
                      </button>

                      {isExpanded && (
                        <div className="p-4 space-y-5 bg-white">
                          {sectionQuestions.map((q) => {
                            const val = responses[q.question_code] || '';
                            const isAnswered = Boolean(val);

                            return (
                              <div
                                key={q.id}
                                className={`p-3.5 rounded-md border transition-all ${
                                  isAnswered
                                    ? 'border-slate-200 bg-white'
                                    : 'border-amber-200 bg-amber-50/20'
                                }`}
                              >
                                <div className="flex items-start justify-between gap-4">
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100">
                                        {q.question_code}
                                      </span>
                                      {q.is_required && (
                                        <span className="text-[10px] font-bold text-rose-600 bg-rose-50 px-1.5 py-0.2 rounded border border-rose-200">
                                          Required
                                        </span>
                                      )}
                                      {q.is_conditional && (
                                        <span className="text-[10px] font-medium text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded border border-purple-200">
                                          Conditional
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-sm font-medium text-slate-900 mt-1.5 leading-snug">
                                      {q.prompt}
                                    </p>
                                  </div>
                                </div>

                                {/* Answer Input Controls */}
                                <div className="mt-3">
                                  {q.question_type === 'Single Choice' || q.question_type === 'Yes/No' ? (
                                    <div className="flex flex-wrap gap-2">
                                      {(q.options && q.options.length > 0 ? q.options : ['Yes', 'No']).map(
                                        (opt) => {
                                          const selected = val === opt;
                                          return (
                                            <button
                                              key={opt}
                                              type="button"
                                              disabled={detail.assessment.status === 'Approved'}
                                              onClick={() => handleResponseChange(q.question_code, opt)}
                                              className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-all ${
                                                selected
                                                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                                                  : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                                              }`}
                                            >
                                              {opt}
                                            </button>
                                          );
                                        }
                                      )}
                                    </div>
                                  ) : q.question_type === 'Text' || q.question_type === 'URL' ? (
                                    <input
                                      type="text"
                                      value={val}
                                      disabled={detail.assessment.status === 'Approved'}
                                      onChange={(e) =>
                                        handleResponseChange(q.question_code, e.target.value)
                                      }
                                      placeholder={`Enter ${q.prompt.toLowerCase()}...`}
                                      className="w-full text-xs border border-slate-300 rounded-md px-3 py-2 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                                    />
                                  ) : (
                                    <textarea
                                      rows={2}
                                      value={val}
                                      disabled={detail.assessment.status === 'Approved'}
                                      onChange={(e) =>
                                        handleResponseChange(q.question_code, e.target.value)
                                      }
                                      placeholder="Provide detailed description..."
                                      className="w-full text-xs border border-slate-300 rounded-md px-3 py-2 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                                    />
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Assessment Metadata, Risk Findings & Departmental Review (1 col) */}
          <div className="space-y-6">
            {/* Automated Risk Findings Card */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-rose-600" />
                  <h3 className="text-sm font-bold text-slate-900">Triggered Findings</h3>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                  {detail.findings.length}
                </span>
              </div>

              <div className="mt-4 space-y-3 max-h-[360px] overflow-y-auto">
                {detail.findings.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500 bg-slate-50 rounded-md border border-slate-200">
                    No risk findings triggered. Submit questionnaire to evaluate Appendix E rules.
                  </div>
                ) : (
                  detail.findings.map((f: RiskFindingItem) => (
                    <div
                      key={f.id}
                      className="p-3 bg-rose-50/40 border border-rose-200 rounded-md text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-[10px] text-rose-700 bg-rose-100/70 px-1.5 py-0.5 rounded">
                          {f.rule_code}
                        </span>
                        <span
                          className={`font-semibold px-2 py-0.5 rounded-full text-[10px] ${
                            f.inherent_risk === 'High'
                              ? 'bg-rose-600 text-white'
                              : f.inherent_risk === 'Medium'
                              ? 'bg-amber-500 text-white'
                              : 'bg-emerald-600 text-white'
                          }`}
                        >
                          {f.inherent_risk} Risk
                        </span>
                      </div>
                      <div className="font-semibold text-slate-900 leading-snug">{f.risk_name}</div>
                      <div className="text-[11px] text-slate-600">
                        <strong>Control:</strong> {f.control_id} — {f.control_name}
                      </div>
                      <div className="text-[10px] text-slate-500">
                        <strong>Owner:</strong> {f.responsible_group} • <strong>Due:</strong> {f.due_date || 'SLA'}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Departmental Review Card */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
                <UserCheck className="w-5 h-5 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">Departmental Review</h3>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700">Reviewer Group:</label>
                <div className="text-xs font-medium text-slate-900 bg-slate-50 p-2 rounded border border-slate-200">
                  {currentUser.groups[0] || 'Vendor Risk Management'} ({currentUser.full_name})
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700">Review Notes / Mitigation Plan:</label>
                <textarea
                  rows={3}
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  placeholder="Record verification notes, mitigating controls, or rationale..."
                  className="w-full text-xs border border-slate-300 rounded-md p-2 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => handleReviewAction('Approved')}
                  className="flex-1 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-md transition-colors shadow-xs"
                >
                  Approve Section
                </button>
                <button
                  type="button"
                  onClick={() => handleReviewAction('Rejected')}
                  className="flex-1 py-1.5 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-md transition-colors"
                >
                  Request Changes
                </button>
              </div>

              {/* Existing Reviews History */}
              {detail.reviews && detail.reviews.length > 0 && (
                <div className="pt-3 border-t border-slate-100">
                  <h4 className="text-xs font-bold text-slate-700 mb-2">Review History</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {detail.reviews.map((r) => (
                      <div key={r.id} className="text-xs bg-slate-50 p-2 rounded border border-slate-200">
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-slate-800">{r.user_group_name}</span>
                          <span
                            className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                              r.status === 'Approved'
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {r.status}
                          </span>
                        </div>
                        <p className="text-slate-600 text-[11px] mt-1">{r.notes}</p>
                        <span className="text-[10px] text-slate-400 block mt-1">
                          By {r.reviewer_email} at {new Date(r.reviewed_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
