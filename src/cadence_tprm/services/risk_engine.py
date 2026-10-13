"""Authoritative Risk Scoring & Findings Engine.

Source Authority: Cadence_TPRM_Training.docx Section 2.3, 6.3, Appendix E, Table 14 (QR.1 to QR.90).
"""

from typing import Dict, List, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from src.cadence_tprm.models.assessment import Assessment, RiskFinding
from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.questionnaire import RiskRule
from src.cadence_tprm.models.task import Task, Notification
from src.cadence_tprm.services.audit_service import AuditService

class RiskEngine:

    @staticmethod
    def evaluate_assessment_submission(
        db: Session,
        assessment: Assessment,
        responses: Dict[str, str],
        actor_email: str
    ) -> Tuple[List[RiskFinding], float, bool]:
        """Evaluates questionnaire submission against Appendix E rules QR.1 to QR.90.

        Returns:
            (findings_list, overall_score, is_tier3_auto_approved)
        """
        template_code = assessment.template_code
        vendor = db.query(Vendor).filter_by(id=assessment.vendor_id).first()

        # Load all risk rules for this questionnaire template
        rules = db.query(RiskRule).filter_by(template_code=template_code).all()

        triggered_findings = []
        department_risks_count = {}

        # 1. Evaluate Rule Triggers
        for rule in rules:
            if rule.action_type != "Create risk":
                continue

            ans = responses.get(rule.trigger_question_code)
            if not ans:
                continue

            # Compare trigger value
            is_match = False
            if rule.trigger_operator == "Equal To":
                is_match = str(ans).strip().lower() == str(rule.trigger_response).strip().lower()
            elif rule.trigger_operator == "Contains":
                is_match = str(rule.trigger_response).strip().lower() in str(ans).strip().lower()

            if is_match:
                # SLA deadline calculation per Appendix D (Table 13)
                # High Risk: 5+4 = 9 days (SLA.3)
                # Medium Risk: 10+4 = 14 days (SLA.4)
                # Low Risk: 15+4 = 19 days (SLA.5)
                sla_days = 9 if rule.inherent_risk == "High" else (14 if rule.inherent_risk == "Medium" else 19)
                due_date = datetime.now(timezone.utc) + timedelta(days=sla_days)

                # Generate mitigation recommendation based on control
                mitigation = RiskEngine._generate_mitigation_guidance(rule.control_id, rule.risk_name)

                finding = RiskFinding(
                    assessment_id=assessment.id,
                    vendor_id=vendor.id,
                    rule_code=rule.rule_code,
                    risk_name=rule.risk_name,
                    inherent_risk=rule.inherent_risk,
                    control_id=rule.control_id,
                    control_name=rule.control_name,
                    responsible_group=rule.responsible_group or "Vendor Risk Management Group",
                    status="Open",
                    mitigation_recommendation=mitigation,
                    due_date=due_date
                )
                db.add(finding)
                triggered_findings.append(finding)

                grp = rule.responsible_group or "Vendor Risk Management Group"
                department_risks_count[grp] = department_risks_count.get(grp, 0) + 1

        db.flush()

        # 2. Calculate Assessment Score (QR.58 / QR.72)
        total_eval_questions = len(responses)
        penalty_points = 0
        for f in triggered_findings:
            if f.inherent_risk == "High":
                penalty_points += 15
            elif f.inherent_risk == "Medium":
                penalty_points += 7
            else:
                penalty_points += 3

        overall_score = max(0.0, min(100.0, round(100.0 - penalty_points, 1)))
        assessment.overall_score = overall_score

        # 3. Rule QR.56 / QR.70: Create "Assessment Submitted" task
        task_name = "Assessment Submitted_T3" if template_code == "T3_v1" else "Assessment Submitted"
        db.add(Task(
            vendor_id=vendor.id,
            assessment_id=assessment.id,
            task_type="Assessment Review",
            title=f"{task_name}: {vendor.name}",
            description=f"Assessment submitted with overall score of {overall_score}%. {len(triggered_findings)} inherent risks flagged.",
            assignee_email=None,
            collaborator_group="Vendor Risk Management Group",
            due_date=datetime.now(timezone.utc) + timedelta(days=4),  # SLA.2 (4 days)
            reminder_date=datetime.now(timezone.utc) + timedelta(days=2),
            status="Pending"
        ))

        # 4. Rule QR.57 / QR.71: Low Assessment Score Task if score < 40
        if overall_score < 40.0:
            low_score_task = "Template score rule_T3" if template_code == "T3_v1" else "Low Assessment Score"
            db.add(Task(
                vendor_id=vendor.id,
                assessment_id=assessment.id,
                task_type="Low Score Escalation",
                title=f"URGENT - {low_score_task}: {vendor.name} ({overall_score}%)",
                description="Assessment scored below the 40% acceptable threshold. Executive VRM review required.",
                assignee_email="daniela.figueroa@cadence.com",
                collaborator_group="Vendor Risk Management Group",
                due_date=datetime.now(timezone.utc) + timedelta(days=2),
                status="Pending"
            ))

        # 5. Department-Specific Tasks (QR.74 to QR.90)
        for dept_group, count in department_risks_count.items():
            if dept_group != "Vendor Risk Management Group":
                task_label = f"{dept_group.replace(' Group', '')} Risk Identified for Third-Party"
                if template_code == "T3_v1":
                    task_label += "_T3"
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=assessment.id,
                    task_type="Departmental Risk Review",
                    title=f"{task_label}: {vendor.name} ({count} risks)",
                    description=f"{count} risk findings flagged under {dept_group} oversight. Review responses and propose mitigations.",
                    assignee_email=None,
                    collaborator_group=dept_group,
                    due_date=datetime.now(timezone.utc) + timedelta(days=4),
                    status="Pending"
                ))

        # 6. Rule QR.73: Tier 3 Auto-Approval Check
        is_tier3_auto_approved = False
        if template_code == "T3_v1" and vendor.vendor_tier == "Tier 3":
            # Auto-approve if zero High inherent risks and score >= 80%
            high_risks = [f for f in triggered_findings if f.inherent_risk == "High"]
            if len(high_risks) == 0 and overall_score >= 80.0:
                is_tier3_auto_approved = True

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="ASSESSMENT_EVALUATED",
            entity_type="ASSESSMENT",
            entity_id=assessment.id,
            details={
                "overall_score": overall_score,
                "findings_count": len(triggered_findings),
                "is_tier3_auto_approved": is_tier3_auto_approved,
            }
        )

        db.commit()
        return triggered_findings, overall_score, is_tier3_auto_approved

    @staticmethod
    def _generate_mitigation_guidance(control_id: str, risk_name: str) -> str:
        """Maps standard control recommendations."""
        guidance = {
            "QRC_CL_1.1": "Execute cross-border data transfer addendum (Standard Contractual Clauses / GDPR Transfer Impact Assessment).",
            "QRC_CL_1.2": "Require additional financial solvency verification or parental guarantee due to operational history <5 years.",
            "QRC_Fin_3.1": "Require bank reference letter and audited tax filings in lieu of formal audited statements.",
            "QRC_Fin_3.2": "Execute enhanced financial indemnification and periodic quarterly solvency reviews.",
            "QRC_Pri_4.1": "Confirm technical encryption controls (AES-256) and obtain signed cross-border data processing agreement.",
            "QRC_Pri_4.8": "Vendor must adopt Cadence Third-Party Privacy Standard prior to contract live date.",
            "QRC_Sec_4.12": "Enforce mandatory Multi-Factor Authentication (MFA) via SSO integration or IP allowlisting.",
            "QRC_Sec_4.14": "Require quarterly SIEM / SOC monitoring reports and continuous vulnerability telemetry.",
            "QRC_Sec_4.17": "Require vendor to commission third-party pen test and remediate high-severity findings within 60 days.",
            "QRC_Sec_4.24": "Require implementation of TLS 1.3 in transit and AES-256 at rest with customer-managed keys.",
            "QRC_Sec_4.34": "Vendor must furnish SOC 2 Type II or ISO 27001 certificate within 9 months or accept penalty clause.",
            "QRC_Sec_4.35": "Vendor must bind Cyber Liability Insurance policy with minimum $5,000,000 aggregate coverage.",
            "QRC_RR_8.1": "Incorporate Cadence standard SLA schedule with uptime credits and response time penalties.",
            "QRC_RR_8.2": "Require annual delivery of Business Continuity Plan test results and Disaster Recovery failover reports.",
        }
        return guidance.get(control_id, f"Review control implementation and agree on remediation milestone for {risk_name}.")
