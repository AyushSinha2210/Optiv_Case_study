"""Authoritative Database Seeder for Cadence TPRM.

Populates organizations, 10 user groups, documented users, questionnaire templates (T1-2 v1 and T3 v1),
all 14 conditional rules (CL.1-14), all risk rules (QR.1-90), workflows, and initial vendors.
Source Authority: Cadence_TPRM_Training.docx.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from src.cadence_tprm.models import (
    Organization,
    Department,
    UserGroup,
    User,
    GroupMembership,
    Vendor,
    Contract,
    QuestionnaireTemplate,
    QuestionnaireSection,
    Question,
    ConditionalRule,
    RiskRule,
    Workflow,
    WorkflowInstance,
    Assessment,
    RiskFinding,
    Task,
    Notification,
    AuditLog,
)

def seed_database(db: Session):
    """Idempotently seeds authoritative baseline data."""

    # 1. Organization
    org = db.query(Organization).filter_by(name="Cadence Design Systems").first()
    if not org:
        org = Organization(
            name="Cadence Design Systems",
            domain="cadence.com",
            created_at=datetime.now(timezone.utc)
        )
        db.add(org)
        db.flush()

    # 2. Departments
    departments_data = [
        ("Vendor Risk Management", "VRM"),
        ("Legal", "LEGAL"),
        ("Procurement", "PROC"),
        ("Finance", "FIN"),
        ("IT", "IT"),
        ("Compliance", "COMP"),
        ("Privacy", "PRIV"),
        ("Security", "SEC"),
        ("Data Quality", "DQ"),
    ]
    for name, code in departments_data:
        if not db.query(Department).filter_by(code=code).first():
            db.add(Department(organization_id=org.id, name=name, code=code))
    db.flush()

    # 3. User Groups (Table 5)
    groups_data = [
        ("Vendor Risk Management Group", "Decision-making body for third-party assessments", "Admin"),
        ("Legal Group", "Responsible for reviewing legal and contracting workflows", "Edit"),
        ("Procurement Group", "Responsible for reviewing procurement workflows", "Edit"),
        ("Finance Group", "Responsible for reviewing finance workflows and tax forms", "Edit"),
        ("IT Group", "Responsible for reviewing IT systems and integration workflows", "Edit"),
        ("Compliance Group", "Responsible for reviewing compliance workflows and AML", "Edit"),
        ("Privacy Group", "Responsible for reviewing privacy workflows and AI data risks", "Edit"),
        ("Security Group", "Responsible for reviewing security posture and technical controls", "Edit"),
        ("Data Quality Group", "Responsible for reviewing data consistency and attribute accuracy", "Edit"),
    ]
    groups_map = {}
    for name, desc, perm in groups_data:
        g = db.query(UserGroup).filter_by(name=name).first()
        if not g:
            g = UserGroup(name=name, description=desc, default_permission=perm)
            db.add(g)
            db.flush()
        groups_map[name] = g

    # 4. Users (Table 5)
    users_roster = [
        ("daniela.figueroa@cadence.com", "Daniela Figueroa", True, [
            ("Vendor Risk Management Group", "Admin"),
            ("Legal Group", "Edit"),
            ("Finance Group", "Edit"),
            ("Data Quality Group", "Edit"),
        ]),
        ("bridgett.gatewood@cadence.com", "Bridgett Gatewood", True, [
            ("Vendor Risk Management Group", "Admin"),
        ]),
        ("kc.burney@cadence.com", "KC Burney", True, [
            ("Vendor Risk Management Group", "Admin"),
        ]),
        ("jyoti.karwal@cadence.com", "Jyoti Karwal", True, [
            ("Vendor Risk Management Group", "Admin"),
            ("IT Group", "Edit"),
        ]),
        ("tamika.oliver@cadence.com", "Tamika Oliver", False, [
            ("Vendor Risk Management Group", "Edit"),
            ("Compliance Group", "Edit"),
        ]),
        ("shimane.smith@cadence.com", "Shimane Smith", False, [
            ("Vendor Risk Management Group", "Edit"),
            ("Legal Group", "Edit"),
        ]),
        ("chris.schmitz@cadence.com", "Chris Schmitz", False, [
            ("Vendor Risk Management Group", "Edit"),
            ("Procurement Group", "Edit"),
        ]),
        ("chris.ott@cadence.com", "Chris Ott", False, [
            ("Vendor Risk Management Group", "Edit"),
            ("Security Group", "Edit"),
        ]),
        ("rob.tilney@cadence.com", "Rob Tilney", False, [
            ("Vendor Risk Management Group", "Edit"),
            ("IT Group", "Edit"),
        ]),
        ("jonathan.szeto@cadence.com", "Jonathan Szeto", False, [
            ("IT Group", "Edit"),
        ]),
        ("marc.otani@cadence.com", "Marc Otani", False, [
            ("IT Group", "Edit"),
        ]),
        ("dayo.seton@cadence.com", "Dayo Seton", False, [
            ("Privacy Group", "Edit"),
        ]),
        ("melisa.cardozo@cadence.com", "Melisa Cardozo", False, [
            ("Security Group", "Edit"),
        ]),
        ("dk.koran@cadence.com", "DK Koran", False, [
            ("Security Group", "Edit"),
        ]),
        ("erik.hansen@cadence.com", "Erik Hansen", False, [
            ("Security Group", "Edit"),
        ]),
    ]

    for email, full_name, is_admin, memberships in users_roster:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(
                organization_id=org.id,
                email=email,
                full_name=full_name,
                is_tprm_admin=is_admin,
                is_active=True
            )
            db.add(user)
            db.flush()

        for group_name, role_in_grp in memberships:
            group = groups_map.get(group_name)
            if group:
                existing_m = db.query(GroupMembership).filter_by(user_id=user.id, group_id=group.id).first()
                if not existing_m:
                    db.add(GroupMembership(user_id=user.id, group_id=group.id, role_in_group=role_in_grp))
    db.flush()

    # 5. Workflows (Table 6, 7, 8)
    workflows_list = [
        ("CD_Onboarding Workflow", "Central gateway workflow for analyzing vendor attributes and routing"),
        ("CD_Revenue Partners Workflow", "Dedicated lifecycle workflow for Revenue Partners (Tier 1 & Tier 2)"),
        ("CD_Marketing Partners Workflow", "Dedicated lifecycle workflow for Marketing Partners (Tier 1 & Tier 2)"),
        ("CD_Service Providers Workflow", "Dedicated lifecycle workflow for Service Providers and Vendors (Tier 1 & Tier 2)"),
        ("CD_Staffing Vendors Workflow", "Dedicated lifecycle workflow for Staffing Vendors (Tier 1 & Tier 2)"),
        ("CD_International Vendors Workflow", "Dedicated lifecycle workflow for International Vendors (Tier 1 & Tier 2)"),
        ("CD_Tier3 Workflow", "Simplified lifecycle workflow for Tier 3 Vendors with auto-approval rules"),
    ]
    for w_name, w_desc in workflows_list:
        if not db.query(Workflow).filter_by(name=w_name).first():
            db.add(Workflow(name=w_name, description=w_desc, is_active=True))
    db.flush()

    # 6. Questionnaire Templates & Sections (Table 11, Section 6.3)
    # 6.1 Due Diligence Questionnaire T1-2 v1
    t1_2 = db.query(QuestionnaireTemplate).filter_by(code="T1-2_v1").first()
    if not t1_2:
        t1_2 = QuestionnaireTemplate(
            code="T1-2_v1",
            name="Due Diligence Questionnaire T1-2 v1",
            description="Comprehensive security and operational questionnaire for Tier 1 and Tier 2 third parties.",
            version=1,
            is_published=True
        )
        db.add(t1_2)
        db.flush()

        sections_t1_2 = [
            (1, "1. Contracting and Legal", "Legal Group", [
                ("1.1", "Company Legal Name and Operating Aliases", "Text", None, False),
                ("1.2", "Company Registration Number and Jurisdiction", "Text", None, False),
                ("1.3", "Is the company incorporated within the United States?", "YesNo", ["Yes", "No"], False),
                ("1.4", "Company Headquarters Address and Executive Contact", "Text", None, False),
                ("1.5", "Are there foreign affiliates or foreign ownership involved?", "YesNo", ["Yes", "No"], False),
                ("1.6", "Please provide: State of Incorporation, Principal Place of Business, Parent Company / Affiliates, Foreign Ownership", "Text", None, True),
                ("1.7", "Please provide the date of incorporation", "Text", None, True),
                ("1.8", "How long has your company been in business?", "SingleChoice", ["0-5", "5-10", "10+"], True),
                ("1.9", "Does the company operate through active subsidiaries or affiliates?", "YesNo", ["Yes", "No"], False),
                ("1.10", "Has the company been involved in material litigation in the past 3 years?", "YesNo", ["Yes", "No"], False),
                ("1.11", "Has the organization undergone mergers, acquisitions, or restructuring in the past 24 months?", "YesNo", ["Yes", "No"], False),
            ]),
            (2, "2. Compliance and Legal", "Compliance Group", [
                ("2.1", "Does the organization maintain a formal Code of Business Conduct?", "YesNo", ["Yes", "No"], False),
                ("2.2", "Does the company produce independent annual compliance audit reports?", "YesNo", ["Yes", "No"], False),
                ("2.3", "Is the company subject to strict regulatory oversight (e.g., SEC, FCA, FINRA)?", "YesNo", ["Yes", "No"], False),
                ("2.4", "Does the company have a formalized customer complaint handling policy?", "YesNo", ["Yes", "No"], False),
                ("2.5", "Please provide a copy of your policy for handling consumer complaints", "Text", None, True),
                ("2.6", "Is the company subject to Anti-Money Laundering (AML) / KYC statutory requirements?", "YesNo", ["Yes", "No"], False),
                ("2.7", "Does the organization conduct regular third-party AML audits?", "YesNo", ["Yes", "No"], False),
            ]),
            (3, "3. Finance", "Finance Group", [
                ("3.1", "Primary financial institution and banking relationship", "Text", None, False),
                ("3.2", "Fiscal year end date and annual operating revenue bracket", "SingleChoice", ["<$5M", "$5M-$50M", "$50M-$250M", ">$250M"], False),
                ("3.3", "Can the company provide audited financial statements for the past 2 fiscal years?", "YesNo", ["Yes", "No"], False),
                ("3.4", "Has the company filed for bankruptcy or debt restructuring within the past 5 years?", "YesNo", ["Yes", "No"], False),
                ("3.5", "Are your financial statements certified by an independent accredited CPA firm?", "YesNo", ["Yes", "No"], False),
                ("3.6", "Has your company already registered in the Oracle Vendor Onboarding portal?", "YesNo", ["Yes", "No"], False),
                ("3.7", "If no, please complete the form here: Oracle Vendor Onboarding Form (link) and upload confirmation", "Text", None, True),
            ]),
            (4, "4. Data Privacy and Security", "Security Group", [
                ("4.1", "Will Cadence customer data be transferred, hosted, or accessed outside the United States?", "YesNo", ["Yes", "No"], False),
                ("4.2", "Does your organization maintain technical or operational support in high-risk regions?", "YesNo", ["Yes", "No"], False),
                ("4.3", "Does your solution process electronic Protected Health Information (ePHI)?", "YesNo", ["Yes", "No"], False),
                ("4.4", "Will personal data (PII) of Cadence employees or clients be collected or processed?", "YesNo", ["Yes", "No"], False),
                ("4.5", "Select Cadence data subjects involved in this engagement", "SingleChoice", ["Employees", "Customers", "Partners", "All"], True),
                ("4.6", "Describe and select personal data categories processed", "Text", None, True),
                ("4.7", "Does your organization comply with GDPR / CCPA data subject access request standards?", "YesNo", ["Yes", "No"], False),
                ("4.8", "Are downstream sub-processors engaged for Cadence data processing or storage?", "YesNo", ["Yes", "No"], False),
                ("4.9", "Do you maintain written Data Processing Agreements (DPAs) with all sub-processors?", "YesNo", ["Yes", "No"], False),
                ("4.10", "Does your solution incorporate Artificial Intelligence (AI) or Machine Learning models?", "YesNo", ["Yes", "No"], False),
                ("4.11", "Will AI models interact with Cadence customers or access sensitive employee information?", "YesNo", ["Yes", "No"], True),
                ("4.12", "Does the organization use AI or Large Language Models (LLMs) in data processing?", "YesNo", ["Yes", "No"], True),
                ("4.13", "Are there processes established for managing risks related to Artificial Intelligence?", "YesNo", ["Yes", "No"], True),
                ("4.14", "Does your organization publish and enforce a comprehensive Privacy Policy?", "YesNo", ["Yes", "No"], False),
                ("4.15", "Do you maintain a formalized Identity & Access Management (IAM) policy?", "YesNo", ["Yes", "No"], False),
                ("4.16", "Is role-based least privilege access enforced across production and client databases?", "YesNo", ["Yes", "No"], False),
                ("4.17", "Is a strict corporate password complexity policy enforced (length, expiration, rotation)?", "YesNo", ["Yes", "No"], False),
                ("4.18", "Is Multi-Factor Authentication (MFA) mandated for all administrative and remote access?", "YesNo", ["Yes", "No"], False),
                ("4.19", "If No - Please explain why MFA is not required (compensating controls, acceptable risk)", "Text", None, True),
                ("4.20", "Do employees utilize VPN for remote network access?", "YesNo", ["Yes", "No"], False),
                ("4.21", "If Yes - How is VPN secured and is access control based on user role?", "Text", None, True),
                ("4.22", "Is 24/7 automated network monitoring and intrusion detection (IDS/IPS) active?", "YesNo", ["Yes", "No"], False),
                ("4.23", "Does your company utilize automated vulnerability scanners with scheduled scans?", "YesNo", ["Yes", "No"], False),
                ("4.24", "Are multi-tenant environments segregated logically or physically?", "YesNo", ["Yes", "No"], False),
                ("4.25", "If Yes - Please describe separation method (Logical, Physical, VLAN, Cloud tenant)", "Text", None, True),
                ("4.26", "Has an independent third party performed an application penetration test within 12 months?", "YesNo", ["Yes", "No"], False),
                ("4.27", "Do you have a process for remediating critical/high findings from penetration tests with SLAs?", "YesNo", ["Yes", "No"], True),
                ("4.28", "Do you maintain a secure Software Development Life Cycle (S-SDLC) policy?", "YesNo", ["Yes", "No"], False),
                ("4.29", "Do you maintain a documented and tested Incident Response Plan?", "YesNo", ["Yes", "No"], False),
                ("4.30", "Has your organization suffered a security breach or incident in the past 24 months?", "YesNo", ["Yes", "No"], False),
                ("4.31", "If Yes - Please describe incident type, remediation actions, timeline, and residual risk", "Text", None, True),
                ("4.32", "Do you maintain a defined security breach notification process with defined timelines?", "YesNo", ["Yes", "No"], False),
                ("4.33", "Will Cadence be notified of security incidents affecting Cadence data within 48 hours?", "YesNo", ["Yes", "No"], False),
                ("4.34", "Is data encrypted in transit (TLS 1.2+) and at rest (AES-256)?", "YesNo", ["Yes", "No"], False),
                ("4.35", "How do you manage and store encryption keys (access restrictions, KMS)?", "Text", None, True),
                ("4.36", "Do you deploy Data Loss Prevention (DLP) controls across endpoints and networks?", "YesNo", ["Yes", "No"], False),
                ("4.37", "If Yes - Indicate scope of DLP (End-user devices, Email, File storage, Database, Cloud)", "Text", None, True),
                ("4.38", "Do you enforce a documented data retention and secure data destruction policy?", "YesNo", ["Yes", "No"], False),
                ("4.39", "Does your organization enforce a formal Information Security Policy approved by leadership?", "YesNo", ["Yes", "No"], False),
                ("4.40", "Do you maintain a dedicated risk management program for Information Security?", "YesNo", ["Yes", "No"], False),
                ("4.41", "Are information security awareness training sessions required annually for all staff?", "YesNo", ["Yes", "No"], False),
                ("4.42", "Are formal pre-employment background checks performed for all employees and contractors?", "YesNo", ["Yes", "No"], False),
                ("4.43", "Is access immediately revoked upon employee termination?", "YesNo", ["Yes", "No"], False),
                ("4.44", "Do you maintain a formal employee offboarding and asset reclamation process?", "YesNo", ["Yes", "No"], False),
                ("4.45", "Is Bring Your Own Device (BYOD) permitted for accessing corporate and client data?", "YesNo", ["Yes", "No"], False),
                ("4.46", "Do you enforce a centralized Mobile Device Management (MDM) policy on all devices?", "YesNo", ["Yes", "No"], False),
                ("4.47", "Is anti-malware and endpoint detection (EDR) installed across all corporate systems?", "YesNo", ["Yes", "No"], False),
                ("4.48", "Can your solution support complete, verifiable data deletion upon Cadence request?", "YesNo", ["Yes", "No"], False),
                ("4.49", "Does your organization hold valid security certifications (SOC 2 Type II, ISO 27001, PCI-DSS)?", "YesNo", ["Yes", "No"], False),
                ("4.50", "Does your organization maintain active Cyber Liability Insurance coverage?", "YesNo", ["Yes", "No"], False),
            ]),
            (5, "5. IT Systems and Integration", "IT Group", [
                ("5.1", "Does the engagement require direct integration with Cadence internal IT systems?", "YesNo", ["Yes", "No"], False),
                ("5.2", "Supported integration protocols (REST API, Webhooks, SFTP, GraphQL, DB connector)", "Text", None, False),
                ("5.3", "Does the vendor platform offer a sandbox / staging testing environment?", "YesNo", ["Yes", "No"], False),
                ("5.4", "Are API keys and secrets rotated at least every 90 days?", "YesNo", ["Yes", "No"], False),
                ("5.5", "Does your platform support Single Sign-On (SSO) via SAML 2.0 or OIDC?", "YesNo", ["Yes", "No"], False),
                ("5.6", "Does your platform support SCIM automated user provisioning and deprovisioning?", "YesNo", ["Yes", "No"], False),
            ]),
            (6, "6. Marketing", "Marketing Group", [
                ("6.1", "Will sensitive customer targeting data or market segment behavioral profiles be processed?", "YesNo", ["Yes", "No"], False),
                ("6.2", "Does the contract grant publicity rights or use of Cadence brand marks in marketing?", "YesNo", ["Yes", "No"], False),
                ("6.3", "Are co-branding and public disclosure guidelines documented in the contract?", "YesNo", ["Yes", "No"], False),
            ]),
            (7, "7. Procurement", "Procurement Group", [
                ("7.1", "Is the vendor an accredited diverse supplier (MBE, WBE, VBE, LGBTBE)?", "YesNo", ["Yes", "No"], False),
                ("7.2", "Does your organization maintain a non-solicitation and employee anti-poaching policy?", "YesNo", ["Yes", "No"], False),
                ("7.3", "Does your company have a documented Environmental, Social, and Governance (ESG) policy?", "YesNo", ["Yes", "No"], False),
            ]),
            (8, "8. Resiliency & Business Continuity", "Resiliency Group", [
                ("8.1", "Are specific service availability SLAs and KPI performance penalties included in the contract?", "YesNo", ["Yes", "No"], False),
                ("8.2", "What KPIs or SLAs are linked to this engagement? Please provide details", "Text", None, True),
                ("8.3", "Does your company maintain a documented Business Continuity Plan (BCP)?", "YesNo", ["Yes", "No"], False),
                ("8.4", "Does your company maintain a documented Disaster Recovery (DR) Plan with defined RTO/RPO?", "YesNo", ["Yes", "No"], False),
            ]),
        ]

        for s_num, s_title, s_grp, questions in sections_t1_2:
            sec = QuestionnaireSection(
                template_id=t1_2.id,
                section_number=s_num,
                title=s_title,
                responsible_group=s_grp,
                order_index=s_num
            )
            db.add(sec)
            db.flush()

            for idx, (q_code, q_prompt, q_type, q_opts, is_cond) in enumerate(questions, start=1):
                db.add(Question(
                    section_id=sec.id,
                    question_code=q_code,
                    prompt=q_prompt,
                    question_type=q_type,
                    options=q_opts,
                    is_required=True,
                    is_conditional=is_cond,
                    order_index=idx
                ))
        db.flush()

    # 6.2 Due Diligence Questionnaire T3 v1
    t3 = db.query(QuestionnaireTemplate).filter_by(code="T3_v1").first()
    if not t3:
        t3 = QuestionnaireTemplate(
            code="T3_v1",
            name="Due Diligence Questionnaire T3 v1",
            description="Simplified due diligence questionnaire for Tier 3 low-risk third parties.",
            version=1,
            is_published=True
        )
        db.add(t3)
        db.flush()

        sections_t3 = [
            (1, "1. Company Information", "Legal Group", [
                ("1.1", "Company Legal Name and Website URL", "Text", None, False),
                ("1.2", "Is the company incorporated within the United States?", "YesNo", ["Yes", "No"], False),
            ]),
            (2, "2. Compliance and Legal", "Compliance Group", [
                ("2.1", "Does the organization have a formal Code of Conduct?", "YesNo", ["Yes", "No"], False),
                ("2.2", "Is the company subject to Anti-Money Laundering (AML) statutory requirements?", "YesNo", ["Yes", "No"], False),
            ]),
            (3, "3. Finance", "Finance Group", [
                ("3.1", "Primary Banking Entity and Address", "Text", None, False),
                ("3.2", "Annual Operating Revenue Estimate", "SingleChoice", ["<$1M", "$1M-$10M", ">$10M"], False),
                ("3.3", "Does your company undergo independent financial audits?", "YesNo", ["Yes", "No"], False),
                ("3.4", "Has your company completed the Oracle Vendor Onboarding portal registration?", "YesNo", ["Yes", "No"], False),
                ("3.5", "If No, please complete the form here: Oracle Vendor Onboarding Form (link) and upload evidence", "Text", None, True),
            ]),
            (4, "4. Data Privacy and Information Security", "Security Group", [
                ("4.1", "Does your organization maintain and publish a Privacy Policy?", "YesNo", ["Yes", "No"], False),
                ("4.2", "Does your organization maintain a written Information Security Policy?", "YesNo", ["Yes", "No"], False),
                ("4.3", "Do you maintain a dedicated risk management program for Information Security?", "YesNo", ["Yes", "No"], False),
                ("4.4", "Is Cadence confidential data encrypted in transit and at rest?", "YesNo", ["Yes", "No"], False),
                ("4.5", "Does your company hold active Cyber Liability Insurance coverage?", "YesNo", ["Yes", "No"], False),
            ]),
            (5, "5. Incident Management", "Security Group", [
                ("5.1", "Does the vendor maintain a formal Incident Response Plan?", "YesNo", ["Yes", "No"], False),
                ("5.2", "Will Cadence be notified of security incidents affecting Cadence data within 48 hours?", "YesNo", ["Yes", "No"], False),
            ]),
            (6, "6. Resiliency", "Resiliency Group", [
                ("6.1", "Does your company maintain a documented Business Continuity Plan (BCP)?", "YesNo", ["Yes", "No"], False),
                ("6.2", "Does your company maintain a documented Disaster Recovery (DR) Plan?", "YesNo", ["Yes", "No"], False),
            ]),
        ]

        for s_num, s_title, s_grp, questions in sections_t3:
            sec = QuestionnaireSection(
                template_id=t3.id,
                section_number=s_num,
                title=s_title,
                responsible_group=s_grp,
                order_index=s_num
            )
            db.add(sec)
            db.flush()

            for idx, (q_code, q_prompt, q_type, q_opts, is_cond) in enumerate(questions, start=1):
                db.add(Question(
                    section_id=sec.id,
                    question_code=q_code,
                    prompt=q_prompt,
                    question_type=q_type,
                    options=q_opts,
                    is_required=True,
                    is_conditional=is_cond,
                    order_index=idx
                ))
        db.flush()

    # 7. Conditional Show Logic (Table 12: CL.1 to CL.14)
    cond_rules_data = [
        ("CL.1", "T1-2_v1", "1.5", "Equal To", "Yes", ["1.6", "1.7", "1.8"], "Show incorporation details, date, and business duration"),
        ("CL.2", "T1-2_v1", "2.4", "Equal To", "Yes", ["2.5"], "Show consumer complaint handling policy request"),
        ("CL.3", "T1-2_v1", "3.6", "Equal To", "No", ["3.7"], "Show Oracle Vendor Onboarding form link"),
        ("CL.4", "T1-2_v1", "4.4", "Equal To", "Yes", ["4.5", "4.6"], "Show data subjects and personal data categories"),
        ("CL.5", "T1-2_v1", "4.10", "Equal To", "Yes", ["4.11", "4.12", "4.13"], "Show AI interaction, LLM usage, and AI risk management questions"),
        ("CL.6", "T1-2_v1", "4.18", "Equal To", "No", ["4.19"], "Show MFA non-requirement justification question"),
        ("CL.7", "T1-2_v1", "4.20", "Equal To", "Yes", ["4.21"], "Show VPN security and role access question"),
        ("CL.8", "T1-2_v1", "4.24", "Equal To", "Yes", ["4.25"], "Show separation method question"),
        ("CL.9", "T1-2_v1", "4.26", "Equal To", "Yes", ["4.27"], "Show penetration test remediation SLAs question"),
        ("CL.10", "T1-2_v1", "4.30", "Equal To", "Yes", ["4.31"], "Show security incident details question"),
        ("CL.11", "T1-2_v1", "4.34", "Equal To", "Yes", ["4.35"], "Show encryption key management procedures question"),
        ("CL.12", "T1-2_v1", "4.36", "Equal To", "Yes", ["4.37"], "Show DLP scope question"),
        ("CL.13", "T1-2_v1", "8.1", "Equal To", "Yes", ["8.2"], "Show contractual SLAs and KPIs question"),
        ("CL.14", "T3_v1", "3.4", "Equal To", "No", ["3.5"], "Show Tier 3 Oracle Vendor Onboarding form link"),
    ]
    for r_code, t_code, q_trigger, op, resp, shown, desc in cond_rules_data:
        if not db.query(ConditionalRule).filter_by(rule_code=r_code).first():
            db.add(ConditionalRule(
                rule_code=r_code,
                template_code=t_code,
                trigger_question_code=q_trigger,
                trigger_operator=op,
                trigger_response=resp,
                shown_question_codes=shown,
                description=desc
            ))
    db.flush()

    # 8. Risk Scoring & Controls Rules (Table 14: QR.1 to QR.90)
    risk_rules_data = [
        # QR.1 to QR.55: Tier 1 & 2 rules
        ("QR.1", "T1-2_v1", "QR_Non US Company", "1.3", "Equal To", "No", "Create risk", "QRN_Non US Company", "High", "QRC_CL_1.1", "QRC_Non US Company", "Legal Group"),
        ("QR.2", "T1-2_v1", "QR_Business duration_less", "1.8", "Equal To", "0-5", "Create risk", "QRN_Business duration_less", "High", "QRC_CL_1.2", "QRC_Business duration_less", "Legal Group"),
        ("QR.3", "T1-2_v1", "QR_Business duration_medium", "1.8", "Equal To", "5-10", "Create risk", "QRN_Business duration_medium", "Medium", "QRC_CL_1.3", "QRC_Business duration_medium", "Legal Group"),
        ("QR.4", "T1-2_v1", "QR_Subsidiaries and Affiliates", "1.9", "Equal To", "Yes", "Create risk", "QRN_Subsidiaries and Affiliates", "Medium", "QRC_CL_1.4", "QRC_Subsidiaries and Affiliates", "Legal Group"),
        ("QR.5", "T1-2_v1", "QR_Recent M and A", "1.11", "Equal To", "Yes", "Create risk", "QRN_Recent M and A", "Medium", "QRC_CL_1.5", "QRC_Recent M and A", "Legal Group"),
        ("QR.6", "T1-2_v1", "QR_No Compliance Report", "2.2", "Equal To", "No", "Create risk", "QRN_No Compliance Report", "High", "QRC_CmL_2.1", "QRC_No Compliance Report", "Compliance Group"),
        ("QR.7", "T1-2_v1", "QR_No Strong Laws", "2.3", "Equal To", "No", "Create risk", "QRN_No Strong Laws", "Medium", "QRC_CmL_2.2", "QRC_No Strong Laws", "Compliance Group"),
        ("QR.8", "T1-2_v1", "QR_AML Requirement", "2.6", "Equal To", "Yes", "Create risk", "QRN_AML Requirement", "Medium", "QRC_CmL_2.3", "QRC_AML Requirement", "Compliance Group"),
        ("QR.9", "T1-2_v1", "QR_No AML Audit", "2.7", "Equal To", "No", "Create risk", "QRN_No AML Audit", "Medium", "QRC_CmL_2.4", "QRC_No AML Audit", "Compliance Group"),
        ("QR.10", "T1-2_v1", "QR_No Financial Statement", "3.3", "Equal To", "No", "Create risk", "QRN_No Financial Statement", "High", "QRC_Fin_3.1", "QRC_No Financial Statement", "Finance Group"),
        ("QR.11", "T1-2_v1", "QR_No Financial Audits", "3.5", "Equal To", "No", "Create risk", "QRN_No Financial Audits", "High", "QRC_Fin_3.2", "QRC_No Financial Audits", "Finance Group"),
        ("QR.12", "T1-2_v1", "QR_Cust_Data Outside US", "4.1", "Equal To", "Yes", "Create risk", "QRN_Cust_Data Outside US", "High", "QRC_Pri_4.1", "QRC_Cust_Data Outside US", "Privacy Group"),
        ("QR.13", "T1-2_v1", "QR_Operations_Risk Regions", "4.2", "Equal To", "Yes", "Create risk", "QRN_Operations_Risk Regions", "High", "QRC_Pri_4.2", "QRC_Operations_Risk Regions", "Privacy Group"),
        ("QR.14", "T1-2_v1", "QR_Personal Data Collected", "4.4", "Equal To", "Yes", "Create risk", "QRN_Personal Data Collected", "Medium", "QRC_Pri_4.3", "QRC_Personal Data Collected", "Privacy Group"),
        ("QR.15", "T1-2_v1", "QR_Sub-processor Used", "4.8", "Equal To", "Yes", "Create risk", "QRN_Sub-processor Used", "Medium", "QRC_Pri_4.4", "QRC_Sub-processor Used", "Privacy Group"),
        ("QR.16", "T1-2_v1", "QR_AI Interaction with Data", "4.11", "Equal To", "Yes", "Create risk", "QRN_AI Interaction with Data", "Medium", "QRC_Pri_4.5", "QRC_AI Interaction with Data", "Privacy Group"),
        ("QR.17", "T1-2_v1", "QR_LLM Use in Data Processing", "4.12", "Equal To", "Yes", "Create risk", "QRN_LLM Use in Data Processing", "Medium", "QRC_Pri_4.6", "QRC_LLM Use in Data Processing", "Privacy Group"),
        ("QR.18", "T1-2_v1", "QR_No RM for AI", "4.13", "Equal To", "No", "Create risk", "QRN_No RM for AI", "Medium", "QRC_Pri_4.7", "QRC_No RM for AI", "Privacy Group"),
        ("QR.19", "T1-2_v1", "QR_No Privacy Policy", "4.14", "Equal To", "No", "Create risk", "QRN_No Privacy Policy", "High", "QRC_Pri_4.8", "QRC_No Privacy Policy", "Privacy Group"),
        ("QR.20", "T1-2_v1", "QR_No IAM Policy", "4.15", "Equal To", "No", "Create risk", "QRN_No IAM Policy", "High", "QRC_Sec_4.9", "QRC_No IAM Policy", "Security Group"),
        ("QR.21", "T1-2_v1", "QR_No Least Privilege Access", "4.16", "Equal To", "No", "Create risk", "QRN_No Least Privilege Access", "Medium", "QRC_Sec_4.10", "QRC_No Least Privilege Access", "Security Group"),
        ("QR.22", "T1-2_v1", "QR_No Password Policy", "4.17", "Equal To", "No", "Create risk", "QRN_No Password Policy", "Medium", "QRC_Sec_4.11", "QRC_No Password Policy", "Security Group"),
        ("QR.23", "T1-2_v1", "QR_No MFA", "4.18", "Equal To", "No", "Create risk", "QRN_No MFA", "Medium", "QRC_Sec_4.12", "QRC_No MFA", "Security Group"),
        ("QR.24", "T1-2_v1", "QR_Employee Remote Access", "4.20", "Equal To", "Yes", "Create risk", "QRN_Employee Remote Access", "Medium", "QRC_Sec_4.13", "QRC_Employee Remote Access", "Security Group"),
        ("QR.25", "T1-2_v1", "QR_Network Not Monitored", "4.22", "Equal To", "No", "Create risk", "QRN_Network Not Monitored", "High", "QRC_Sec_4.14", "QRC_Network Not Monitored", "Security Group"),
        ("QR.26", "T1-2_v1", "QR_No Tools for Vulnerability Scan", "4.23", "Equal To", "No", "Create risk", "QRN_No Tools for Vulnerability Scan", "Medium", "QRC_Sec_4.15", "QRC_No Tools for Vulnerability Scan", "Security Group"),
        ("QR.27", "T1-2_v1", "QR_System Not Segrated", "4.24", "Equal To", "No", "Create risk", "QRN_System Not Segrated", "Medium", "QRC_Sec_4.16", "QRC_System Not Segrated", "Security Group"),
        ("QR.28", "T1-2_v1", "QR_No Pen Test", "4.26", "Equal To", "No", "Create risk", "QRN_No Pen Test", "High", "QRC_Sec_4.17", "QRC_No Pen Test", "Security Group"),
        ("QR.29", "T1-2_v1", "QR_No Remediation for Findings", "4.27", "Equal To", "No", "Create risk", "QRN_No Remediation for Findings", "Medium", "QRC_Sec_4.18", "QRC_No Remediation for Findings", "Security Group"),
        ("QR.30", "T1-2_v1", "QR_No Security App Dev Policy", "4.28", "Equal To", "No", "Create risk", "QRN_No Security App Dev Policy", "Medium", "QRC_Sec_4.19", "QRC_No Security App Dev Policy", "Security Group"),
        ("QR.31", "T1-2_v1", "QR_No Incident Response Plan", "4.29", "Equal To", "No", "Create risk", "QRN_No Incident Response Plan", "High", "QRC_Sec_4.20", "QRC_No Incident Response Plan", "Security Group"),
        ("QR.32", "T1-2_v1", "QR_24 Mon Security Incident", "4.30", "Equal To", "Yes", "Create risk", "QRN_24 Mon Security Incident", "High", "QRC_Sec_4.21", "QRC_24 Mon Security Incident", "Security Group"),
        ("QR.33", "T1-2_v1", "QR_No Breach Notification Process", "4.32", "Equal To", "No", "Create risk", "QRN_No Breach Notification Process", "High", "QRC_Sec_4.22", "QRC_No Breach Notification Process", "Security Group"),
        ("QR.34", "T1-2_v1", "QR_No Notification to Cadence", "4.33", "Equal To", "No", "Create risk", "QRN_No Notification to Cadence", "High", "QRC_Sec_4.23", "QRC_No Notification to Cadence", "Security Group"),
        ("QR.35", "T1-2_v1", "QR_No Encryption Used", "4.34", "Equal To", "No", "Create risk", "QRN_No Encryption Used", "High", "QRC_Sec_4.24", "QRC_No Encryption Used", "Security Group"),
        ("QR.36", "T1-2_v1", "QR_No Data Loss Prevention", "4.36", "Equal To", "No", "Create risk", "QRN_No Data Loss Prevention", "Medium", "QRC_Sec_4.25", "QRC_No Data Loss Prevention", "Security Group"),
        ("QR.37", "T1-2_v1", "QR_No Data Retention Policy", "4.38", "Equal To", "No", "Create risk", "QRN_No Data Retention Policy", "Medium", "QRC_Sec_4.26", "QRC_No Data Retention Policy", "Security Group"),
        ("QR.38", "T1-2_v1", "QR_No Information Security Policy", "4.39", "Equal To", "No", "Create risk", "QRN_No Information Security Policy", "High", "QRC_Sec_4.27", "QRC_No Information Security Policy", "Security Group"),
        ("QR.39", "T1-2_v1", "QR_No RM for Information Security", "4.40", "Equal To", "No", "Create risk", "QRN_No RM for Information Security", "High", "QRC_Sec_4.28", "QRC_No RM for Information Security", "Security Group"),
        ("QR.40", "T1-2_v1", "QR_No Background checks for Emp", "4.42", "Equal To", "No", "Create risk", "QRN_No Background checks for Emp", "Medium", "QRC_Sec_4.29", "QRC_No Background checks for Emp", "Security Group"),
        ("QR.41", "T1-2_v1", "QR_No Offboarding Process", "4.44", "Equal To", "No", "Create risk", "QRN_No Offboarding Process", "Medium", "QRC_Sec_4.30", "QRC_No Offboarding Process", "Security Group"),
        ("QR.42", "T1-2_v1", "QR_BYOD Allowed", "4.45", "Equal To", "Yes", "Create risk", "QRN_BYOD Allowed", "Medium", "QRC_Sec_4.31", "QRC_BYOD Allowed", "Security Group"),
        ("QR.43", "T1-2_v1", "QR_No MDM Policy", "4.46", "Equal To", "No", "Create risk", "QRN_No MDM Policy", "Medium", "QRC_Sec_4.32", "QRC_No MDM Policy", "Security Group"),
        ("QR.44", "T1-2_v1", "QR_No Data Deletion Supported", "4.48", "Equal To", "No", "Create risk", "QRN_No Data Deletion Supported", "Medium", "QRC_Sec_4.33", "QRC_No Data Deletion Supported", "Security Group"),
        ("QR.45", "T1-2_v1", "QR_No Security Certifications", "4.49", "Equal To", "No", "Create risk", "QRN_No Security Certifications", "High", "QRC_Sec_4.34", "QRC_No Security Certifications", "Security Group"),
        ("QR.46", "T1-2_v1", "QR_No Cyber Insurance", "4.50", "Equal To", "No", "Create risk", "QRN_No Cyber Insurance", "High", "QRC_Sec_4.35", "QRC_No Cyber Insurance", "Security Group"),
        ("QR.47", "T1-2_v1", "QR_No SSO_SCIM Provisioning", "5.6", "Equal To", "No", "Create risk", "QRN_No SSO_SCIM Provisioning", "Medium", "QRC_IT_5.1", "QRC_No SSO_SCIM Provisioning", "IT Group"),
        ("QR.48", "T1-2_v1", "QR_Sensitive Targeting Data", "6.1", "Equal To", "Yes", "Create risk", "QRN_Sensitive Targeting Data", "Medium", "QRC_Mar_6.1", "QRC_Sensitive Targeting Data", "Marketing Group"),
        ("QR.49", "T1-2_v1", "QR_Publicity Rights", "6.2", "Equal To", "Yes", "Create risk", "QRN_Publicity Rights", "Medium", "QRC_Mar_6.2", "QRC_Publicity Rights", "Marketing Group"),
        ("QR.50", "T1-2_v1", "QR_No Co-branding Disclosures", "6.3", "Equal To", "No", "Create risk", "QRN_No Co-branding Disclosures", "Medium", "QRC_Mar_6.3", "QRC_No Co-branding Disclosures", "Marketing Group"),
        ("QR.51", "T1-2_v1", "QR_No Employee Poaching Policy", "7.2", "Equal To", "No", "Create risk", "QRN_No Employee Poaching Policy", "Medium", "QRC_Pcr_7.1", "QRC_No Employee Poaching Policy", "Procurement Group"),
        ("QR.52", "T1-2_v1", "QR_No ESG Policy", "7.3", "Equal To", "No", "Create risk", "QRN_No ESG Policy", "Medium", "QRC_Pcr_7.2", "QRC_No ESG Policy", "Procurement Group"),
        ("QR.53", "T1-2_v1", "QR_No SLA KPI in Contract", "8.1", "Equal To", "No", "Create risk", "QRN_No SLA KPI in Contract", "High", "QRC_RR_8.1", "QRC_No SLA KPI in Contract", "Resiliency Group"),
        ("QR.54", "T1-2_v1", "QR_No Business Continuity Plan", "8.3", "Equal To", "No", "Create risk", "QRN_No Business Continuity Plan", "High", "QRC_RR_8.2", "QRC_No Business Continuity Plan", "Resiliency Group"),
        ("QR.55", "T1-2_v1", "QR_No Disaster Recovery Plan", "8.4", "Equal To", "No", "Create risk", "QRN_No Disaster Recovery Plan", "High", "QRC_RR_8.3", "QRC_No Disaster Recovery Plan", "Resiliency Group"),
        
        # QR.59 to QR.69: Tier 3 rules
        ("QR.59", "T3_v1", "QR_T3_Non-US Company", "1.2", "Equal To", "No", "Create risk", "QRN_T3_Non-US Company", "High", "QRC_T3_CL_1.1", "QRC_T3_Non US Company", "Legal Group"),
        ("QR.60", "T3_v1", "QR_T3_AML Requirement", "2.2", "Equal To", "Yes", "Create risk", "QRN_T3_AML Requirement", "Medium", "QRC_CmL_2.3", "QRC_AML Requirement", "Compliance Group"),
        ("QR.61", "T3_v1", "QR_T3_No Financial Audits", "3.3", "Equal To", "No", "Create risk", "QRN_T3_No Financial Audits", "High", "QRC_Fin_3.2", "QRC_No Financial Audits", "Finance Group"),
        ("QR.62", "T3_v1", "QR_T3_No Privacy Policy", "4.1", "Equal To", "No", "Create risk", "QRN_T3_No Privacy Policy", "High", "QRC_Pri_4.8", "QRC_No Privacy Policy", "Privacy Group"),
        ("QR.63", "T3_v1", "QR_T3_No Information Security Policy", "4.2", "Equal To", "No", "Create risk", "QRN_T3_No Information Security Policy", "High", "QRC_Sec_4.27", "QRC_No Information Security Policy", "Security Group"),
        ("QR.64", "T3_v1", "QR_T3_No RM for Information Security", "4.3", "Equal To", "No", "Create risk", "QRN_T3_No RM for Information Security", "High", "QRC_Sec_4.28", "QRC_No RM for Information Security", "Security Group"),
        ("QR.65", "T3_v1", "QR_T3_No Encryption Used", "4.4", "Equal To", "No", "Create risk", "QRN_T3_No Encryption Used", "High", "QRC_Sec_4.24", "QRC_No Encryption Used", "Security Group"),
        ("QR.66", "T3_v1", "QR_T3_No Cyber Insurance", "4.5", "Equal To", "No", "Create risk", "QRN_T3_No Cyber Insurance", "High", "QRC_Sec_4.35", "QRC_No Cyber Insurance", "Security Group"),
        ("QR.67", "T3_v1", "QR_T3_No Notification to Cadence", "5.2", "Equal To", "No", "Create risk", "QRN_T3_No Notification to Cadence", "High", "QRC_Sec_4.23", "QRC_No Notification to Cadence", "Security Group"),
        ("QR.68", "T3_v1", "QR_T3_No Business Continuity Plan", "6.1", "Equal To", "No", "Create risk", "QRN_T3_No Business Continuity Plan", "High", "QRC_RR_8.2", "QRC_No Business Continuity Plan", "Resiliency Group"),
        ("QR.69", "T3_v1", "QR_T3_No Disaster Recovery Plan", "6.2", "Equal To", "No", "Create risk", "QRN_T3_No Disaster Recovery Plan", "High", "QRC_RR_8.3", "QRC_No Disaster Recovery Plan", "Resiliency Group"),
    ]

    for r_code, t_code, r_name, q_code, op, val, act, r_n, inh, c_id, c_n, grp in risk_rules_data:
        if not db.query(RiskRule).filter_by(rule_code=r_code).first():
            db.add(RiskRule(
                rule_code=r_code,
                template_code=t_code,
                rule_name=r_name,
                trigger_question_code=q_code,
                trigger_operator=op,
                trigger_response=val,
                action_type=act,
                risk_name=r_n,
                inherent_risk=inh,
                control_id=c_id,
                control_name=c_n,
                responsible_group=grp
            ))
    db.flush()

    # 9. Realistic Initial Vendors across categories & tiers
    initial_vendors = [
        ("Apex Cloud Infrastructure Ltd", "Technology", "Critical", "security@apexcloud.com", "daniela.figueroa@cadence.com", "Tier 1", "Service Provider and Vendor", "https://apexcloud.com", "Live", "CD_Service Providers Workflow", "Live", datetime.now(timezone.utc) - timedelta(days=200)),
        ("Global Staffing Partners LLC", "Operations", "Medium", "contact@globalstaffing.com", "chris.schmitz@cadence.com", "Tier 2", "Staffing Vendor", "https://globalstaffing.com", "Live", "CD_Staffing Vendors Workflow", "Live", datetime.now(timezone.utc) - timedelta(days=500)),
        ("OmniChannel Revenue Growth Inc", "Strategic", "High", "admin@omnichannelrev.com", "shimane.smith@cadence.com", "Tier 1", "Revenue Partner", "https://omnichannelrev.com", "In Progress", "CD_Revenue Partners Workflow", "Launching RevPart", None),
        ("Digital Horizon Marketing Agency", "Consulting", "Medium", "ops@digitalhorizon.com", "daniela.figueroa@cadence.com", "Tier 2", "Marketing Partner", "https://digitalhorizon.com", "In Progress", "CD_Marketing Partners Workflow", "Review Reject MarPart", None),
        ("EuroData Consult GmbH", "Regulatory", "High", "privacy@eurodataconsult.de", "dayo.seton@cadence.com", "Tier 1", "International Vendor", "https://eurodataconsult.de", "In Progress", "CD_International Vendors Workflow", "Launching IntVen", None),
        ("Swift Courier Express", "Operations", "Low", "dispatch@swiftcourier.com", "rob.tilney@cadence.com", "Tier 3", "Service Provider and Vendor", "https://swiftcourier.com", "Live", "CD_Tier3 Workflow", "Live", datetime.now(timezone.utc) - timedelta(days=100)),
        ("NexGen AI Labs Inc", "Technology", "Critical", "security@nexgenai.io", "daniela.figueroa@cadence.com", "Tier 1", "Service Provider and Vendor", "https://nexgenai.io", "New", "CD_Onboarding Workflow", "New Third Party", None),
    ]

    for v_name, v_type, v_crit, pvc, b_owner, v_tier, v_cat, web, status, wf_name, stage, last_comp in initial_vendors:
        vendor = db.query(Vendor).filter_by(name=v_name).first()
        if not vendor:
            next_due = None
            if last_comp:
                days = 365 if v_tier == "Tier 1" else 730
                next_due = last_comp + timedelta(days=days)

            vendor = Vendor(
                name=v_name,
                type=v_type,
                criticality=v_crit,
                primary_vendor_contact=pvc,
                business_owner=b_owner,
                vendor_tier=v_tier,
                vendor_category=v_cat,
                website=web,
                lifecycle_status=status,
                current_workflow_name=wf_name,
                current_stage=stage,
                last_assessment_completion_date=last_comp,
                next_reassessment_due_date=next_due,
            )
            db.add(vendor)
            db.flush()

            # Create an assessment record for vendors in review or completed
            template_code = "T3_v1" if v_tier == "Tier 3" else "T1-2_v1"
            asm_status = "Approved" if status == "Live" else ("Rejected" if "Reject" in stage else "Submitted")
            asm = Assessment(
                vendor_id=vendor.id,
                template_code=template_code,
                respondent_email=pvc,
                approver_group="Vendor Risk Management Group",
                status=asm_status,
                overall_score=85.0 if asm_status == "Approved" else 35.0,
                due_date=datetime.now(timezone.utc) + timedelta(days=9),
                submitted_at=datetime.now(timezone.utc) - timedelta(days=3),
                completed_at=last_comp or (datetime.now(timezone.utc) if asm_status in ["Approved", "Rejected"] else None),
                decision_reason="Assessment approved following VRM team review" if asm_status == "Approved" else None,
                decision_by="daniela.figueroa@cadence.com" if asm_status in ["Approved", "Rejected"] else None,
            )
            db.add(asm)
            db.flush()

            # Create contracts
            db.add(Contract(
                vendor_id=vendor.id,
                contract_reference=f"IC-{v_tier[:2].upper()}-{vendor.id[:6].upper()}",
                title=f"Enterprise Master Services Agreement - {v_name}",
                source="Ironclad",
                status="Executed" if status == "Live" else "Draft",
                effective_date=datetime.now(timezone.utc).date() - timedelta(days=60),
                expiration_date=datetime.now(timezone.utc).date() + timedelta(days=305),
            ))

            # Add tasks and findings if adverse
            if "Reject" in stage:
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=asm.id,
                    task_type="Review Reject Followup",
                    title=f"Review Vendor Rejection - {v_name}",
                    description="Vendor rejected during assessment. Follow up with business owner within 14 days per WR.*.5.",
                    assignee_email=b_owner,
                    collaborator_group="Vendor Risk Management Group",
                    due_date=datetime.now(timezone.utc) + timedelta(days=14),
                    status="Pending"
                ))
                db.add(RiskFinding(
                    assessment_id=asm.id,
                    vendor_id=vendor.id,
                    rule_code="QR.45",
                    risk_name="QRN_No Security Certifications",
                    inherent_risk="High",
                    control_id="QRC_Sec_4.34",
                    control_name="QRC_No Security Certifications",
                    responsible_group="Security Group",
                    status="Open",
                    mitigation_recommendation="Vendor must attain SOC 2 Type II or ISO 27001 within 90 days.",
                    due_date=datetime.now(timezone.utc) + timedelta(days=9)
                ))

            # Add general Assessment Submitted task if pending
            if status == "In Progress" and "Reject" not in stage:
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=asm.id,
                    task_type="Assessment Review",
                    title=f"Review Assessment Submission - {v_name}",
                    description="Evaluate questionnaire responses and analyze inherent risks.",
                    assignee_email="daniela.figueroa@cadence.com",
                    collaborator_group="Vendor Risk Management Group",
                    due_date=datetime.now(timezone.utc) + timedelta(days=4),
                    reminder_date=datetime.now(timezone.utc) + timedelta(days=2),
                    status="Pending"
                ))

    # Commit all seeded records
    db.commit()
