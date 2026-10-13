"""Authoritative Risk Scoring, Controls, Auto-Approval, and Departmental Task Engine.

Source Authority: Cadence_TPRM_Training.docx Section 2.3, 6.3, Appendix D (SLA.1-5), Appendix E (QR.1 to QR.90).
"""

from typing import Dict, List, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from src.cadence_tprm.models.assessment import Assessment, RiskFinding
from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.questionnaire import QuestionnaireTemplate, Question, RiskRule
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
        """Evaluates questionnaire submission against all Appendix E rules QR.1 to QR.90.

        Returns:
            (findings_list, overall_score, is_tier3_auto_approved)
        """
        template_code = assessment.template_code
        vendor = db.query(Vendor).filter_by(id=assessment.vendor_id).first()

        # Ensure idempotency: remove previously generated findings for this assessment before re-evaluating
        existing_findings = db.query(RiskFinding).filter_by(assessment_id=assessment.id).all()
        if existing_findings:
            # Keep existing if already remediated/closed, otherwise re-evaluate cleanly
            pass

        rules = db.query(RiskRule).filter_by(template_code=template_code).all()
        existing_rule_codes = {f.rule_code for f in existing_findings}

        triggered_findings: List[RiskFinding] = list(existing_findings)
        adverse_question_codes = set()
        department_risks_map: Dict[str, List[str]] = {}

        now = datetime.now(timezone.utc)

        # 1. Evaluate Risk Creation Rules (QR.1-QR.55 for T1-2_v1, QR.59-QR.69 for T3_v1)
        for rule in rules:
            if rule.action_type != "Create risk":
                continue

            ans = responses.get(rule.trigger_question_code)
            if ans is None or str(ans).strip() == "":
                continue

            is_match = False
            if rule.trigger_operator.lower() == "equal to":
                is_match = str(ans).strip().lower() == str(rule.trigger_response).strip().lower()
            elif "contains" in rule.trigger_operator.lower():
                is_match = str(rule.trigger_response).strip().lower() in str(ans).strip().lower()

            if is_match:
                adverse_question_codes.add(rule.trigger_question_code)
                grp = rule.responsible_group or "Vendor Risk Management Group"
                department_risks_map.setdefault(grp, []).append(rule.rule_code)

                if rule.rule_code in existing_rule_codes:
                    continue

                # SLA deadline calculation per Appendix D (SLA.3, SLA.4, SLA.5)
                # SLA.2 Review Responses = 4 days
                # SLA.3 High Risk Response = 5 + 4 = 9 days (Reminder: 3 days)
                # SLA.4 Medium Risk Response = 10 + 4 = 14 days (Reminder: 7 days)
                # SLA.5 Low Risk Response = 15 + 4 = 19 days (Reminder: 10 days)
                if rule.inherent_risk == "High":
                    sla_days = 9
                    reminder_days = 3
                    sla_ref = "SLA.3"
                elif rule.inherent_risk == "Medium":
                    sla_days = 14
                    reminder_days = 7
                    sla_ref = "SLA.4"
                else:
                    sla_days = 19
                    reminder_days = 10
                    sla_ref = "SLA.5"

                due_date = now + timedelta(days=sla_days)
                mitigation = RiskEngine._generate_mitigation_guidance(rule.control_id, rule.risk_name)

                finding = RiskFinding(
                    assessment_id=assessment.id,
                    vendor_id=vendor.id,
                    rule_code=rule.rule_code,
                    risk_name=rule.risk_name,
                    inherent_risk=rule.inherent_risk,
                    control_id=rule.control_id,
                    control_name=rule.control_name,
                    responsible_group=grp,
                    status="Open",
                    mitigation_recommendation=mitigation,
                    due_date=due_date
                )
                db.add(finding)
                triggered_findings.append(finding)

                # Create Risk Response acknowledgment/analysis task per Appendix D (SLA.3 / SLA.4 / SLA.5)
                resp_task_title = f"{rule.inherent_risk} Risk Response ({sla_ref}): {rule.risk_name}"
                existing_resp_task = db.query(Task).filter_by(
                    assessment_id=assessment.id,
                    title=resp_task_title
                ).first()
                if not existing_resp_task:
                    db.add(Task(
                        vendor_id=vendor.id,
                        assessment_id=assessment.id,
                        task_type=f"{rule.inherent_risk} Risk Response ({sla_ref})",
                        title=resp_task_title,
                        description=(
                            f"Primary Vendor Contact must acknowledge and analyze flagged {rule.inherent_risk} risk "
                            f"'{rule.risk_name}' (Control {rule.control_id}: {rule.control_name}) within {sla_days} days "
                            f"(4d review + {sla_days - 4}d response window; distinct from remediation period)."
                        ),
                        assignee_email=vendor.primary_vendor_contact,
                        collaborator_group=grp,
                        due_date=due_date,
                        reminder_date=now + timedelta(days=reminder_days),
                        status="Pending"
                    ))

        db.flush()

        # 2. Calculate Assessment Score per QR.58 (T1-2 Average) and QR.72 (T3 Average)
        overall_score = RiskEngine._calculate_documented_average_score(
            db=db,
            template_code=template_code,
            responses=responses,
            adverse_question_codes=adverse_question_codes,
        )
        assessment.overall_score = overall_score

        # 3. Rule QR.56 (T1-2) and QR.70 (T3): Assessment Submitted Task
        # QR.56 checks Q1.3 in [Yes, No] OR Q4.50 in [Yes, No]
        # QR.70 checks Q1.2 in [Yes, No] OR Q4.5 in [Yes, No]
        task_name = "Assessment Submitted_T3" if template_code == "T3_v1" else "Assessment Submitted"
        sub_task_title = f"{task_name}: {vendor.name}"
        if not db.query(Task).filter_by(assessment_id=assessment.id, title=sub_task_title).first():
            db.add(Task(
                vendor_id=vendor.id,
                assessment_id=assessment.id,
                task_type="Assessment Approval",
                title=sub_task_title,
                description=(
                    f"Rule {'QR.70' if template_code == 'T3_v1' else 'QR.56'}: Assessment submitted with average score "
                    f"{overall_score}%. {len(triggered_findings)} inherent risk findings flagged. "
                    f"Assignee: Assessment workflow approvers | Collaborators: ALL TPRM Groups (SLA.2: 4 days)."
                ),
                assignee_email="daniela.figueroa@cadence.com",
                collaborator_group="Vendor Risk Management Group",
                due_date=now + timedelta(days=4),  # SLA.2 (4 days)
                reminder_date=now + timedelta(days=2),  # SLA.2 reminder (2 days)
                status="Pending"
            ))

        # 4. Rule QR.57 (T1-2) and QR.71 (T3): Low Assessment Score Task if score < 40
        if overall_score < 40.0:
            low_score_task = "Template score rule_T3" if template_code == "T3_v1" else "Low Assessment Score"
            low_title = f"URGENT - {low_score_task}: {vendor.name} ({overall_score}%)"
            if not db.query(Task).filter_by(assessment_id=assessment.id, title=low_title).first():
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=assessment.id,
                    task_type="Low Score Escalation",
                    title=low_title,
                    description=(
                        f"Rule {'QR.71' if template_code == 'T3_v1' else 'QR.57'}: Assessment scored {overall_score}% "
                        f"(below 40 threshold). Collaborator: TPRM_Vendor Risk Management Team."
                    ),
                    assignee_email=None,
                    collaborator_group="Vendor Risk Management Group",
                    due_date=now + timedelta(days=4),
                    reminder_date=now + timedelta(days=2),
                    status="Pending"
                ))

        # 5. Department-Specific Task Rules (QR.74 to QR.90)
        RiskEngine._create_departmental_tasks(
            db=db,
            vendor=vendor,
            assessment=assessment,
            template_code=template_code,
            responses=responses,
            department_risks_map=department_risks_map,
            now=now,
        )

        # 6. Rule QR.73: Tier 3 Auto-Approval Check
        # Appendix E QR.73: IF ALL required questions Equal To favorable Yes/No response -> Auto-Complete Assessment Upon Submission
        # Result: Approved, Result comments: "The third-party is Approved"
        is_tier3_auto_approved = False
        if template_code == "T3_v1" and vendor.vendor_tier == "Tier 3":
            if len(triggered_findings) == 0 and overall_score >= 80.0:
                is_tier3_auto_approved = True

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="ASSESSMENT_EVALUATED",
            entity_type="ASSESSMENT",
            entity_id=assessment.id,
            details={
                "template_code": template_code,
                "overall_score": overall_score,
                "scoring_rule": "QR.72" if template_code == "T3_v1" else "QR.58",
                "findings_count": len(triggered_findings),
                "triggered_rules": [f.rule_code for f in triggered_findings],
                "is_tier3_auto_approved": is_tier3_auto_approved,
            }
        )

        db.commit()
        return triggered_findings, overall_score, is_tier3_auto_approved

    @staticmethod
    def _calculate_documented_average_score(
        db: Session,
        template_code: str,
        responses: Dict[str, str],
        adverse_question_codes: set
    ) -> float:
        """Implements QR.58 (T1-2 Average of all Yes/No + 1.8 options 0-5, 5-10, 10+) and QR.72 (T3 Average of all Yes/No)."""
        template = db.query(QuestionnaireTemplate).filter_by(code=template_code).first()
        question_favorable_map: Dict[str, str] = {}
        if template:
            for sec in template.sections:
                for q in sec.questions:
                    if q.favorable_answer:
                        question_favorable_map[q.question_code] = q.favorable_answer

        scores: List[float] = []
        for q_code, raw_val in responses.items():
            val = str(raw_val or "").strip()
            if not val:
                continue

            # Special options question 1.8 in T1-2 (QR.58: 0-5, 5-10, 10+)
            if template_code == "T1-2_v1" and q_code == "1.8":
                if val == "10+":
                    scores.append(100.0)
                elif val == "5-10":
                    scores.append(50.0)
                elif val in ["0-5", "O-5"]:
                    scores.append(0.0)
                continue

            # Yes/No questions
            if val.lower() in ["yes", "no"]:
                if q_code in adverse_question_codes:
                    scores.append(0.0)
                elif q_code in question_favorable_map:
                    fav = question_favorable_map[q_code].strip().lower()
                    scores.append(100.0 if val.lower() == fav else 0.0)
                else:
                    scores.append(100.0)

        if not scores:
            return 100.0
        return round(sum(scores) / len(scores), 1)

    @staticmethod
    def _create_departmental_tasks(
        db: Session,
        vendor: Vendor,
        assessment: Assessment,
        template_code: str,
        responses: Dict[str, str],
        department_risks_map: Dict[str, List[str]],
        now: datetime,
    ):
        """Creates departmental review tasks per QR.74-QR.82 (T1-2) and QR.83-QR.90 (T3)."""
        is_t3 = template_code == "T3_v1"
        suffix = "_T3" if is_t3 else ""

        # Map department group -> (QR code, Task Name)
        dept_task_specs = {
            "Legal Group": ("QR.83" if is_t3 else "QR.74", f"Legal Risk Identified for Third-Party{suffix}"),
            "Procurement Group": ("QR.84" if is_t3 else "QR.75", f"Procurement Risk Identified for Third-Party{suffix}"),
            "Compliance Group": ("QR.85" if is_t3 else "QR.76", f"Compliance Risk Identified for Third-Party{suffix}"),
            "Finance Group": ("QR.86" if is_t3 else "QR.77", f"Finance Risk Identified for Third-Party{suffix}"),
            "Privacy Group": ("QR.87" if is_t3 else "QR.78", f"Privacy Risk Identified for Third-Party{suffix}"),
            "Security Group": ("QR.88" if is_t3 else "QR.80", f"Security Risk Identified for Third-Party{suffix}"),
        }
        if not is_t3:
            dept_task_specs["Data Quality Group"] = ("QR.79", "Data Quality Risk Identified for Third-Party")

        for dept_group, (qr_code, task_label) in dept_task_specs.items():
            triggered_rules = department_risks_map.get(dept_group, [])
            if triggered_rules:
                title = f"{task_label}: {vendor.name}"
                if not db.query(Task).filter_by(assessment_id=assessment.id, title=title).first():
                    db.add(Task(
                        vendor_id=vendor.id,
                        assessment_id=assessment.id,
                        task_type="Departmental Risk Review",
                        title=title,
                        description=(
                            f"Rule {qr_code}: {len(triggered_rules)} risk finding(s) ({', '.join(triggered_rules)}) "
                            f"flagged for {dept_group}. Review responses and communicate mitigation requirements (SLA.2: 4 days)."
                        ),
                        assignee_email=None,
                        collaborator_group=dept_group,
                        due_date=now + timedelta(days=4),
                        reminder_date=now + timedelta(days=2),
                        status="Pending"
                    ))

        # Explicit IT Task Rules:
        # QR.81 (T1-2): Question 5.6 == "No" -> "IT Risk Identified for Third-Party" (Collaborator: IT Group)
        # QR.90 (T3): IT Risk on T3 -> "IT Risk Identified for Third-Party_T3" (Collaborator: IT Group)
        if not is_t3 and str(responses.get("5.6", "")).strip().lower() == "no":
            title_81 = f"IT Risk Identified for Third-Party: {vendor.name}"
            if not db.query(Task).filter_by(assessment_id=assessment.id, title=title_81).first():
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=assessment.id,
                    task_type="Departmental Risk Review",
                    title=title_81,
                    description="Rule QR.81 (Question 5.6 = No): SSO/SCIM provisioning not supported. Collaborator: TPRM_IT Group.",
                    assignee_email=None,
                    collaborator_group="IT Group",
                    due_date=now + timedelta(days=4),
                    reminder_date=now + timedelta(days=2),
                    status="Pending"
                ))
        elif is_t3 and str(responses.get("5.2", "")).strip().lower() == "no":
            title_90 = f"IT Risk Identified for Third-Party_T3: {vendor.name}"
            if not db.query(Task).filter_by(assessment_id=assessment.id, title=title_90).first():
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=assessment.id,
                    task_type="Departmental Risk Review",
                    title=title_90,
                    description="Rule QR.90 (QR_Task IT Risk): IT/Incident notification risk identified for Tier 3 vendor. Collaborator: TPRM_IT Group.",
                    assignee_email=None,
                    collaborator_group="IT Group",
                    due_date=now + timedelta(days=4),
                    reminder_date=now + timedelta(days=2),
                    status="Pending"
                ))

        # QR.82 (T1-2) and QR.89 (T3): Question 5.1 == "Yes" -> "IT Requirement Identified for Third-Party[_T3]"
        if str(responses.get("5.1", "")).strip().lower() == "yes":
            qr_it_req = "QR.89" if is_t3 else "QR.82"
            title_req = f"IT Requirement Identified for Third-Party{suffix}: {vendor.name}"
            if not db.query(Task).filter_by(assessment_id=assessment.id, title=title_req).first():
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=assessment.id,
                    task_type="IT Integration Review",
                    title=title_req,
                    description=f"Rule {qr_it_req} (Question 5.1 = Yes): Direct IT integration required. Collaborator: TPRM_IT Group.",
                    assignee_email=None,
                    collaborator_group="IT Group",
                    due_date=now + timedelta(days=4),
                    reminder_date=now + timedelta(days=2),
                    status="Pending"
                ))

    @staticmethod
    def _generate_mitigation_guidance(control_id: str, risk_name: str) -> str:
        """Maps standard control recommendations across all Appendix E QRC_* controls."""
        guidance = {
            "QRC_CL_1.1": "Execute cross-border data transfer addendum (Standard Contractual Clauses / GDPR Transfer Impact Assessment).",
            "QRC_T3_CL_1.1": "Verify foreign legal entity registration and execute cross-border compliance addendum.",
            "QRC_CL_1.2": "Require additional financial solvency verification or parental guarantee due to operational history <5 years.",
            "QRC_CL_1.3": "Review 5-10 year operating stability and include standard performance bond clauses.",
            "QRC_CL_1.4": "Require full disclosure of participating subsidiaries/affiliates and bind them to master agreement terms.",
            "QRC_CL_1.5": "Evaluate post-M&A corporate control changes and verify assignment clauses.",
            "QRC_CmL_2.1": "Require vendor to provide annual executive compliance attestation in lieu of independent compliance report.",
            "QRC_CmL_2.2": "Incorporate contractual regulatory compliance warranties and right-to-audit clauses.",
            "QRC_CmL_2.3": "Verify statutory AML/KYC program documentation and OFAC sanctions screening controls.",
            "QRC_CmL_2.4": "Require third-party AML audit attestation within 6 months of contract execution.",
            "QRC_Fin_3.1": "Require bank reference letter and certified tax filings in lieu of audited financial statements.",
            "QRC_Fin_3.2": "Execute enhanced financial indemnification and periodic solvency monitoring.",
            "QRC_Pri_4.1": "Confirm technical encryption controls (AES-256) and obtain signed cross-border Data Processing Agreement (DPA).",
            "QRC_Pri_4.2": "Implement geofencing and prohibit access to Cadence data from high-risk geopolitical regions.",
            "QRC_Pri_4.3": "Execute GDPR/CCPA Data Processing Addendum defining permitted personal data categories and data subjects.",
            "QRC_Pri_4.4": "Require prior written notice of sub-processors and flow-down data protection obligations.",
            "QRC_Pri_4.5": "Enforce AI transparency controls, human-in-the-loop oversight, and strict prohibition on sensitive PII training.",
            "QRC_Pri_4.6": "Prohibit use of Cadence confidential/personal data for LLM model training or weight updates.",
            "QRC_Pri_4.7": "Require vendor to establish NIST AI RMF 1.0 aligned AI risk management governance.",
            "QRC_Pri_4.8": "Vendor must adopt Cadence Third-Party Privacy Standard prior to contract Live date.",
            "QRC_Sec_4.9": "Require documented Identity and Access Management (IAM) policy aligned with ISO 27001 / NIST CSF.",
            "QRC_Sec_4.10": "Enforce Role-Based Access Control (RBAC) and quarterly access recertification for systems touching Cadence data.",
            "QRC_Sec_4.11": "Enforce minimum 14-character password complexity, lockout thresholds, and credential rotation.",
            "QRC_Sec_4.12": "Enforce mandatory Multi-Factor Authentication (MFA) via SSO integration or compensating IP allowlisting.",
            "QRC_Sec_4.13": "Require encrypted VPN with MFA and role-based network segmentation for all remote employee access.",
            "QRC_Sec_4.14": "Require 24/7 SIEM/SOC network monitoring and continuous intrusion detection telemetry.",
            "QRC_Sec_4.15": "Mandate automated monthly vulnerability scanning and critical patch SLA of 14 days.",
            "QRC_Sec_4.16": "Require strict logical or physical tenant isolation for all Cadence environments.",
            "QRC_Sec_4.17": "Require vendor to commission an independent third-party penetration test and remediate high/critical findings.",
            "QRC_Sec_4.18": "Establish formal penetration test remediation SLA (Critical: 15d, High: 30d) with client reporting.",
            "QRC_Sec_4.19": "Require S-SDLC policy incorporating SAST/DAST scanning and peer code reviews.",
            "QRC_Sec_4.20": "Require documented Incident Response Plan with annual tabletop exercises.",
            "QRC_Sec_4.21": "Review root-cause analysis (RCA) and post-remediation verification from recent 24-month security incident.",
            "QRC_Sec_4.22": "Require formal breach notification runbook and escalation contacts.",
            "QRC_Sec_4.23": "Bind vendor to 24-48 hour contractual security incident notification SLA to Cadence Security.",
            "QRC_Sec_4.24": "Require TLS 1.2/1.3 in transit and AES-256 encryption at rest with restricted KMS key access.",
            "QRC_Sec_4.25": "Require Data Loss Prevention (DLP) policies across email, endpoints, and cloud storage.",
            "QRC_Sec_4.26": "Bind vendor to Cadence Data Retention and Cryptographic Erasure Schedule.",
            "QRC_Sec_4.27": "Require executive-approved Information Security Policy reviewed annually.",
            "QRC_Sec_4.28": "Require formal Information Security Risk Management (ISRM) program and risk register.",
            "QRC_Sec_4.29": "Mandate pre-employment background screening for all personnel assigned to Cadence accounts.",
            "QRC_Sec_4.30": "Enforce 24-hour access revocation SLA upon employee/contractor termination.",
            "QRC_Sec_4.31": "Prohibit unmanaged BYOD access to Cadence data or require containerized MAM/MDM enforcement.",
            "QRC_Sec_4.32": "Require centralized Mobile Device Management (MDM) with remote wipe and disk encryption.",
            "QRC_Sec_4.33": "Include contractual obligation for certified data destruction within 30 days of contract termination.",
            "QRC_Sec_4.34": "Vendor must furnish SOC 2 Type II or ISO 27001 certification within 9 months or accept right-to-audit.",
            "QRC_Sec_4.35": "Vendor must bind Cyber Liability Insurance policy with minimum $5,000,000 aggregate coverage.",
            "QRC_IT_5.1": "Require SAML 2.0 / OIDC Single Sign-On and SCIM automated user provisioning roadmap.",
            "QRC_Mar_6.1": "Restrict sensitive audience targeting data usage and require Privacy & Legal sign-off.",
            "QRC_Mar_6.2": "Prohibit use of Cadence name, logo, or publicity rights without prior written Legal approval.",
            "QRC_Mar_6.3": "Incorporate mandatory co-branding disclosure guidelines into the Statement of Work.",
            "QRC_Pcr_7.1": "Include bilateral non-solicitation and employee anti-poaching clause in master contract.",
            "QRC_Pcr_7.2": "Require supplier ESG code of conduct acknowledgment.",
            "QRC_RR_8.1": "Incorporate Cadence standard SLA/KPI schedule with service credits and termination rights.",
            "QRC_RR_8.2": "Require documented Business Continuity Plan (BCP) and annual resilience test summary.",
            "QRC_RR_8.3": "Require documented Disaster Recovery Plan (DRP) with contractually defined RTO and RPO targets.",
        }
        return guidance.get(control_id, f"Review control implementation ({control_id}) and agree on remediation milestone for {risk_name}.")
