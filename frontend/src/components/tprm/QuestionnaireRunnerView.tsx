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
  Download,
  GitBranch,
  Copy,
} from 'lucide-react';
import type { AssessmentDetail, UserProfile, RiskFindingItem } from '../../types';

interface QuestionnaireRunnerViewProps {
  currentUser: UserProfile;
  initialAssessmentId?: string | null;
  onNavigateToVendor?: (vendorId: string) => void;
  onRefreshMetrics?: () => void;
}

export const QuestionnaireRunnerView: React.FC<QuestionnaireRunnerViewProps> = ({
  currentUser,
  initialAssessmentId,
  onNavigateToVendor,
  onRefreshMetrics,
}) => {
  const [viewMode, setViewMode] = useState<'runner' | 'rules' | 'versions'>('runner');
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
  const [templatesCatalog, setTemplatesCatalog] = useState<any[]>([]);

  const fetchAssessments = async () => {
    try {
      const [asmRes, tplRes] = await Promise.all([
        fetch('/api/tprm/v1/assessments', { headers: { 'X-User-Email': currentUser.email } }),
        fetch('/api/tprm/v1/questionnaires/templates', { headers: { 'X-User-Email': currentUser.email } }),
      ]);
      if (asmRes.ok) {
        const data = await asmRes.json();
        const list = data.items || data.assessments || [];
        setAssessmentsList(list);
        if (!selectedAssessmentId && list.length > 0) {
          setSelectedAssessmentId(list[0].id);
        }
      }
      if (tplRes.ok) {
        const tplData = await tplRes.json();
        setTemplatesCatalog(tplData.items || tplData.templates || []);
      }
    } catch (err) {
      console.error('Failed to load assessments', err);
    }
  };

  const fetchDetail = async (id: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/tprm/v1/assessments/${id}`, {
        headers: { 'X-User-Email': currentUser.email },
      });
      if (res.ok) {
        const data: AssessmentDetail = await res.json();
        setDetail(data);
        setResponses(data.responses || {});
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
    if (initialAssessmentId) {
      setSelectedAssessmentId(initialAssessmentId);
    }
  }, [initialAssessmentId]);

  useEffect(() => {
    if (selectedAssessmentId) {
      fetchDetail(selectedAssessmentId);
    }
  }, [selectedAssessmentId]);

  // Evaluate Appendix C Conditional Rules (CL.1 to CL.14)
  const isQuestionVisible = (qCode: string): boolean => {
    if (!detail?.template) return true;
    const rules = detail.template.conditional_rules || [];
    const governingRules = rules.filter((r) => r.shown_question_codes.includes(qCode));
    if (governingRules.length === 0) return true;

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

  const handleFillAllFavorable = () => {
    if (!detail?.template) return;
    const next: Record<string, string> = { ...responses };
    detail.template.sections.forEach((s) => {
      s.questions.forEach((q) => {
        if (!q.is_conditional) {
          if (q.favorable_answer) next[q.question_code] = q.favorable_answer;
          else if (q.question_type === 'YesNo') next[q.question_code] = 'Yes';
          else if (q.options && q.options.length > 0) next[q.question_code] = q.options[q.options.length - 1];
          else next[q.question_code] = `Verified response for ${q.question_code}`;
        }
      });
    });
    setResponses(next);
    setMessage({ type: 'success', text: 'Pre-filled all required questions with compliant baseline responses. Review and click Submit & Score.' });
  };

  const handleSaveDraft = async () => {
    if (!selectedAssessmentId) return;
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch(`/api/tprm/v1/assessments/${selectedAssessmentId}/responses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': currentUser.email },
        body: JSON.stringify({ responses }),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: 'Questionnaire draft responses persisted to database.' });
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
      const res = await fetch(`/api/tprm/v1/assessments/${selectedAssessmentId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': currentUser.email },
        body: JSON.stringify({ responses }),
      });
      if (res.ok) {
        const resData = await res.json();
        setMessage({
          type: 'success',
          text: `${resData.message} (Average Score: ${resData.overall_score}%, Triggered Findings: ${resData.findings_count})`,
        });
        await fetchDetail(selectedAssessmentId);
        await fetchAssessments();
        onRefreshMetrics?.();
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Submission validation failed' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error submitting assessment' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReviewAction = async (status: 'Approved' | 'ConcernsRaised') => {
    if (!selectedAssessmentId) return;
    const reviewerGroup = currentUser.groups[0] || 'Vendor Risk Management Group';
    try {
      const res = await fetch(`/api/tprm/v1/assessments/${selectedAssessmentId}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': currentUser.email },
        body: JSON.stringify({
          group_name: reviewerGroup,
          status,
          notes: reviewNote || `${status} by ${currentUser.full_name} (${reviewerGroup})`,
        }),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: `Departmental review recorded for ${reviewerGroup}: ${status}` });
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

  const handleVersionAction = async (templateCode: string, method: 'A' | 'B') => {
    try {
      const res = await fetch(`/api/tprm/v1/questionnaires/templates/${templateCode}/version`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': currentUser.email },
        body: JSON.stringify({ method }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessage({
          type: 'success',
          text:
            method === 'B'
              ? `Method B Version Published: ${data.name} updated to v${data.version} across published workflows while preserving historical assessment responses.`
              : `Method A Draft Created: Duplicated template as '${data.name}' (${data.code}) in Draft state for VRM validation.`,
        });
        await fetchAssessments();
        if (selectedAssessmentId) await fetchDetail(selectedAssessmentId);
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Versioning requires VRM Admin privileges' });
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to create questionnaire version' });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Selection Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FileText size={20} className="text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">
              Due Diligence Questionnaires (Appendix B, C & E)
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Dynamic questionnaire engine enforcing all 14 Conditional Rules (CL.1–CL.14), 90 Risk/Task/Scoring Rules (QR.1–QR.90), and Method A/B Versioning.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setViewMode('runner')}
            className={`btn btn-sm ${viewMode === 'runner' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Questionnaire Runner
          </button>
          <button
            type="button"
            onClick={() => setViewMode('rules')}
            className={`btn btn-sm ${viewMode === 'rules' ? 'btn-primary' : 'btn-secondary'}`}
          >
            CL.1–14 & QR.1–90 Rule Registry
          </button>
          <button
            type="button"
            onClick={() => setViewMode('versions')}
            className={`btn btn-sm ${viewMode === 'versions' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Templates & Versioning (Sec 6.3.3)
          </button>
        </div>
      </div>

      {/* Assessment Selector Row */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold text-slate-700">Active Assessment:</label>
          <select
            className="form-select min-w-[280px]"
            value={selectedAssessmentId || ''}
            onChange={(e) => setSelectedAssessmentId(e.target.value)}
          >
            {assessmentsList.map((a) => (
              <option key={a.id} value={a.id}>
                {a.vendor_name} ({a.template_code}) — {a.status} {a.overall_score !== null ? `[${a.overall_score}%]` : ''}
              </option>
            ))}
          </select>
        </div>

        {detail?.template && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={handleFillAllFavorable}
              disabled={detail.assessment.status === 'Approved'}
            >
              Auto-Fill Baseline Answers
            </button>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => window.open(`/api/tprm/v1/questionnaires/templates/${detail.template.code}/export-csv`, '_blank')}
            >
              <Download size={13} /> Export Template CSV
            </button>
          </div>
        )}
      </div>

      {message && (
        <div
          className={`p-4 rounded-md border text-xs font-medium flex items-center gap-3 ${
            message.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle size={16} className="text-rose-600 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {loading && !detail && (
        <div className="p-12 text-center text-slate-500 bg-white border border-slate-200 rounded-lg">
          <p className="text-sm">Loading questionnaire template and response matrix...</p>
        </div>
      )}

      {/* VIEW MODE 2: CL.1-14 & QR.1-90 Rule Inspector */}
      {detail && viewMode === 'rules' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
            <h3 className="text-sm font-bold text-slate-900">
              Appendix C Conditional Show-Logic Rules for {detail.template.name} ({detail.template.conditional_rules.length} Rules)
            </h3>
            <div className="overflow-x-auto">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>Logic No.</th>
                    <th>Section</th>
                    <th>Trigger Question & Condition</th>
                    <th>Shown Question(s)</th>
                    <th>Copy Logic To</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.template.conditional_rules.map((r) => (
                    <tr key={r.rule_code}>
                      <td className="font-mono font-bold text-indigo-600">{r.rule_code}</td>
                      <td>{r.section_name}</td>
                      <td className="font-mono text-xs">
                        Question {r.trigger_question_code} {r.trigger_operator || 'Equal To'} <strong>{r.trigger_response}</strong>
                      </td>
                      <td className="font-mono font-bold">{r.shown_question_codes.join(', ')}</td>
                      <td className="font-mono text-xs">{(r.copy_logic_to_questions || []).join(', ') || '—'}</td>
                      <td className="text-xs text-slate-600">{r.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
            <h3 className="text-sm font-bold text-slate-900">
              Appendix E Risk, Scoring, Auto-Approve & Departmental Task Rules for {detail.template.name} ({detail.template.risk_rules?.length || 0} Rules)
            </h3>
            <div className="overflow-x-auto">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>Rule No.</th>
                    <th>Rule Name</th>
                    <th>Trigger Question / Condition</th>
                    <th>Action Type</th>
                    <th>Risk / Task Created</th>
                    <th>Inherent Risk</th>
                    <th>Control ID & Name</th>
                    <th>Responsible / Collaborator Group</th>
                  </tr>
                </thead>
                <tbody>
                  {(detail.template.risk_rules || []).map((rr) => (
                    <tr key={rr.rule_code}>
                      <td className="font-mono font-bold text-indigo-600">{rr.rule_code}</td>
                      <td className="font-mono text-xs font-semibold">{rr.rule_name}</td>
                      <td className="text-xs">
                        <span className="font-mono">{rr.trigger_question_code}</span> ({rr.trigger_operator}: <strong>{rr.trigger_response}</strong>)
                      </td>
                      <td><span className="badge badge-neutral">{rr.action_type}</span></td>
                      <td className="text-xs font-semibold">{rr.risk_name || rr.task_name || rr.result_comments || 'Average Score'}</td>
                      <td>
                        {rr.inherent_risk ? (
                          <span className={`badge ${rr.inherent_risk === 'High' ? 'badge-alert' : 'badge-warning'}`}>
                            {rr.inherent_risk}
                          </span>
                        ) : '—'}
                      </td>
                      <td className="font-mono text-xs">
                        {rr.control_id ? `${rr.control_id} (${rr.control_name})` : '—'}
                      </td>
                      <td className="text-xs">{rr.collaborator_group || rr.responsible_group || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* VIEW MODE 3: Template Versioning & Administration (Section 6.3.3) */}
      {viewMode === 'versions' && (
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900">
            Questionnaire Template Versioning & Maintenance (Section 6.3.1 & 6.3.3)
          </h3>
          <p className="text-xs text-slate-500">
            Source Reference File: <strong>Final Due Diligence Questionnaire v1.0</strong>. Supports both documented versioning methods without rewriting historical assessment responses.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templatesCatalog.map((tpl) => (
              <div key={tpl.id} className="p-4 rounded-lg border border-slate-200 bg-slate-50 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="badge badge-info">{tpl.questionnaire_no || 'Template'} • v{tpl.version}</span>
                  <span className={`badge ${tpl.is_published ? 'badge-success' : 'badge-warning'}`}>
                    {tpl.status || (tpl.is_published ? 'Published' : 'Draft')}
                  </span>
                </div>
                <div className="text-sm font-bold text-slate-900">{tpl.name}</div>
                <p className="text-xs text-slate-600">{tpl.description}</p>
                <div className="text-xs text-slate-500">
                  Sections: <strong>{tpl.sections_count}</strong> • Questions: <strong>{tpl.questions_count}</strong> • Show Rules: <strong>{tpl.conditional_rules_count}</strong> • Risk Rules: <strong>{tpl.risk_rules_count}</strong>
                </div>
                <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-200">
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    onClick={() => handleVersionAction(tpl.code, 'B')}
                  >
                    <GitBranch size={13} /> Method B: Create New Version (v{(tpl.version || 1) + 1})
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => handleVersionAction(tpl.code, 'A')}
                  >
                    <Copy size={13} /> Method A: Duplicate Draft Copy
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => window.open(`/api/tprm/v1/questionnaires/templates/${tpl.code}/export-csv`, '_blank')}
                  >
                    <Download size={13} /> Export CSV
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VIEW MODE 1: Interactive Questionnaire Runner */}
      {detail && viewMode === 'runner' && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div>
                  <span className="badge badge-info">
                    Template: {detail.template.name} (v{detail.template.version}) • Source: {detail.template.source_file_name || 'Final Due Diligence Questionnaire v1.0'}
                  </span>
                  <div className="flex items-center gap-3 mt-2">
                    <h2 className="text-lg font-bold text-slate-900">
                      Vendor: {detail.assessment.vendor_name}
                    </h2>
                    {onNavigateToVendor && (
                      <button
                        type="button"
                        onClick={() => onNavigateToVendor(detail.assessment.vendor_id)}
                        className="btn-link text-xs"
                      >
                        (View Vendor Record)
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                    <span>Tier: <strong>{detail.assessment.vendor_tier}</strong></span>
                    <span>•</span>
                    <span>Category: <strong>{detail.assessment.vendor_category}</strong></span>
                    <span>•</span>
                    <span>Status: <strong className="text-indigo-600">{detail.assessment.status}</strong></span>
                    {detail.assessment.overall_score !== null && (
                      <>
                        <span>•</span>
                        <span>Average Score: <strong>{detail.assessment.overall_score}%</strong></span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleSaveDraft}
                    disabled={saving || detail.assessment.status === 'Approved'}
                    className="btn btn-secondary"
                  >
                    <Save size={14} />
                    <span>{saving ? 'Saving...' : 'Save Draft'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={submitting || detail.assessment.status === 'Approved'}
                    className="btn btn-primary"
                  >
                    <Send size={14} />
                    <span>{submitting ? 'Evaluating QR.1–90...' : 'Submit & Score'}</span>
                  </button>
                </div>
              </div>

              {/* Sections Accordion */}
              <div className="mt-6 space-y-6">
                {detail.template.sections.map((section) => {
                  const isExpanded = expandedSections[section.id] !== false;
                  const sectionQuestions = section.questions.filter((q) => isQuestionVisible(q.question_code));

                  return (
                    <div
                      key={section.id}
                      className="border border-slate-200 rounded-lg overflow-hidden bg-slate-50/50"
                    >
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedSections((prev) => ({
                            ...prev,
                            [section.id]: !isExpanded,
                          }))
                        }
                        className="w-full text-left px-4 py-3 bg-slate-100 flex items-center justify-between border-b border-slate-200"
                      >
                        <div className="flex items-center gap-2.5">
                          {isExpanded ? (
                            <ChevronDown size={15} className="text-slate-500" />
                          ) : (
                            <ChevronRight size={15} className="text-slate-500" />
                          )}
                          <span className="text-xs font-bold text-slate-900">
                            Section {section.section_number}: {section.title}
                          </span>
                          <span className="badge badge-neutral">
                            Reviewer: {section.responsible_group}
                          </span>
                        </div>
                        <span className="text-xs text-slate-500">
                          {sectionQuestions.length} visible question(s)
                        </span>
                      </button>

                      {isExpanded && (
                        <div className="p-4 space-y-4 bg-white">
                          {sectionQuestions.map((q) => {
                            const val = responses[q.question_code] || '';
                            const isAnswered = Boolean(val);
                            const isChoiceType =
                              q.question_type === 'YesNo' ||
                              q.question_type === 'Yes/No' ||
                              q.question_type === 'SingleChoice' ||
                              q.question_type === 'Single Choice';

                            return (
                              <div
                                key={q.id}
                                className={`p-3.5 rounded-md border ${
                                  isAnswered
                                    ? 'border-slate-200 bg-white'
                                    : 'border-amber-200 bg-amber-50/20'
                                }`}
                              >
                                <div className="flex items-center gap-2">
                                  <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100">
                                    {q.question_code}
                                  </span>
                                  {q.is_required && (
                                    <span className="badge badge-alert">Required</span>
                                  )}
                                  {q.is_conditional && (
                                    <span className="badge badge-purple">Conditional Show Logic (Appendix C)</span>
                                  )}
                                </div>
                                <p className="text-sm font-medium text-slate-900 mt-1.5">
                                  {q.prompt}
                                </p>

                                <div className="mt-3">
                                  {isChoiceType ? (
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
                                              className={`btn btn-sm ${
                                                selected ? 'btn-primary' : 'btn-secondary'
                                              }`}
                                            >
                                              {opt}
                                            </button>
                                          );
                                        }
                                      )}
                                    </div>
                                  ) : q.question_type === 'Date' ? (
                                    <input
                                      type="date"
                                      value={val}
                                      disabled={detail.assessment.status === 'Approved'}
                                      onChange={(e) => handleResponseChange(q.question_code, e.target.value)}
                                      className="form-input max-w-sm"
                                    />
                                  ) : (
                                    <input
                                      type="text"
                                      value={val}
                                      disabled={detail.assessment.status === 'Approved'}
                                      onChange={(e) => handleResponseChange(q.question_code, e.target.value)}
                                      placeholder={`Enter response for ${q.question_code}...`}
                                      className="form-input"
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

          {/* Right Column: Triggered Findings & Departmental Review */}
          <div className="space-y-6">
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <ShieldAlert size={18} className="text-rose-600" />
                  <h3 className="text-sm font-bold text-slate-900">Triggered Findings</h3>
                </div>
                <span className="badge badge-alert">{detail.findings.length}</span>
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
                        <span className="font-mono font-bold text-rose-700">{f.rule_code}</span>
                        <span className={`badge ${f.inherent_risk === 'High' ? 'badge-alert' : 'badge-warning'}`}>
                          {f.inherent_risk} Risk
                        </span>
                      </div>
                      <div className="font-semibold text-slate-900">{f.risk_name}</div>
                      <div className="text-[11px] text-slate-600">
                        <strong>Control:</strong> {f.control_id} — {f.control_name}
                      </div>
                      <div className="text-[10px] text-slate-500">
                        <strong>Owner:</strong> {f.responsible_group}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
                <UserCheck size={18} className="text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">Departmental Section Review</h3>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Reviewer Group:</label>
                <div className="text-xs font-medium text-slate-900 bg-slate-50 p-2 rounded border border-slate-200">
                  {currentUser.groups[0] || 'Vendor Risk Management Group'} ({currentUser.full_name})
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Review Notes & Communication to VRM:</label>
                <textarea
                  rows={3}
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  placeholder="Record verification notes, mitigating controls, or concerns for VRM..."
                  className="input-textarea"
                />
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleReviewAction('Approved')}
                  className="btn btn-sm btn-success flex-1"
                >
                  Approve Section
                </button>
                <button
                  type="button"
                  onClick={() => handleReviewAction('ConcernsRaised')}
                  className="btn btn-sm btn-alert flex-1"
                >
                  Flag Concerns
                </button>
              </div>

              {detail.reviews && detail.reviews.length > 0 && (
                <div className="pt-3 border-t border-slate-100">
                  <h4 className="text-xs font-bold text-slate-700 mb-2">Recorded Departmental Reviews</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {detail.reviews.map((r) => (
                      <div key={r.id} className="text-xs bg-slate-50 p-2 rounded border border-slate-200">
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-slate-800">{r.user_group_name}</span>
                          <span className={`badge ${r.status === 'Approved' ? 'badge-success' : 'badge-alert'}`}>
                            {r.status}
                          </span>
                        </div>
                        <p className="text-slate-600 text-[11px] mt-1">{r.notes}</p>
                        <span className="text-[10px] text-slate-400 block mt-1">
                          By {r.reviewer_email} • {new Date(r.reviewed_at).toLocaleDateString()}
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
