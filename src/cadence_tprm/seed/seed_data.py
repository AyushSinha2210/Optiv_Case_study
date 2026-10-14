"""Authoritative Database Seeder for Cadence TPRM.

Populates:
- Organization (Cadence), 9 Departments, Roles, Permissions, 9 User Groups, and Synthetic Demo Users
- All 8 Section 5.2 Vendor Attribute Definitions
- All 7 Workflows with exact stages and all 45 Appendix A Workflow & Reassessment Rules (WR.* and AR.*)
- All 7 Appendix D SLAs (SLA.1 to SLA.7)
- Questionnaire Templates (Due Diligence Questionnaire T1-2 v1 & Due Diligence Questionnaire T3 v1)
- All 14 Appendix C Conditional Show-Logic Rules (CL.1 to CL.14)
- All 90 Appendix E Questionnaire Risk, Scoring, Auto-Approve, and Task Rules (QR.1 to QR.90)
- Initial Vendors, Assessments, Contracts, Renewal Decisions, Tasks, and Audit Logs
Source Authority: Cadence_TPRM_Training.docx.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from src.cadence_tprm.models import (
    Organization,
    Department,
    Role,
    Permission,
    UserGroup,
    User,
    GroupMembership,
    Vendor,
    VendorAttributeDefinition,
    Contract,
    RenewalDecision,
    QuestionnaireTemplate,
    QuestionnaireSection,
    Question,
    ConditionalRule,
    RiskRule,
    Workflow,
    WorkflowRuleSpec,
    SLAConfig,
    WorkflowInstance,
    WorkflowTransition,
    Assessment,
    QuestionResponse,
    RiskFinding,
    Task,
    Notification,
    AuditLog,
)

def seed_database(db: Session):
    """Idempotently seeds authoritative baseline data from Cadence_TPRM_Training.docx."""

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
        ("Vendor Risk Management", "VRM", "Enterprise TPRM administration, governance, and final approval decisions"),
        ("Legal", "LEGAL", "Contracting, legal risk review, foreign entity and dispute evaluation"),
        ("Procurement", "PROC", "Supplier onboarding, commercial terms, and procurement risk review"),
        ("Finance", "FIN", "Financial statement verification, audit review, and Oracle onboarding"),
        ("IT", "IT", "IT systems integration, SSO/SCIM provisioning, and technical compatibility"),
        ("Compliance", "COMP", "Regulatory compliance, AML statutory review, and ethics oversight"),
        ("Privacy", "PRIV", "Personal data protection, cross-border transfers, confidentiality, and AI/LLM governance"),
        ("Security", "SEC", "Cybersecurity controls, SOC/ISO/PCI certifications, and technical risk assessments"),
        ("Data Quality", "DQ", "Vendor inventory integrity, attribute accuracy, and data quality review"),
    ]
    dept_map = {}
    for name, code, desc in departments_data:
        dept = db.query(Department).filter_by(code=code).first()
        if not dept:
            dept = Department(organization_id=org.id, name=name, code=code, description=desc)
            db.add(dept)
            db.flush()
        dept_map[code] = dept

    # 3. Roles & Permissions (Section 2.3, 4.2, 6.1, 7.11)
    permissions_data = [
        ("vendor:read", "Vendor", "read", "View third-party vendor inventory and details"),
        ("vendor:write", "Vendor", "write", "Create and update vendor records and classification"),
        ("vendor:approve", "Vendor", "approve", "Approve or reject third-party vendor assessments"),
        ("vendor:offboard", "Vendor", "offboard", "Initiate offboarding and move vendors to Closed/Archived"),
        ("questionnaire:read", "Questionnaire", "read", "View questionnaire templates and responses"),
        ("questionnaire:respond", "Questionnaire", "respond", "Fill and submit assigned due diligence questionnaires"),
        ("questionnaire:review", "Questionnaire", "review", "Review departmental questionnaire sections and flag risks"),
        ("questionnaire:admin", "Questionnaire", "admin", "Create, edit, version, and publish questionnaire templates"),
        ("risk:manage", "RiskFinding", "manage", "Acknowledge, remediate, and update risk findings and controls"),
        ("workflow:admin", "Workflow", "admin", "Configure workflows, stages, and automation rules"),
        ("attribute:admin", "Attribute", "admin", "Create, edit, and deactivate vendor attributes"),
        ("user:admin", "Organization", "admin", "Manage users, groups, roles, and memberships"),
        ("report:export", "Report", "export", "Generate and export operational and audit reports"),
    ]
    for p_code, res, act, desc in permissions_data:
        if not db.query(Permission).filter_by(code=p_code).first():
            db.add(Permission(code=p_code, resource=res, action=act, description=desc))
    db.flush()

    roles_data = [
        ("TPRM_ADMIN", "TPRM Administrator", "Full Admin for TPRM module (Vendor Risk Management Group Admin)", [p[0] for p in permissions_data]),
        ("VRM_EDIT", "VRM Reviewer (Edit)", "Edit access in Vendor Risk Management Group for assessment oversight without admin config/approval", [
            "vendor:read", "vendor:write", "questionnaire:read", "questionnaire:review", "risk:manage", "report:export"
        ]),
        ("DEPT_REVIEWER", "Departmental Reviewer (Edit)", "Edit access for assigned departmental questionnaire sections and risk findings", [
            "vendor:read", "questionnaire:read", "questionnaire:review", "risk:manage", "report:export"
        ]),
        ("VENDOR_RESPONDENT", "Primary Vendor Contact (Respondent)", "External vendor point-of-contact completing assigned questionnaires", [
            "questionnaire:read", "questionnaire:respond"
        ]),
    ]
    for r_code, r_name, r_desc, r_perms in roles_data:
        if not db.query(Role).filter_by(code=r_code).first():
            db.add(Role(code=r_code, name=r_name, description=r_desc, permissions=r_perms))
    db.flush()

    # 4. User Groups (Section 4.2 Table)
    groups_data = [
        ("Vendor Risk Management Group", "VRM", "Composed of senior or executive-level stakeholders. This group is the decision-making body for third-party assessments.", "Admin", ["All Sections (1-8)"]),
        ("Legal Group", "LEGAL", "This group includes the users from the Legal team who are responsible for reviewing workflows.", "Edit", ["1. Contracting and Legal", "2. Compliance and Legal"]),
        ("Procurement Group", "PROC", "This group includes the users from the Procurement team who are responsible for reviewing workflows.", "Edit", ["7. Procurement Process"]),
        ("Finance Group", "FIN", "This group includes the users from the Finance team who are responsible for reviewing workflows.", "Edit", ["3. Finance"]),
        ("IT Group", "IT", "This group includes the users from the IT team who are responsible for reviewing workflows.", "Edit", ["5. IT Systems and Integration"]),
        ("Compliance Group", "COMP", "This group includes the users from the Compliance team who are responsible for reviewing workflows.", "Edit", ["2. Compliance and Legal", "8. Resiliency & Business Continuity"]),
        ("Privacy Group", "PRIV", "This group includes the users from the Privacy team who are responsible for reviewing workflows and risk flagged for privacy section.", "Edit", ["4. Data Privacy and Security (Privacy & AI)"]),
        ("Security Group", "SEC", "This group includes the users from the Security team who are responsible for reviewing workflows and risk flagged for security section.", "Edit", ["4. Data Privacy and Security (Security & Certs)", "8. Resiliency & Business Continuity"]),
        ("Data Quality Group", "DQ", "This group includes the users from the Data Quality team who are responsible for reviewing workflows.", "Edit", ["Vendor Attributes & Data Quality"]),
    ]
    groups_map = {}
    for name, dept_code, desc, perm, rev_secs in groups_data:
        g = db.query(UserGroup).filter_by(name=name).first()
        if not g:
            dept = dept_map.get(dept_code)
            g = UserGroup(
                department_id=dept.id if dept else None,
                name=name,
                description=desc,
                default_permission=perm,
                review_sections=rev_secs
            )
            db.add(g)
            db.flush()
        groups_map[name] = g

    # 5. Synthetic Demo Users (Section 4.2 & Section 7.10)
    users_roster = [
        ("daniela.figueroa@cadence.com", "Daniela Figueroa (Synthetic Demo)", "VRM Executive Lead", "VRM", True, [
            ("Vendor Risk Management Group", "Admin", "TPRM_ADMIN"),
            ("Legal Group", "Edit", "DEPT_REVIEWER"),
            ("Finance Group", "Edit", "DEPT_REVIEWER"),
            ("Data Quality Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("bridgett.gatewood@cadence.com", "Bridgett Gatewood (Synthetic Demo)", "VRM Principal Administrator", "VRM", True, [
            ("Vendor Risk Management Group", "Admin", "TPRM_ADMIN"),
        ]),
        ("kc.burney@cadence.com", "KC Burney (Synthetic Demo)", "VRM Director", "VRM", True, [
            ("Vendor Risk Management Group", "Admin", "TPRM_ADMIN"),
        ]),
        ("jyoti.karwal@cadence.com", "Jyoti Karwal (Synthetic Demo)", "VRM & IT Governance Lead", "VRM", True, [
            ("Vendor Risk Management Group", "Admin", "TPRM_ADMIN"),
            ("IT Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("tamika.oliver@cadence.com", "Tamika Oliver (Synthetic Demo)", "Compliance & VRM Specialist", "COMP", False, [
            ("Vendor Risk Management Group", "Edit", "VRM_EDIT"),
            ("Compliance Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("shimane.smith@cadence.com", "Shimane Smith (Synthetic Demo)", "Legal Counsel & VRM Reviewer", "LEGAL", False, [
            ("Vendor Risk Management Group", "Edit", "VRM_EDIT"),
            ("Legal Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("chris.schmitz@cadence.com", "Chris Schmitz (Synthetic Demo)", "Procurement Lead & VRM Reviewer", "PROC", False, [
            ("Vendor Risk Management Group", "Edit", "VRM_EDIT"),
            ("Procurement Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("chris.ott@cadence.com", "Chris Ott (Synthetic Demo)", "Security Architect & VRM Reviewer", "SEC", False, [
            ("Vendor Risk Management Group", "Edit", "VRM_EDIT"),
            ("Security Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("rob.tilney@cadence.com", "Rob Tilney (Synthetic Demo)", "IT Systems Reviewer & VRM Edit", "IT", False, [
            ("Vendor Risk Management Group", "Edit", "VRM_EDIT"),
            ("IT Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("jonathan.szeto@cadence.com", "Jonathan Szeto (Synthetic Demo)", "IT Integration Engineer", "IT", False, [
            ("IT Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("marc.otani@cadence.com", "Marc Otani (Synthetic Demo)", "IT Infrastructure Specialist", "IT", False, [
            ("IT Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("dayo.seton@cadence.com", "Dayo Seton (Synthetic Demo)", "Privacy & AI Governance Lead", "PRIV", False, [
            ("Privacy Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("melisa.cardozo@cadence.com", "Melisa Cardozo (Synthetic Demo)", "Security Compliance Analyst", "SEC", False, [
            ("Security Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("dk.koran@cadence.com", "DK Koran (Synthetic Demo)", "Cloud Security Reviewer", "SEC", False, [
            ("Security Group", "Edit", "DEPT_REVIEWER"),
        ]),
        ("erik.hansen@cadence.com", "Erik Hansen (Synthetic Demo)", "Penetration Testing & Controls Reviewer", "SEC", False, [
            ("Security Group", "Edit", "DEPT_REVIEWER"),
        ]),
    ]

    for email, full_name, title, dept_code, is_admin, memberships in users_roster:
        user = db.query(User).filter_by(email=email).first()
        dept = dept_map.get(dept_code)
        if not user:
            user = User(
                organization_id=org.id,
                department_id=dept.id if dept else None,
                email=email,
                full_name=full_name,
                title=title,
                is_tprm_admin=is_admin,
                is_active=True,
                is_synthetic=True,
            )
            db.add(user)
            db.flush()

        for group_name, role_in_grp, role_code in memberships:
            group = groups_map.get(group_name)
            if group:
                existing_m = db.query(GroupMembership).filter_by(user_id=user.id, group_id=group.id).first()
                if not existing_m:
                    db.add(GroupMembership(
                        user_id=user.id,
                        group_id=group.id,
                        role_in_group=role_in_grp,
                        role_code=role_code
                    ))
    db.flush()

    # 6. Section 5.2 & 6.2 Vendor Attribute Definitions
    attributes_data = [
        ("Name", "Name", "Default system attribute representing the third-party name, automatically imported from Ironclad into OneTrust.", "Text", [], "System", True, False),
        ("Type", "Type", "Represents the nature of vendor engagement (e.g., Consulting, Operations, Regulatory). Used for classification and reporting.", "Single select", ["Consulting", "Operations", "Regulatory", "Strategic", "Technology", "Unknown"], "Custom", True, False),
        ("Criticality", "Criticality", "It indicates the business importance of the third-party. Though optional, it can be used for prioritization.", "Single select", ["Critical", "High", "Medium", "Low"], "Custom", False, False),
        ("Primary vendor contact", "Primary vendor contact", "Mandatory attribute that stores the vendor point of contact (POC) email address. Used for automated questionnaire distribution.", "Email", [], "System", True, True),
        ("Business Owner", "Business Owner", "Identifies the internal requestor or process owner responsible for managing the third-party relationship.", "Email", [], "System", True, True),
        ("Vendor Tier", "Vendor Tier", "Custom attribute used to classify vendors into Tier 1, Tier 2, or Tier 3 based on data sensitivity and risk exposure. Determines reassessment and renewal cadence.", "Single select", ["Tier 1", "Tier 2", "Tier 3"], "Custom", True, True),
        ("Vendor Category", "Vendor Category", "Custom attribute used to assign the appropriate workflow for a new vendor based on the vendor type (e.g., Service Provider, Marketing Partner, Staffing, etc.).", "Single select", ["Service Provider and Vendor", "Revenue Partner", "Marketing Partner", "Staffing Vendor", "International Vendor"], "Custom", True, True),
        ("Website", "Website", "This is a system attribute that can be used to automatically connect the third-party to the Third-Party Exchange.", "URL", [], "System", False, False),
    ]
    for key_name, disp, desc, r_type, opts, src, mandatory, wf_driver in attributes_data:
        if not db.query(VendorAttributeDefinition).filter_by(key_name=key_name).first():
            db.add(VendorAttributeDefinition(
                key_name=key_name,
                display_name=disp,
                description_key=desc,
                response_type=r_type,
                options=opts,
                source=src,
                direction="From: Ironclad To: OneTrust",
                is_mandatory=mandatory,
                is_active=True,
                is_workflow_driver=wf_driver,
            ))
    db.flush()

    # 7. Workflows (Section 4.2, 6.4, Appendix A)
    workflows_list = [
        ("CD_Onboarding Workflow", "Central gateway workflow analyzing Vendor Category and Vendor Tier attributes to assign category/tier workflow.", True, [
            {"name": "New Third Party", "badge_color": "New", "description": "Entry stage analyzing third-party attributes from Ironclad and routing via On_T_Assign Workflow (WR.ON.1-6).", "is_used": True},
            {"name": "Live", "badge_color": "Live", "description": "Present in workflow definition as final stage but not used directly (vendors transition to category/tier workflows).", "is_used": False},
        ]),
        ("CD_Revenue Partners Workflow", "Dedicated lifecycle workflow for Revenue Partners (Tier 1 & Tier 2).", False, [
            {"name": "New", "badge_color": "New", "description": "Present in template but not used.", "is_used": False},
            {"name": "Initiated", "badge_color": "New", "description": "Entry stage evaluating WR.RP.1 to advance to Launching RevPart.", "is_used": True},
            {"name": "Launching RevPart", "badge_color": "In Review", "description": "Launches Due Diligence Questionnaire T1-2 v1 to Primary Vendor Contact (WR.RP.2).", "is_used": True},
            {"name": "Review Reject RevPart", "badge_color": "Rejected", "description": "Rejection review stage triggering notification and 14-day Business Owner task (PWR.RP.4, WR.RP.5).", "is_used": True},
            {"name": "Live", "badge_color": "Live", "description": "Active approved vendor stage (WR.RP.3, WR.RP.6).", "is_used": True},
            {"name": "Closed", "badge_color": "Closed", "description": "Manual closure stage after offboarding completion.", "is_used": True},
        ]),
        ("CD_Marketing Partners Workflow", "Dedicated lifecycle workflow for Marketing Partners (Tier 1 & Tier 2).", False, [
            {"name": "New", "badge_color": "New", "description": "Present in template but not used.", "is_used": False},
            {"name": "Initiated", "badge_color": "New", "description": "Entry stage evaluating WR.MP.1 to advance to Launching MarPart.", "is_used": True},
            {"name": "Launching MarPart", "badge_color": "In Review", "description": "Launches Due Diligence Questionnaire T1-2 v1 to Primary Vendor Contact (WR.MP.2).", "is_used": True},
            {"name": "Review Reject MarPart", "badge_color": "Rejected", "description": "Rejection review stage triggering notification and 14-day Business Owner task (WR.MP.4, WR.MP.5).", "is_used": True},
            {"name": "Live", "badge_color": "Live", "description": "Active approved vendor stage (WR.MP.3, WR.MP.6).", "is_used": True},
            {"name": "Closed", "badge_color": "Closed", "description": "Manual closure stage after offboarding completion.", "is_used": True},
        ]),
        ("CD_International Vendors Workflow", "Dedicated lifecycle workflow for International Vendors (Tier 1 & Tier 2).", False, [
            {"name": "New", "badge_color": "New", "description": "Present in template but not used.", "is_used": False},
            {"name": "Initiated", "badge_color": "New", "description": "Entry stage evaluating WR.IV.1 to advance to Launching IntVen.", "is_used": True},
            {"name": "Launching IntVen", "badge_color": "In Review", "description": "Launches Due Diligence Questionnaire T1-2 v1 to Primary Vendor Contact (WR.IV.2).", "is_used": True},
            {"name": "Review Reject IntVen", "badge_color": "Rejected", "description": "Rejection review stage triggering notification and 14-day Business Owner task (WR.IV.4, WR.IV.5).", "is_used": True},
            {"name": "Live", "badge_color": "Live", "description": "Active approved vendor stage (WR.IV.3, WR.IV.6).", "is_used": True},
            {"name": "Closed", "badge_color": "Closed", "description": "Manual closure stage after offboarding completion.", "is_used": True},
        ]),
        ("CD_Service Providers Workflow", "Dedicated lifecycle workflow for Service Providers and Vendors (Tier 1 & Tier 2).", False, [
            {"name": "New", "badge_color": "New", "description": "Present in template but not used.", "is_used": False},
            {"name": "Initiated", "badge_color": "New", "description": "Entry stage evaluating WR.SP.1 to advance to Launching ServPro.", "is_used": True},
            {"name": "Launching ServPro", "badge_color": "In Review", "description": "Launches Due Diligence Questionnaire T1-2 v1 to Primary Vendor Contact (WR.SP.2).", "is_used": True},
            {"name": "Review Reject ServPro", "badge_color": "Rejected", "description": "Rejection review stage triggering notification and 14-day Business Owner task (WR.SP.4, WR.SP.5).", "is_used": True},
            {"name": "Live", "badge_color": "Live", "description": "Active approved vendor stage (WR.SP.3, WR.SP.6).", "is_used": True},
            {"name": "Closed", "badge_color": "Closed", "description": "Manual closure stage after offboarding completion.", "is_used": True},
        ]),
        ("CD_Staffing Vendors Workflow", "Dedicated lifecycle workflow for Staffing Vendors (Tier 1 & Tier 2).", False, [
            {"name": "New", "badge_color": "New", "description": "Present in template but not used.", "is_used": False},
            {"name": "Initiated", "badge_color": "New", "description": "Entry stage evaluating WR.SV.1 to advance to Launching StafVen.", "is_used": True},
            {"name": "Launching StafVen", "badge_color": "In Review", "description": "Launches Due Diligence Questionnaire T1-2 v1 to Primary Vendor Contact (WR.SV.2).", "is_used": True},
            {"name": "Review Reject StafVen", "badge_color": "Rejected", "description": "Rejection review stage triggering notification and 14-day Business Owner task (WR.SV.4, WR.SV.5).", "is_used": True},
            {"name": "Live", "badge_color": "Live", "description": "Active approved vendor stage (WR.SV.3, WR.SV.6).", "is_used": True},
            {"name": "Closed", "badge_color": "Closed", "description": "Manual closure stage after offboarding completion.", "is_used": True},
        ]),
        ("CD_Tier3 Workflow", "Simplified lifecycle workflow for Tier 3 Vendors with auto-approval rules.", False, [
            {"name": "New", "badge_color": "New", "description": "Present in template but not used.", "is_used": False},
            {"name": "Initiated", "badge_color": "New", "description": "Entry stage evaluating WR.T3.1 to advance to Launching Tier3.", "is_used": True},
            {"name": "Launching Tier3", "badge_color": "In Review", "description": "Launches Due Diligence Questionnaire T3 v1 to Primary Vendor Contact (WR.T3.2).", "is_used": True},
            {"name": "Review Reject Tier3", "badge_color": "Rejected", "description": "Rejection review stage triggering notification and 14-day Business Owner task (WR.T3.4, WR.T3.5).", "is_used": True},
            {"name": "Live", "badge_color": "Live", "description": "Active approved vendor stage with 24-month reassessment cadence (WR.T3.3, WR.T3.6).", "is_used": True},
            {"name": "Closed", "badge_color": "Closed", "description": "Manual closure stage after offboarding completion.", "is_used": True},
        ]),
    ]
    for w_name, w_desc, is_def, w_stages in workflows_list:
        wf = db.query(Workflow).filter_by(name=w_name).first()
        if not wf:
            db.add(Workflow(
                name=w_name,
                description=w_desc,
                status="Published",
                is_default=is_def,
                is_active=True,
                stages=w_stages
            ))
    db.flush()

    # 8. Appendix A Workflow & Reassessment Rule Specifications (45 Rules)
    appendix_a_rules = [
        # Revenue Partners
        ("WR.RP.1", "WR.RP.1", "RP_R_Push to Next", "CD_Revenue Partners Workflow", "Initiated", "RP_T_Push to Next", "Vendor Created", "Workflow Rule", "To push the third-party to the next stage in Revenue Partners Workflow", "Attribute: Vendor Category Contains Any: Revenue Partner AND Attribute: Vendor Category [Vendor Tier] Does not contain: Tier 3", "Advance to stage: Launching RevPart", "Source table states 'Attribute: Vendor Category Does not contain: Tier 3' as a clerical typo for 'Attribute: Vendor Tier Does not contain: Tier 3'."),
        ("WR.RP.2", "WR.RP.2", "Send RevPart Questionnaire", "CD_Revenue Partners Workflow", "Launching RevPart", None, None, "Stage Rule", "To launch third-party due diligence assessment for the third-party", "Attribute: Vendor Category Contains Any: Revenue Partner AND Attribute: Vendor Tier Does not contain: Tier 3", "Launch Assessment: Due Diligence Questionnaire T1-2 v1 | Approver: TPRM_Vendor Risk Management Team | Respondent: Primary Vendor Contact", None),
        ("WR.RP.3", "WR.RP.3", "RP_R_Assessment Approved", "CD_Revenue Partners Workflow", "Launching RevPart", "RP_T_Assessment Approved", "Approved", "Workflow Rule", "To move the third party to the next stage when the third-party is approved.", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1", "Advance to stage: Live", None),
        ("WR.RP.4", "PWR.RP.4", "RP_R_Assessment Rejected", "CD_Revenue Partners Workflow", "Launching RevPart", "RP_T_Assessment Rejected", "Rejected", "Workflow Rule", "To move the rejected third-party to the appropriate stage Review Reject RevPart", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1", "Advance to stage: Review Reject RevPart", "Source SR. NO. is printed as 'PWR.RP.4' in Appendix A."),
        ("WR.RP.5", "WR.RP.5", "Notify RevPart Reject", "CD_Revenue Partners Workflow", "Review Reject RevPart", None, None, "Stage Rule", "To notify the respective internal users of the rejection of the third-party", "Attribute: Vendor Category Contains: Revenue Partner", "Send Notification AND Create Task (Assignee: Business Owner, Collaborator: TPRM_Vendor Risk Management Team, Deadline: 14 Days)", None),
        ("WR.RP.6", "WR.RP.6", "Notify RevPart Approval", "CD_Revenue Partners Workflow", "Live", None, None, "Stage Rule", "To notify the respective internal users of the approval of the third-party", "Attribute: Vendor Category Contains: Revenue Partner", "Send Notification", None),
        # Tier 3
        ("WR.T3.1", "WR.T3.1", "T3_R_Push to Next", "CD_Tier3 Workflow", "Initiated", "T3_T_Push to Next", "Vendor Created", "Workflow Rule", "To push the third-party to the next stage in Tier 3 Workflow", "Attribute: Vendor Category Contains Any: ALL categories", "Advance to stage: Launching Tier3", None),
        ("WR.T3.2", "WR.T3.2", "Send Tier3 Questionnaire", "CD_Tier3 Workflow", "Launching Tier3", None, None, "Stage Rule", "To launch third-party due diligence assessment for the third-party", "Attribute: Vendor Tier Contains: Tier 3", "Launch Assessment: Due Diligence Questionnaire T3 v1 | Approver: TPRM_Vendor Risk Management Team | Respondent: Primary Vendor Contact", None),
        ("WR.T3.3", "WR.T3.3", "T3_R_Assessment Auto-approve", "CD_Tier3 Workflow", "Launching Tier3", "T3_T_Assessment Auto-approve", "Auto-approve", "Workflow Rule", "To move the third party to the next stage when the third-party is approved.", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T3 v1", "Advance to stage: Live", None),
        ("WR.T3.4", "WR.T3.4", "T3_R_Assessment Rejected", "CD_Tier3 Workflow", "Launching Tier3", "T3_T_Assessment Rejected", "Rejected", "Workflow Rule", "To move the rejected third-party to the Review Reject Tier 3 stage.", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T3 v1", "Advance to stage: Review Reject Tier3", None),
        ("WR.T3.5", "WR.T3.5", "Notify Tier3 Reject", "CD_Tier3 Workflow", "Review Reject Tier3", None, None, "Stage Rule", "To notify the respective internal users of the rejection of the third-party", "Attribute: Vendor Tier Contains: Tier 3", "Send Notification AND Create Task (Assignee: Business Owner, Collaborator: TPRM_Vendor Risk Management Team, Deadline: 14 Days)", None),
        ("WR.T3.6", "WR.T3.6", "Notify Tier3 Approval", "CD_Tier3 Workflow", "Live", None, None, "Stage Rule", "To notify the respective internal users of the approval of the third-party", "Attribute: Vendor Tier Contains: Tier 3", "Send Notification", None),
        # Automation Reassessment Rules
        ("AR.T1.1", "AR.T1.1", "Tier 1 Reassessment rule", "TPRM Reassessment Rules", "Live", "Daily Schedule", "Daily", "Vendor Automation Rule", "Send reassessments to Tier 1 third parties on an annual basis (90 days prior to 1 year = 275 days).", "Last Assessment Completion Date – By Template >= 275 Days (Due Diligence Questionnaire T1-2 v1) AND Attribute: Vendor Tier Contains any: Tier 1", "Send vendor assessment (Copy Previous Assessment = Yes, Template: Due Diligence Questionnaire T1-2 v1, Respondent: Primary Vendor Contact) AND Send vendor email 'Vendor Upcoming Re-Assessment' to Business Owners", None),
        ("AR.T2.1", "AR.T2.1", "Tier 2 Reassessment rule", "TPRM Reassessment Rules", "Live", "Daily Schedule", "Daily", "Vendor Automation Rule", "Send reassessments to Tier 2 third parties in a period of two years (90 days prior to 2 years = 640 days).", "Last Assessment Completion Date – By Template >= 640 Days (Due Diligence Questionnaire T1-2 v1) AND Attribute: Vendor Tier Contains any: Tier 2", "Send vendor assessment (Copy Previous Assessment = Yes, Template: Due Diligence Questionnaire T1-2 v1, Respondent: Primary Vendor Contact) AND Send vendor email 'Vendor Upcoming Re-Assessment' to Business Owners", None),
        ("AR.T3.1", "AR.T3.1", "Tier 3 Reassessment rule", "TPRM Reassessment Rules", "Live", "Daily Schedule", "Daily", "Vendor Automation Rule", "Send reassessments to Tier 3 third parties in a period of two years (90 days prior to 2 years = 640 days).", "Last Assessment Completion Date – By Template >= 640 Days (Due Diligence Questionnaire T3 v1) AND Attribute: Vendor Tier Contains any: Tier 3", "Send vendor assessment (Copy Previous Assessment = Yes, Template: Due Diligence Questionnaire T3 v1, Respondent: Primary Vendor Contact) AND Send vendor email 'Vendor Upcoming Re-Assessment' to Business Owners", None),
        # Marketing Partners
        ("WR.MP.1", "WR.MP.1", "MP_R_Push to Next", "CD_Marketing Partners Workflow", "Initiated", "MP_T_Push to Next", "Vendor Created", "Workflow Rule", "To push the third-party to the next stage in Marketing Partners Workflow", "Attribute: Vendor Category Contains Any: Marketing Partner AND Attribute: Vendor Tier Does not contain: Tier 3", "Advance to stage: Launching MarPart", None),
        ("WR.MP.2", "WR.MP.2", "Send MarPart Questionnaire", "CD_Marketing Partners Workflow", "Launching MarPart", None, None, "Stage Rule", "To launch third-party due diligence assessment for the third-party", "Attribute: Vendor Category Contains Any: Marketing Partner AND Attribute: Vendor Tier Does not contain: Tier 3", "Launch Assessment: Due Diligence Questionnaire T1-2 v1 | Approver: TPRM_Vendor Risk Management Team | Respondent: Primary Vendor Contact", None),
        ("WR.MP.3", "WR.MP.3", "MP_R_Assessment Approved", "CD_Marketing Partners Workflow", "Launching MarPart", "MP_T_Assessment Approved", "Approved", "Workflow Rule", "To move the third party to the next stage when the third-party is approved.", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1", "Advance to stage: Live", None),
        ("WR.MP.4", "WR.MP.4", "MP_R_Assessment Rejected", "CD_Marketing Partners Workflow", "Launching MarPart", "MP_T_Assessment Rejected", "Rejected", "Workflow Rule", "To move the rejected third-party to the appropriate stage Review Reject MarPart", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1", "Advance to stage: Review Reject MarPart", None),
        ("WR.MP.5", "WR.MP.5", "Notify MarPart Reject", "CD_Marketing Partners Workflow", "Review Reject MarPart", None, None, "Stage Rule", "To notify the respective internal users of the rejection of the third-party", "Attribute: Vendor Category Contains: Marketing Partner", "Send Notification AND Create Task (Assignee: Business Owner, Collaborator: TPRM_Vendor Risk Management Team, Deadline: 14 Days)", None),
        ("WR.MP.6", "WR.MP.6", "Notify MarPart Approval", "CD_Marketing Partners Workflow", "Live", None, None, "Stage Rule", "To notify the respective internal users of the approval of the third-party", "Attribute: Vendor Category Contains: Marketing Partner", "Send Notification", None),
        # International Vendors
        ("WR.IV.1", "WR.IV.1", "IV_R_Push to Next", "CD_International Vendors Workflow", "Initiated", "IV_T_Push to Next", "Vendor Created", "Workflow Rule", "To push the third-party to the next stage in International Vendors Workflow", "Attribute: Vendor Category Contains Any: International Vendors AND Attribute: Vendor Tier Does not contain: Tier 3", "Advance to stage: Launching IntVen", "Source condition uses plural 'International Vendors' while Table 9 uses 'International Vendor'; engine normalizes both."),
        ("WR.IV.2", "WR.IV.2", "Send IntVen Questionnaire", "CD_International Vendors Workflow", "Launching IntVen", None, None, "Stage Rule", "To launch third-party due diligence assessment for the third-party", "Attribute: Vendor Category Contains Any: International Vendors AND Attribute: Vendor Tier Does not contain: Tier 3", "Launch Assessment: Due Diligence Questionnaire T1-2 v1 | Approver: TPRM_Vendor Risk Management Team | Respondent: Primary Vendor Contact", None),
        ("WR.IV.3", "WR.IV.3", "IV_R_Assessment Approved", "CD_International Vendors Workflow", "Launching IntVen", "IV_T_Assessment Approved", "Approved", "Workflow Rule", "To move the third party to the next stage when the third-party is approved.", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1", "Advance to stage: Live", None),
        ("WR.IV.4", "WR.IV.4", "IV_R_Assessment Rejected", "CD_International Vendors Workflow", "Launching IntVen", "IV_T_Assessment Rejected", "Rejected", "Workflow Rule", "To move the rejected third-party to the appropriate stage Review Reject IntVen", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1", "Advance to stage: Review Reject IntVen", None),
        ("WR.IV.5", "WR.IV.5", "Notify IntVen Reject", "CD_International Vendors Workflow", "Review Reject IntVen", None, None, "Stage Rule", "To notify the respective internal users of the rejection of the third-party", "Attribute: Vendor Category Contains: International Vendors", "Send Notification AND Create Task (Assignee: Business Owner, Collaborator: TPRM_Vendor Risk Management Team, Deadline: 14 Days)", None),
        ("WR.IV.6", "WR.IV.6", "Notify IntVen Approval", "CD_International Vendors Workflow", "Live", None, None, "Stage Rule", "To notify the respective internal users of the approval of the third-party", "Attribute: Vendor Category Contains: International Vendors", "Send Notification", None),
        # Service Providers
        ("WR.SP.1", "WR.SP.1", "SP_R_Push to Next", "CD_Service Providers Workflow", "Initiated", "SP_T_Push to Next", "Vendor Created", "Workflow Rule", "To push the third-party to the next stage in Service Providers Workflow", "Attribute: Vendor Category Contains Any: Service Provider and Vendor AND Attribute: Vendor Tier Does not contain: Tier 3", "Advance to stage: Launching ServPro", None),
        ("WR.SP.2", "WR.SP.2", "Send ServPro Questionnaire", "CD_Service Providers Workflow", "Launching ServPro", None, None, "Stage Rule", "To launch third-party due diligence assessment for the third-party", "Attribute: Vendor Category Contains Any: Service Provider and Vendor AND Attribute: Vendor Tier Does not contain: Tier 3", "Launch Assessment: Due Diligence Questionnaire T1-2 v1 | Approver: TPRM_Vendor Risk Management Team | Respondent: Primary Vendor Contact", None),
        ("WR.SP.3", "WR.SP.3", "SP_R_Assessment Approved", "CD_Service Providers Workflow", "Launching ServPro", "SP_T_Assessment Approved", "Approved", "Workflow Rule", "To move the third party to the next stage when the third-party is approved.", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1", "Advance to stage: Live", None),
        ("WR.SP.4", "WR.SP.4", "SP_R_Assessment Rejected", "CD_Service Providers Workflow", "Launching ServPro", "SP_T_Assessment Rejected", "Rejected", "Workflow Rule", "To move the rejected third-party to the appropriate stage Review Reject ServPro", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1", "Advance to stage: Review Reject ServPro", None),
        ("WR.SP.5", "WR.SP.5", "Notify ServPro Reject", "CD_Service Providers Workflow", "Review Reject ServPro", None, None, "Stage Rule", "To notify the respective internal users of the rejection of the third-party", "Attribute: Vendor Category Contains: Service Provider and Vendor", "Send Notification AND Create Task (Assignee: Business Owner, Collaborator: TPRM_Vendor Risk Management Team, Deadline: 14 Days)", None),
        ("WR.SP.6", "WR.SP.6", "Notify ServPro Approval", "CD_Service Providers Workflow", "Live", None, None, "Stage Rule", "To notify the respective internal users of the approval of the third-party", "Attribute: Vendor Category Contains: Service Provider and Vendor", "Send Notification", None),
        # Staffing Vendors
        ("WR.SV.1", "WR.SV.1", "SV_R_Push to Next", "CD_Staffing Vendors Workflow", "Initiated", "SV_T_Push to Next", "Vendor Created", "Workflow Rule", "To push the third-party to the next stage in Staffing Vendors Workflow", "Attribute: Vendor Category Contains Any: Staffing Vendor AND Attribute: Vendor Tier Does not contain: Tier 3", "Advance to stage: Launching StafVen", None),
        ("WR.SV.2", "WR.SV.2", "Send StafVen Questionnaire", "CD_Staffing Vendors Workflow", "Launching StafVen", None, None, "Stage Rule", "To launch third-party due diligence assessment for the third-party", "Attribute: Vendor Category Contains Any: Staffing Vendor AND Attribute: Vendor Tier Does not contain: Tier 3", "Launch Assessment: Due Diligence Questionnaire T1-2 v1 | Approver: TPRM_Vendor Risk Management Team | Respondent: Primary Vendor Contact", None),
        ("WR.SV.3", "WR.SV.3", "SV_R_Assessment Approved", "CD_Staffing Vendors Workflow", "Launching StafVen", "SV_T_Assessment Approved", "Approved", "Workflow Rule", "To move the third party to the next stage when the third-party is approved.", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1 AND Attribute: Vendor Category Contains Any: Staffing Vendor", "Advance to stage: Live", None),
        ("WR.SV.4", "WR.SV.4", "SV_R_Assessment Rejected", "CD_Staffing Vendors Workflow", "Launching StafVen", "SV_T_Assessment Rejected", "Rejected", "Workflow Rule", "To move the rejected third-party to the appropriate stage Review Reject StafVen", "Assessment stage – By template: Completed AND Template name: Due Diligence Questionnaire T1-2 v1 AND Attribute: Vendor Category Contains Any: Staffing Vendor", "Advance to stage: Review Reject StafVen", None),
        ("WR.SV.5", "WR.SV.5", "Notify StafVen Reject", "CD_Staffing Vendors Workflow", "Review Reject StafVen", None, None, "Stage Rule", "To notify the respective internal users of the rejection of the third-party", "Attribute: Vendor Category Contains: Staffing Vendor", "Send Notification AND Create Task (Assignee: Business Owner, Collaborator: TPRM_Vendor Risk Management Team, Deadline: 14 Days)", None),
        ("WR.SV.6", "WR.SV.6", "Notify StafVen Approval", "CD_Staffing Vendors Workflow", "Live", None, None, "Stage Rule", "To notify the respective internal users of the approval of the third-party", "Attribute: Vendor Category Contains: Staffing Vendor", "Send Notification", None),
        # Onboarding Routing Rules
        ("WR.ON.1", "WR.ON.1", "On_R_Assign RevPart", "CD_Onboarding Workflow", "New Third Party", "On_T_Assign Workflow", "Vendor Created", "Workflow Rule", "To assign workflow for Revenue Partners.", "Attribute: Vendor Category Contains Any: Revenue Partner AND Attribute: Vendor Tier Contains Any: Tier 1, Tier 2", "Change Workflow: CD_Revenue Partners Workflow | Stage: Launching RevPart", None),
        ("WR.ON.2", "WR.ON.2", "On_R_Assign MarPart", "CD_Onboarding Workflow", "New Third Party", "On_T_Assign Workflow", "Vendor Created", "Workflow Rule", "To assign workflow for Marketing Partners.", "Attribute: Vendor Category Contains Any: Marketing Partner AND Attribute: Vendor Tier Contains Any: Tier 1, Tier 2", "Change Workflow: CD_Marketing Partners Workflow | Stage: Launching MarPart", None),
        ("WR.ON.3", "WR.ON.3", "On_R_Assign IntVen", "CD_Onboarding Workflow", "New Third Party", "On_T_Assign Workflow", "Vendor Created", "Workflow Rule", "To assign workflow for International Vendors.", "Attribute: Vendor Category Contains Any: International Vendor AND Attribute: Vendor Tier Contains Any: Tier 1, Tier 2", "Change Workflow: CD_International Vendors Workflow | Stage: Launching IntVen", None),
        ("WR.ON.4", "WR.ON.4", "On_R_Assign ServPro", "CD_Onboarding Workflow", "New Third Party", "On_T_Assign Workflow", "Vendor Created", "Workflow Rule", "To assign workflow for Service Providers and Vendors.", "Attribute: Vendor Category Contains Any: Service Provider and Vendor AND Attribute: Vendor Tier Contains Any: Tier 1, Tier 2", "Change Workflow: CD_Service Providers Workflow | Stage: Launching ServPro", None),
        ("WR.ON.5", "WR.ON.5", "On_R_Assign StafVen", "CD_Onboarding Workflow", "New Third Party", "On_T_Assign Workflow", "Vendor Created", "Workflow Rule", "To assign workflow for Staffing Vendors.", "Attribute: Vendor Category Contains Any: Staffing Vendor AND Attribute: Vendor Tier Contains Any: Tier 1, Tier 2", "Change Workflow: CD_Staffing Vendors Workflow | Stage: Launching StafVen", None),
        ("WR.ON.6", "WR.ON.6", "On_R_Assign Tier3", "CD_Onboarding Workflow", "New Third Party", "On_T_Assign Workflow", "Vendor Created", "Workflow Rule", "To assign workflow for Tier 3 Vendors.", "Attribute: Vendor Category Contains Any: All AND Attribute: Vendor Tier Contains Any: Tier 3", "Change Workflow: CD_Tier3 Workflow | Stage: Launching Tier3", None),
    ]
    for r_code, sr_no, r_name, wf_name, stg, trig, trig_type, r_type, desc, cond_expr, act_expr, disc in appendix_a_rules:
        if not db.query(WorkflowRuleSpec).filter_by(rule_code=r_code).first():
            db.add(WorkflowRuleSpec(
                rule_code=r_code,
                source_sr_no=sr_no,
                rule_name=r_name,
                workflow_name=wf_name,
                stage_name=stg,
                trigger_name=trig,
                trigger_type=trig_type,
                rule_type=r_type,
                description=desc,
                condition_expression=cond_expr,
                action_expression=act_expr,
                discrepancy_note=disc,
            ))
    db.flush()

    # 9. Appendix D SLAs (SLA.1 to SLA.7)
    slas_data = [
        ("SLA.1", "Assessment Completion", "When a new assessment is sent to the Primary Vendor Contact, it must be completed within the specified timeline.", 9, 9, 5),
        ("SLA.2", "Review Responses", "User Groups are responsible for reviewing the responses provided by the Primary Vendor Contact in the questionnaire and for analyzing any flagged risks.", 4, 4, 2),
        ("SLA.3", "High Risk Response", "The Primary Vendor Contact must provide a response within the defined timeframe to address a documented high risk. This stage is for acknowledging and analyzing the risk, it is not a remediation period. (Starts after 4-day Review Responses period: 5+4 = 9 days).", 5, 9, 3),
        ("SLA.4", "Medium Risk Response", "The Primary Vendor Contact must provide a response within the defined timeframe to address a documented medium risk. This stage is for acknowledging and analyzing the risk, it is not a remediation period. (Starts after 4-day Review Responses period: 10+4 = 14 days).", 10, 14, 7),
        ("SLA.5", "Low Risk Response", "The Primary Vendor Contact must provide a response within the defined timeframe to address a documented low risk. This stage is for acknowledging and analyzing the risk, it is not a remediation period. (Starts after 4-day Review Responses period: 15+4 = 19 days).", 15, 19, 10),
        ("SLA.6", "Renewal Process Initiation – Tier 1", "For Tier 1 third parties, the reassessment process begins 90 days prior to the completion of the one-year period. An assessment questionnaire is issued, and the results are used to inform renewal decisions.", 275, 275, None),
        ("SLA.7", "Renewal Process Initiation – Tier 2 and Tier 3", "For Tier 2 and Tier 3 third parties, the reassessment process begins 90 days prior to the completion of the two-year period. An assessment questionnaire is issued, and the results are used to inform renewal decisions.", 640, 640, None),
    ]
    for sla_no, s_name, s_desc, t_days, eff_days, rem_days in slas_data:
        if not db.query(SLAConfig).filter_by(sla_no=sla_no).first():
            db.add(SLAConfig(
                sla_no=sla_no,
                sla_name=s_name,
                description=s_desc,
                timeline_days=t_days,
                effective_deadline_days=eff_days,
                reminder_days=rem_days,
            ))
    db.flush()

    # 10. Questionnaire Templates & Sections (Appendix B, Section 6.3)
    # 10.1 Due Diligence Questionnaire T1-2 v1 (Q.1)
    t1_2 = db.query(QuestionnaireTemplate).filter_by(code="T1-2_v1").first()
    if not t1_2:
        t1_2 = QuestionnaireTemplate(
            questionnaire_no="Q.1",
            code="T1-2_v1",
            name="Due Diligence Questionnaire T1-2 v1",
            description="General security and operational due diligence questionnaire sent to Tier 1 and Tier 2 third parties across all 5 category workflows.",
            template_language="English",
            template_icon="archive",
            source_file_name="Final Due Diligence Questionnaire v1.0",
            approver_group="Vendor Risk Management Group",
            version=1,
            status="Published",
            is_published=True
        )
        db.add(t1_2)
        db.flush()

        # Tuple format: (q_code, prompt, q_type, options, favorable_answer, is_conditional)
        sections_t1_2 = [
            (1, "Contracting and Legal", "Legal Group", [
                ("1.1", "Full legal name of your company and its Primary Place of Business", "Text", None, None, False),
                ("1.2", "Please list any 'Doing Business As' (DBA) names and registration jurisdiction", "Text", None, None, False),
                ("1.3", "Is your company registered in US?", "YesNo", ["Yes", "No"], "Yes", False),
                ("1.4", "Specify entity type (e.g., LLC, Corporation).", "Text", None, None, False),
                ("1.5", "Is your organization incorporated?", "YesNo", ["Yes", "No"], "Yes", False),
                ("1.6", "Please provide the following: State of Incorporation, Principal Place of Business, Parent Company / Affiliates, Ownership/investment by foreign governments?", "Text", None, None, True),
                ("1.7", "Please provide the date of incorporation.", "Date", None, None, True),
                ("1.8", "How long has your company been in business?", "SingleChoice", ["0-5", "5-10", "10+"], "10+", True),
                ("1.9", "Do you operate through subsidiaries or affiliates for this engagement?", "YesNo", ["Yes", "No"], "No", False),
                ("1.10", "Has the company been involved in material litigation in the past 3 years?", "YesNo", ["Yes", "No"], "No", False),
                ("1.11", "Has the organization undergone any recent Mergers & Acquisitions (M&A) in the past 24 months?", "YesNo", ["Yes", "No"], "No", False),
            ]),
            (2, "Compliance and Legal", "Compliance Group", [
                ("2.1", "Does the organization maintain a formal Code of Business Conduct and Ethics?", "YesNo", ["Yes", "No"], "Yes", False),
                ("2.2", "Does your company produce independent annual compliance reports?", "YesNo", ["Yes", "No"], "Yes", False),
                ("2.3", "Does your jurisdiction enforce strong data protection and regulatory compliance laws?", "YesNo", ["Yes", "No"], "Yes", False),
                ("2.4", "Does your organization have a documented policy for handling consumer complaints?", "YesNo", ["Yes", "No"], "Yes", False),
                ("2.5", "Please provide a copy of your policy for handling consumer complaints.", "Text", None, None, True),
                ("2.6", "Is your organization subject to statutory Anti-Money Laundering (AML) requirements?", "YesNo", ["Yes", "No"], "No", False),
                ("2.7", "Does your organization conduct independent AML audits?", "YesNo", ["Yes", "No"], "Yes", False),
            ]),
            (3, "Finance", "Finance Group", [
                ("3.1", "Primary financial institution and banking relationship details", "Text", None, None, False),
                ("3.2", "Fiscal year end date and annual operating revenue bracket", "SingleChoice", ["<$5M", "$5M-$50M", "$50M-$250M", ">$250M"], None, False),
                ("3.3", "Can your company provide audited financial statements for the most recent fiscal years?", "YesNo", ["Yes", "No"], "Yes", False),
                ("3.4", "Has the company filed for bankruptcy or debt restructuring within the past 5 years?", "YesNo", ["Yes", "No"], "No", False),
                ("3.5", "Does your company undergo independent financial audits by a certified public accounting firm?", "YesNo", ["Yes", "No"], "Yes", False),
                ("3.6", "Has your organization completed the Oracle Vendor Onboarding registration?", "YesNo", ["Yes", "No"], "Yes", False),
                ("3.7", "If no, please complete the form here: Oracle Vendor Onboarding Form (link). Please provide the confirmation or upload evidence once completed.", "Text", None, None, True),
            ]),
            (4, "Data Privacy and Security", "Security Group", [
                ("4.1", "Will Cadence customer data be stored, accessed, or processed outside the United States?", "YesNo", ["Yes", "No"], "No", False),
                ("4.2", "Does your organization conduct operations in geopolitically high-risk regions?", "YesNo", ["Yes", "No"], "No", False),
                ("4.3", "Does your service process protected health or financial account records?", "YesNo", ["Yes", "No"], "No", False),
                ("4.4", "As part of this engagement with Cadence will your company collect, process, store, or transmit Cadence personal data? If Yes, explain the type of data you will process and how risks are managed.", "YesNo", ["Yes", "No"], "No", False),
                ("4.5", "Select Cadence data subjects", "SingleChoice", ["Customers", "Employees", "Contractors", "Prospective Employees", "Other"], None, True),
                ("4.6", "Describe (Select) personal data categories.", "Text", None, None, True),
                ("4.7", "Which transfer safeguards apply between your entity and Cadence?", "Text", None, None, False),
                ("4.8", "Will any sub-processors be used to deliver services or process Cadence data?", "YesNo", ["Yes", "No"], "No", False),
                ("4.9", "As part of this engagement, will you provide Cadence services via cloud infrastructure?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.10", "Do you provide AI or LLM-based services for this engagement?", "YesNo", ["Yes", "No"], "No", False),
                ("4.11", "Will the AI a) interact with Cadence customers, b) have access to customer data (PI), or sensitive employee information (i.e., race, gender, religion, etc.). Please describe in detail.", "YesNo", ["Yes", "No"], "No", True),
                ("4.12", "Does the organization use AI or large language models in data processing?", "YesNo", ["Yes", "No"], "No", True),
                ("4.13", "Are there processes established for managing risks related to Artificial Intelligence? If Yes, describe in detail.", "YesNo", ["Yes", "No"], "Yes", True),
                ("4.14", "Do you have a documented Privacy Policy? If Yes, please attach or provide link.", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.15", "Do you have identity and access management (IAM) policies in place?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.16", "Do you enforce least privilege access controls across systems and data?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.17", "Do you enforce a formal password policy (complexity, rotation, length)?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.18", "Is Multi-Factor Authentication (MFA) required for all internal and remote access?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.19", "If No - Please explain why MFA is not required (e.g., compensating controls, acceptable risk)", "Text", None, None, True),
                ("4.20", "Do employees have remote access to your corporate network or production environments?", "YesNo", ["Yes", "No"], "No", False),
                ("4.21", "If Yes - (a) How is VPN secured? (b) Is access control based on user role or uniform for all users?", "Text", None, None, True),
                ("4.22", "Is your corporate and production network continuously monitored 24/7?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.23", "Do you use automated tools for regular vulnerability scanning?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.24", "Are customer systems and multi-tenant environments segregated?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.25", "If Yes - Please describe separation method (Logical, Physical, VLAN, Cloud tenant separation, Other)", "Text", None, None, True),
                ("4.26", "Do you conduct regular independent penetration testing (at least annually)?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.27", "Do you have a process for remediating critical and high-risk findings from penetration tests, including your defined timelines for remediation and how you communicate updates to clients?", "YesNo", ["Yes", "No"], "Yes", True),
                ("4.28", "Do you maintain a documented Secure Application Development (S-SDLC) policy?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.29", "Do you have a documented and tested Incident Response Plan?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.30", "Has your organization experienced any security incident or data breach in the last 24 months?", "YesNo", ["Yes", "No"], "No", False),
                ("4.31", "If Yes - Please describe: (a) Incident type (Data breach, Ransomware, Unauthorized Access, Other) (b) Remediation actions (c) Timeline (d) Any residual risk or findings post remediation.", "Text", None, None, True),
                ("4.32", "Do you have a formal breach notification process?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.33", "Do you commit to notifying Cadence within contractual SLA timeframes of any security incident?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.34", "Is encryption used for data at rest and data in transit?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.35", "How do you manage and store encryption keys? (e.g., access restrictions, storage method)", "Text", None, None, True),
                ("4.36", "Do you have Data Loss Prevention (DLP) controls deployed?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.37", "If Yes - Indicate scope of DLP (End-user devices, Email, File storage, Database, Cloud apps, Other).", "Text", None, None, True),
                ("4.38", "Do you maintain a documented Data Retention and Disposal Policy?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.39", "Do you have a formal Information Security Policy approved by management?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.40", "Do you have an established Risk Management program for Information Security?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.41", "Do all employees complete annual information security and privacy training?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.42", "Do you conduct pre-employment background checks for all employees?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.43", "Are physical security controls enforced at all data centers and offices?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.44", "Do you have a formal employee offboarding and access revocation process?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.45", "Is Bring Your Own Device (BYOD) allowed for accessing corporate systems or data?", "YesNo", ["Yes", "No"], "No", False),
                ("4.46", "Do you enforce a Mobile Device Management (MDM) policy?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.47", "Are endpoint protection and anti-malware tools deployed on all workstations?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.48", "Is secure data deletion supported upon contract termination or request?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.49", "Does your organization hold active security certifications (SOC 2, ISO 27001, PCI)?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.50", "Does your organization maintain Cyber Liability Insurance?", "YesNo", ["Yes", "No"], "Yes", False),
            ]),
            (5, "IT Systems and Integration", "IT Group", [
                ("5.1", "Does the engagement require IT system integration or network connectivity with Cadence?", "YesNo", ["Yes", "No"], "No", False),
                ("5.2", "Describe the integration architecture, APIs, and data flows", "Text", None, None, False),
                ("5.3", "Does your platform provide a dedicated staging / sandbox environment?", "YesNo", ["Yes", "No"], "Yes", False),
                ("5.4", "Are API credentials and secrets rotated periodically?", "YesNo", ["Yes", "No"], "Yes", False),
                ("5.5", "Does your platform support enterprise Single Sign-On (SAML 2.0 / OIDC)?", "YesNo", ["Yes", "No"], "Yes", False),
                ("5.6", "Does your application support SSO and SCIM automated user provisioning?", "YesNo", ["Yes", "No"], "Yes", False),
            ]),
            (6, "Marketing Use or Brand", "Legal Group", [
                ("6.1", "Will sensitive customer targeting data or behavioral segments be used?", "YesNo", ["Yes", "No"], "No", False),
                ("6.2", "Does the engagement involve publicity rights or use of Cadence brand assets?", "YesNo", ["Yes", "No"], "No", False),
                ("6.3", "Are co-branding disclosures and brand guidelines contractually enforced?", "YesNo", ["Yes", "No"], "Yes", False),
            ]),
            (7, "Procurement Process", "Procurement Group", [
                ("7.1", "Is the organization a certified diverse supplier?", "YesNo", ["Yes", "No"], "Yes", False),
                ("7.2", "Do you maintain a formal non-solicitation / employee poaching policy?", "YesNo", ["Yes", "No"], "Yes", False),
                ("7.3", "Does your organization maintain an Environmental, Social, and Governance (ESG) policy?", "YesNo", ["Yes", "No"], "Yes", False),
            ]),
            (8, "Resiliency and Continuity", "Compliance Group", [
                ("8.1", "Are SLA and KPI performance commitments included in the contract?", "YesNo", ["Yes", "No"], "Yes", False),
                ("8.2", "What KPIs or SLAs are linked to this engagement? Please provide details.", "Text", None, None, True),
                ("8.3", "Does your organization maintain a documented Business Continuity Plan (BCP)?", "YesNo", ["Yes", "No"], "Yes", False),
                ("8.4", "Does your organization maintain a documented Disaster Recovery Plan (DRP)?", "YesNo", ["Yes", "No"], "Yes", False),
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

            for idx, (q_code, q_prompt, q_type, q_opts, fav, is_cond) in enumerate(questions, start=1):
                db.add(Question(
                    section_id=sec.id,
                    question_code=q_code,
                    prompt=q_prompt,
                    question_type=q_type,
                    options=q_opts,
                    favorable_answer=fav,
                    is_required=True,
                    is_conditional=is_cond,
                    order_index=idx
                ))
        db.flush()

    # 10.2 Due Diligence Questionnaire T3 v1 (Q.2)
    t3 = db.query(QuestionnaireTemplate).filter_by(code="T3_v1").first()
    if not t3:
        t3 = QuestionnaireTemplate(
            questionnaire_no="Q.2",
            code="T3_v1",
            name="Due Diligence Questionnaire T3 v1",
            description="Specific simplified due diligence questionnaire sent to all third parties whose Vendor Tier attribute is selected as Tier 3.",
            template_language="English",
            template_icon="gavel",
            source_file_name="Final Due Diligence Questionnaire v1.0",
            approver_group="Vendor Risk Management Group",
            version=1,
            status="Published",
            is_published=True
        )
        db.add(t3)
        db.flush()

        sections_t3 = [
            (1, "Contracting and Legal", "Legal Group", [
                ("1.1", "Full legal name of your company and Website URL", "Text", None, None, False),
                ("1.2", "Is your company registered in the United States?", "YesNo", ["Yes", "No"], "Yes", False),
            ]),
            (2, "Compliance and Legal", "Compliance Group", [
                ("2.1", "Does the organization maintain a formal Code of Business Conduct?", "YesNo", ["Yes", "No"], "Yes", False),
                ("2.2", "Is your organization subject to statutory Anti-Money Laundering (AML) requirements?", "YesNo", ["Yes", "No"], "No", False),
            ]),
            (3, "Finance", "Finance Group", [
                ("3.1", "Primary financial institution and billing contact", "Text", None, None, False),
                ("3.2", "Annual operating revenue range", "SingleChoice", ["<$1M", "$1M-$10M", ">$10M"], None, False),
                ("3.3", "Does your company undergo independent financial audits?", "YesNo", ["Yes", "No"], "Yes", False),
                ("3.4", "Has your company completed the Oracle Vendor Onboarding registration?", "YesNo", ["Yes", "No"], "Yes", False),
                ("3.5", "If No, please complete the form here: Oracle Vendor Onboarding Form (link). Please provide the confirmation or upload evidence once completed.", "Text", None, None, True),
            ]),
            (4, "Data Privacy and Security", "Security Group", [
                ("4.1", "Do you have a documented Privacy Policy?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.2", "Do you have a documented Information Security Policy?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.3", "Do you have an established Risk Management program for Information Security?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.4", "Is encryption used for data at rest and in transit?", "YesNo", ["Yes", "No"], "Yes", False),
                ("4.5", "Does your organization maintain Cyber Liability Insurance?", "YesNo", ["Yes", "No"], "Yes", False),
            ]),
            (5, "IT Systems and Incident Notification", "IT Group", [
                ("5.1", "Does the engagement require direct IT system integration with Cadence?", "YesNo", ["Yes", "No"], "No", False),
                ("5.2", "Will Cadence be notified promptly in the event of a security breach or incident?", "YesNo", ["Yes", "No"], "Yes", False),
            ]),
            (6, "Business Continuity and Disaster Recovery", "Security Group", [
                ("6.1", "Does your organization maintain a documented Business Continuity Plan (BCP)?", "YesNo", ["Yes", "No"], "Yes", False),
                ("6.2", "Does your organization maintain a documented Disaster Recovery Plan (DRP)?", "YesNo", ["Yes", "No"], "Yes", False),
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

            for idx, (q_code, q_prompt, q_type, q_opts, fav, is_cond) in enumerate(questions, start=1):
                db.add(Question(
                    section_id=sec.id,
                    question_code=q_code,
                    prompt=q_prompt,
                    question_type=q_type,
                    options=q_opts,
                    favorable_answer=fav,
                    is_required=True,
                    is_conditional=is_cond,
                    order_index=idx
                ))
        db.flush()

    # 11. Conditional Show Logic (Appendix C: CL.1 to CL.14)
    cond_rules_data = [
        ("CL.1", "T1-2_v1", "Contracting and Legal", "1.5", "Equal To", "Yes", "1.6", ["1.7", "1.8"], ["1.6", "1.7", "1.8"], "1.6 Please provide the following: State of Incorporation, Principal Place of Business, Parent Company / Affiliates, Ownership/investment by foreign governments? 1.7 Please provide the date of incorporation. 1.8 How long has your company been in business?"),
        ("CL.2", "T1-2_v1", "Compliance and Legal", "2.4", "Equal To", "Yes", "2.5", [], ["2.5"], "2.5 Please provide a copy of your policy for handling consumer complaints."),
        ("CL.3", "T1-2_v1", "Finance", "3.6", "Equal To", "No", "3.7", [], ["3.7"], "3.7 If no, please complete the form here: Oracle Vendor Onboarding Form (link). Please provide the confirmation or upload evidence once completed."),
        ("CL.4", "T1-2_v1", "Data Privacy and Security", "4.4", "Equal To", "Yes", "4.5", ["4.6"], ["4.5", "4.6"], "4.5 Select Cadence data subjects. 4.6 Describe (Select) personal data categories."),
        ("CL.5", "T1-2_v1", "Data Privacy and Security", "4.10", "Equal To", "Yes", "4.11", ["4.12", "4.13"], ["4.11", "4.12", "4.13"], "4.11 Will the AI a) interact with Cadence customers, b) have access to customer data (PI), or sensitive employee information. 4.12 Does the organization use AI or large language models in data processing? 4.13 Are there processes established for managing risks related to Artificial Intelligence?"),
        ("CL.6", "T1-2_v1", "Data Privacy and Security", "4.18", "Equal To", "No", "4.19", [], ["4.19"], "4.19 If No - Please explain why MFA is not required (e.g., compensating controls, acceptable risk)"),
        ("CL.7", "T1-2_v1", "Data Privacy and Security", "4.20", "Equal To", "Yes", "4.21", [], ["4.21"], "4.21 If Yes - (a) How is VPN secured? (b) Is access control based on user role or uniform for all users?"),
        ("CL.8", "T1-2_v1", "Data Privacy and Security", "4.24", "Equal To", "Yes", "4.25", [], ["4.25"], "4.25 If Yes - Please describe separation method (Logical, Physical, VLAN, Cloud tenant separation, Other)"),
        ("CL.9", "T1-2_v1", "Data Privacy and Security", "4.26", "Equal To", "Yes", "4.27", [], ["4.27"], "4.27 Do you have a process for remediating critical and high-risk findings from penetration tests, including your defined timelines for remediation and how you communicate updates to clients?"),
        ("CL.10", "T1-2_v1", "Data Privacy and Security", "4.30", "Equal To", "Yes", "4.31", [], ["4.31"], "4.31 If Yes - Please describe: (a) Incident type (b) Remediation actions (c) Timeline (d) Any residual risk or findings post remediation."),
        ("CL.11", "T1-2_v1", "Data Privacy and Security", "4.34", "Equal To", "Yes", "4.35", [], ["4.35"], "4.35 How do you manage and store encryption keys? (e.g., access restrictions, storage method)"),
        ("CL.12", "T1-2_v1", "Data Privacy and Security", "4.36", "Equal To", "Yes", "4.37", [], ["4.37"], "4.37 If Yes - Indicate scope of DLP (End-user devices, Email, File storage, Database, Cloud apps, Other)."),
        ("CL.13", "T1-2_v1", "Data Privacy and Security [Section 8 Resiliency]", "8.1", "Equal To", "Yes", "8.2", [], ["8.2"], "8.2 What KPIs or SLAs are linked to this engagement? Please provide details. (Note: Appendix C table lists Section as 'Data Privacy and Security' for Question 8.1)."),
        ("CL.14", "T3_v1", "Finance", "3.4", "Equal To", "No", "3.5", [], ["3.5"], "3.5 If No, please complete the form here: Oracle Vendor Onboarding Form (link). Please provide the confirmation or upload evidence once completed."),
    ]
    for r_code, t_code, sec_name, q_trigger, op, resp, prim_shown, copy_to, shown, desc in cond_rules_data:
        if not db.query(ConditionalRule).filter_by(rule_code=r_code).first():
            db.add(ConditionalRule(
                rule_code=r_code,
                template_code=t_code,
                section_name=sec_name,
                condition_logic="IF: Any",
                trigger_question_code=q_trigger,
                trigger_operator=op,
                trigger_response=resp,
                primary_shown_question=prim_shown,
                copy_logic_to_questions=copy_to,
                shown_question_codes=shown,
                description=desc
            ))
    db.flush()

    # 12. Complete 90 Appendix E Questionnaire Rules (QR.1 to QR.90)
    # Format: (rule_code, template_code, rule_name, cond_logic, trig_type, trig_q, op, resp, action_type, risk_name, inherent_risk, control_id, control_name, task_name, assignee, collab_group, resp_group, result_status, result_comments, notes)
    risk_rules_data = [
        # QR.1 to QR.55: T1-2 Risk Creation Rules
        ("QR.1", "T1-2_v1", "QR_Non US Company", "IF: Any", "Question", "1.3", "Equal To", "No", "Create risk", "QRN_Non US Company", "High", "QRC_CL_1.1", "QRC_Non US Company", None, None, None, "Legal Group", None, None, None),
        ("QR.2", "T1-2_v1", "QR_Business duration_less", "IF: Any", "Question", "1.8", "Equal To", "0-5", "Create risk", "QRN_Business duration_less", "High", "QRC_CL_1.2", "QRC_ Business duration_less", None, None, None, "Legal Group", None, None, None),
        ("QR.3", "T1-2_v1", "QR_Business duration_medium", "IF: Any", "Question", "1.8", "Equal To", "5-10", "Create risk", "QRN_Business duration_medium", "Medium", "QRC_CL_1.3", "QRC_ Business duration_medium", None, None, None, "Legal Group", None, None, None),
        ("QR.4", "T1-2_v1", "QR_Subsidiaries and Affiliates", "IF: Any", "Question", "1.9", "Equal To", "Yes", "Create risk", "QRN_Subsidiaries and Affiliates", "Medium", "QRC_CL_1.4", "QRC_Subsidiaries and Affiliates", None, None, None, "Legal Group", None, None, None),
        ("QR.5", "T1-2_v1", "QR_Recent M and A", "IF: Any", "Question", "1.11", "Equal To", "Yes", "Create risk", "QRN_Recent M and A", "Medium", "QRC_CL_1.5", "QRC_Recent M and A", None, None, None, "Legal Group", None, None, None),
        ("QR.6", "T1-2_v1", "QR_No Compliance Report", "IF: Any", "Question", "2.2", "Equal To", "No", "Create risk", "QRN_No Compliance Report", "High", "QRC_CmL_2.1", "QRC_No Compliance Report", None, None, None, "Compliance Group", None, None, None),
        ("QR.7", "T1-2_v1", "QR_No Strong Laws", "IF: Any", "Question", "2.3", "Equal To", "No", "Create risk", "QRN_No Strong Laws", "Medium", "QRC_CmL_2.2", "QRC_No Strong Laws", None, None, None, "Compliance Group", None, None, None),
        ("QR.8", "T1-2_v1", "QR_AML Requirement", "IF: Any", "Question", "2.6", "Equal To", "Yes", "Create risk", "QRN_AML Requirement", "Medium", "QRC_CmL_2.3", "QRC_AML Requirement", None, None, None, "Compliance Group", None, None, None),
        ("QR.9", "T1-2_v1", "QR_No AML Audit", "IF: Any", "Question", "2.7", "Equal To", "No", "Create risk", "QRN_No AML Audit", "Medium", "QRC_CmL_2.4", "QRC_No AML Audit", None, None, None, "Compliance Group", None, None, None),
        ("QR.10", "T1-2_v1", "QR_No Financial Statement", "IF: Any", "Question", "3.3", "Equal To", "No", "Create risk", "QRN_No Financial Statement", "High", "QRC_Fin_3.1", "QRC_No Financial Statement", None, None, None, "Finance Group", None, None, None),
        ("QR.11", "T1-2_v1", "QR_No Financial Audits", "IF: Any", "Question", "3.5", "Equal To", "No", "Create risk", "QRN_No Financial Audits", "High", "QRC_Fin_3.2", "QRC_No Financial Audits", None, None, None, "Finance Group", None, None, None),
        ("QR.12", "T1-2_v1", "QR_Cust_Data Outside US", "IF: Any", "Question", "4.1", "Equal To", "Yes", "Create risk", "QRN_Cust_Data Outside US", "High", "QRC_Pri_4.1", "QRC_Cust_Data Outside US", None, None, None, "Privacy Group", None, None, None),
        ("QR.13", "T1-2_v1", "QR_Operations_Risk Regions", "IF: Any", "Question", "4.2", "Equal To", "Yes", "Create risk", "QRN_Operations_Risk Regions", "High", "QRC_Pri_4.2", "QRC_Operations_Risk Regions", None, None, None, "Privacy Group", None, None, None),
        ("QR.14", "T1-2_v1", "QR_Personal Data Collected", "IF: Any", "Question", "4.4", "Equal To", "Yes", "Create risk", "QRN_Personal Data Collected", "Medium", "QRC_Pri_4.3", "QRC_Personal Data Collected", None, None, None, "Privacy Group", None, None, None),
        ("QR.15", "T1-2_v1", "QR_Sub-processor Used", "IF: Any", "Question", "4.8", "Equal To", "Yes", "Create risk", "QRN_Sub-processor Used", "Medium", "QRC_Pri_4.4", "QRC_Sub-processor Used", None, None, None, "Privacy Group", None, None, None),
        ("QR.16", "T1-2_v1", "QR_AI Interaction with Data", "IF: Any", "Question", "4.11", "Equal To", "Yes", "Create risk", "QRN_AI Interaction with Data", "Medium", "QRC_Pri_4.5", "QRC_AI Interaction with Data", None, None, None, "Privacy Group", None, None, None),
        ("QR.17", "T1-2_v1", "QR_LLM Use in Data Processing", "IF: Any", "Question", "4.12", "Equal To", "Yes", "Create risk", "QRN_LLM Use in Data Processing", "Medium", "QRC_Pri_4.6", "QRC_LLM Use in Data Processing", None, None, None, "Privacy Group", None, None, None),
        ("QR.18", "T1-2_v1", "QR_No RM for AI", "IF: Any", "Question", "4.13", "Equal To", "No", "Create risk", "QRN_No RM for AI", "Medium", "QRC_Pri_4.7", "QRC_No RM for AI", None, None, None, "Privacy Group", None, None, None),
        ("QR.19", "T1-2_v1", "QR_No Privacy Policy", "IF: Any", "Question", "4.14", "Equal To", "No", "Create risk", "QRN_No Privacy Policy", "High", "QRC_Pri_4.8", "QRC_No Privacy Policy", None, None, None, "Privacy Group", None, None, None),
        ("QR.20", "T1-2_v1", "QR_No IAM Policy", "IF: Any", "Question", "4.15", "Equal To", "No", "Create risk", "QRN_No IAM Policy", "High", "QRC_Sec_4.9", "QRC_No IAM Policy", None, None, None, "Security Group", None, None, None),
        ("QR.21", "T1-2_v1", "QR_No Least Privilege Access", "IF: Any", "Question", "4.16", "Equal To", "No", "Create risk", "QRN_No Least Privilege Access", "Medium", "QRC_Sec_4.10", "QRC_No Least Privilege Access", None, None, None, "Security Group", None, None, None),
        ("QR.22", "T1-2_v1", "QR_No Password Policy", "IF: Any", "Question", "4.17", "Equal To", "No", "Create risk", "QRN_No Password Policy", "Medium", "QRC_Sec_4.11", "QRC_No Password Policy", None, None, None, "Security Group", None, None, None),
        ("QR.23", "T1-2_v1", "QR_No MFA", "IF: Any", "Question", "4.18", "Equal To", "No", "Create risk", "QRN_No MFA", "Medium", "QRC_Sec_4.12", "QRC_No MFA", None, None, None, "Security Group", None, None, None),
        ("QR.24", "T1-2_v1", "QR_Employee Remote Access", "IF: Any", "Question", "4.20", "Equal To", "Yes", "Create risk", "QRN_Employee Remote Access", "Medium", "QRC_Sec_4.13", "QRC_Employee Remote Access", None, None, None, "Security Group", None, None, None),
        ("QR.25", "T1-2_v1", "QR_Network Not Monitored", "IF: Any", "Question", "4.22", "Equal To", "No", "Create risk", "QRN_Network Not Monitored", "High", "QRC_Sec_4.14", "QRC_Network Not Monitored", None, None, None, "Security Group", None, None, None),
        ("QR.26", "T1-2_v1", "QR_No Tools for Vulnerability Scan", "IF: Any", "Question", "4.23", "Equal To", "No", "Create risk", "QRN_No Tools for Vulnerability Scan", "Medium", "QRC_Sec_4.15", "QRC_No Tools for Vulnerability Scan", None, None, None, "Security Group", None, None, None),
        ("QR.27", "T1-2_v1", "QR_System Not Segrated", "IF: Any", "Question", "4.24", "Equal To", "No", "Create risk", "QRN_System Not Segrated", "Medium", "QRC_Sec_4.16", "QRC_System Not Segrated", None, None, None, "Security Group", None, None, "Preserves exact Appendix E spelling 'Segrated'."),
        ("QR.28", "T1-2_v1", "QR_No Pen Test", "IF: Any", "Question", "4.26", "Equal To", "No", "Create risk", "QRN_No Pen Test", "High", "QRC_Sec_4.17", "QRC_No Pen Test", None, None, None, "Security Group", None, None, None),
        ("QR.29", "T1-2_v1", "QR_No Remediation for Findings", "IF: Any", "Question", "4.27", "Equal To", "No", "Create risk", "QRN_No Remediation for Findings", "Medium", "QRC_Sec_4.18", "QRC_No Remediation for Findings", None, None, None, "Security Group", None, None, None),
        ("QR.30", "T1-2_v1", "QR_No Security App Dev Policy", "IF: Any", "Question", "4.28", "Equal To", "No", "Create risk", "QRN_No Security App Dev Policy", "Medium", "QRC_Sec_4.19", "QRC_No Security App Dev Policy", None, None, None, "Security Group", None, None, None),
        ("QR.31", "T1-2_v1", "QR_No Incident Response Plan", "IF: Any", "Question", "4.29", "Equal To", "No", "Create risk", "QRN_No Incident Response Plan", "High", "QRC_Sec_4.20", "QRC_No Incident Response Plan", None, None, None, "Security Group", None, None, None),
        ("QR.32", "T1-2_v1", "QR_24 Mon Security Incident", "IF: Any", "Question", "4.30", "Equal To", "Yes", "Create risk", "QRN_24 Mon Security Incident", "High", "QRC_Sec_4.21", "QRC_24 Mon Security Incident", None, None, None, "Security Group", None, None, None),
        ("QR.33", "T1-2_v1", "QR_No Breach Notification Process", "IF: Any", "Question", "4.32", "Equal To", "No", "Create risk", "QRN_No Breach Notification Process", "High", "QRC_Sec_4.22", "QRC_No Breach Notification Process", None, None, None, "Security Group", None, None, None),
        ("QR.34", "T1-2_v1", "QR_No Notification to Cadence", "IF: Any", "Question", "4.33", "Equal To", "No", "Create risk", "QRN_No Notification to Cadence", "High", "QRC_Sec_4.23", "QRC_No Notification to Cadence", None, None, None, "Security Group", None, None, None),
        ("QR.35", "T1-2_v1", "QR_No Encryption Used", "IF: Any", "Question", "4.34", "Equal To", "No", "Create risk", "QRN_No Encryption Used", "High", "QRC_Sec_4.24", "QRC_No Encryption Used", None, None, None, "Security Group", None, None, None),
        ("QR.36", "T1-2_v1", "QR_No Data Loss Prevention", "IF: Any", "Question", "4.36", "Equal To", "No", "Create risk", "QRN_No Data Loss Prevention", "Medium", "QRC_Sec_4.25", "QRC_No Data Loss Prevention", None, None, None, "Security Group", None, None, None),
        ("QR.37", "T1-2_v1", "QR_No Data Retention Policy", "IF: Any", "Question", "4.38", "Equal To", "No", "Create risk", "QRN_No Data Retention Policy", "Medium", "QRC_Sec_4.26", "QRC_No Data Retention Policy", None, None, None, "Security Group", None, None, None),
        ("QR.38", "T1-2_v1", "QR_No Information Security Policy", "IF: Any", "Question", "4.39", "Equal To", "No", "Create risk", "QRN_No Information Security Policy", "High", "QRC_Sec_4.27", "QRC_No Information Security Policy", None, None, None, "Security Group", None, None, None),
        ("QR.39", "T1-2_v1", "QR_No RM for Information Security", "IF: Any", "Question", "4.40", "Equal To", "No", "Create risk", "QRN_No RM for Information Security", "High", "QRC_Sec_4.28", "QRC_No RM for Information Security", None, None, None, "Security Group", None, None, None),
        ("QR.40", "T1-2_v1", "QR_No Background checks for Emp", "IF: Any", "Question", "4.42", "Equal To", "No", "Create risk", "QRN_No Background checks for Emp", "Medium", "QRC_Sec_4.29", "QRC_No Background checks for Emp", None, None, None, "Security Group", None, None, None),
        ("QR.41", "T1-2_v1", "QR_No Offboarding Process", "IF: Any", "Question", "4.44", "Equal To", "No", "Create risk", "QRN_No Offboarding Process", "Medium", "QRC_Sec_4.30", "QRC_No Offboarding Process", None, None, None, "Security Group", None, None, None),
        ("QR.42", "T1-2_v1", "QR_BYOD Allowed", "IF: Any", "Question", "4.45", "Equal To", "Yes", "Create risk", "QRN_BYOD Allowed", "Medium", "QRC_Sec_4.31", "QRC_BYOD Allowed", None, None, None, "Security Group", None, None, None),
        ("QR.43", "T1-2_v1", "QR_No MDM Policy", "IF: Any", "Question", "4.46", "Equal To", "No", "Create risk", "QRN_No MDM Policy", "Medium", "QRC_Sec_4.32", "QRC_No MDM Policy", None, None, None, "Security Group", None, None, None),
        ("QR.44", "T1-2_v1", "QR_No Data Deletion Supported", "IF: Any", "Question", "4.48", "Equal To", "No", "Create risk", "QRN_No Data Deletion Supported", "Medium", "QRC_Sec_4.33", "QRC_No Data Deletion Supported", None, None, None, "Security Group", None, None, None),
        ("QR.45", "T1-2_v1", "QR_No Security Certifications", "IF: Any", "Question", "4.49", "Equal To", "No", "Create risk", "QRN_No Security Certifications", "High", "QRC_Sec_4.34", "QRC_No Security Certifications", None, None, None, "Security Group", None, None, None),
        ("QR.46", "T1-2_v1", "QR_No Cyber Insurance", "IF: Any", "Question", "4.50", "Equal To", "No", "Create risk", "QRN_No Cyber Insurance", "High", "QRC_Sec_4.35", "QRC_No Cyber Insurance", None, None, None, "Security Group", None, None, None),
        ("QR.47", "T1-2_v1", "QR_No SSO_SCIM Provisioning", "IF: Any", "Question", "5.6", "Equal To", "No", "Create risk", "QRN_No SSO_SCIM Provisioning", "Medium", "QRC_IT_5.1", "QRC_No SSO_SCIM Provisioning", None, None, None, "IT Group", None, None, None),
        ("QR.48", "T1-2_v1", "QR_Sensitive Targeting Data", "IF: Any", "Question", "6.1", "Equal To", "Yes", "Create risk", "QRN_Sensitive Targeting Data", "Medium", "QRC_Mar_6.1", "QRC_Sensitive Targeting Data", None, None, None, "Legal Group", None, None, None),
        ("QR.49", "T1-2_v1", "QR_Publicity Rights", "IF: Any", "Question", "6.2", "Equal To", "Yes", "Create risk", "QRN_Publicity Rights", "Medium", "QRC_Mar_6.2", "QRC_Publicity Rights", None, None, None, "Legal Group", None, None, None),
        ("QR.50", "T1-2_v1", "QR_No Co-branding Disclosures", "IF: Any", "Question", "6.3", "Equal To", "No", "Create risk", "QRN_No Co-branding Disclosures", "Medium", "QRC_Mar_6.3", "QRC_No Co-branding Disclosures", None, None, None, "Legal Group", None, None, None),
        ("QR.51", "T1-2_v1", "QR_No Employee Poaching Policy", "IF: Any", "Question", "7.2", "Equal To", "No", "Create risk", "QRN_No Employee Poaching Policy", "Medium", "QRC_Pcr_7.1", "QRC_No Employee Poaching Policy", None, None, None, "Procurement Group", None, None, None),
        ("QR.52", "T1-2_v1", "QR_No ESG Policy", "IF: Any", "Question", "7.3", "Equal To", "No", "Create risk", "QRN_No ESG Policy", "Medium", "QRC_Pcr_7.2", "QRC_No ESG Policy", None, None, None, "Procurement Group", None, None, None),
        ("QR.53", "T1-2_v1", "QR_No SLA KPI in Contract", "IF: Any", "Question", "8.1", "Equal To", "No", "Create risk", "QRN_No SLA KPI in Contract", "High", "QRC_RR_8.1", "QRC_No SLA KPI in Contract", None, None, None, "Compliance Group", None, None, None),
        ("QR.54", "T1-2_v1", "QR_No Business Continuity Plan", "IF: Any", "Question", "8.3", "Equal To", "No", "Create risk", "QRN_No Business Continuity Plan", "High", "QRC_RR_8.2", "QRC_No Business Continuity Plan", None, None, None, "Security Group", None, None, None),
        ("QR.55", "T1-2_v1", "QR_No Disaster Recovery Plan", "IF: Any", "Question", "8.4", "Equal To", "No", "Create risk", "QRN_No Disaster Recovery Plan", "High", "QRC_RR_8.3", "QRC_No Disaster Recovery Plan", None, None, None, "Security Group", None, None, None),
        # QR.56 to QR.58: T1-2 Task & Scoring Rules
        ("QR.56", "T1-2_v1", "QR_Task Assessment Completed", "Condition 1 OR Condition 2", "Question", "1.3 OR 4.50", "Contains Any", "Yes and No", "Create task upon submission", None, None, None, None, "Assessment Submitted", "Assessment workflow approvers", "ALL TPRM Groups", "Vendor Risk Management Group", None, None, "Triggers when Question 1.3 or 4.50 contains Yes or No upon submission."),
        ("QR.57", "T1-2_v1", "QR_Template score rule", "IF: Any", "Assessment Score", "Tier 1 and 2 assessment scoring", "Less than", "40", "Create task upon submission", None, None, None, None, "Low Assessment Score", "N/A", "TPRM_Vendor Risk Management Team", "Vendor Risk Management Group", None, None, None),
        ("QR.58", "T1-2_v1", "Tier1 and 2 assessment scoring", "ALL", "Scoring", "ALL Yes and No and one Options based (0-5,5-10 and 10+)", "Average", "Average", "Scoring Type: Average", None, None, None, None, None, None, None, "Vendor Risk Management Group", None, None, "Source states O-5,5-10 and 10+."),
        # QR.59 to QR.69: Tier 3 Risk Creation Rules
        ("QR.59", "T3_v1", "QR_T3_Non-US Company", "IF: Any", "Question", "1.2", "Equal To", "No", "Create risk", "QRN_T3_ Non-US Company", "High", "QRC_T3_CL_1.1", "QRC_T3_Non US Company", None, None, None, "Legal Group", None, None, None),
        ("QR.60", "T3_v1", "QR_T3_AML Requirement", "IF: Any", "Question", "2.2", "Equal To", "Yes", "Create risk", "QRN_T3_AML Requirement", "Medium", "QRC_CmL_2.3", "QRC_AML Requirement", None, None, None, "Compliance Group", None, None, None),
        ("QR.61", "T3_v1", "QR_T3_No Financial Audits", "IF: Any", "Question", "3.3", "Equal To", "No", "Create risk", "QRN_T3_No Financial Audits", "High", "QRC_Fin_3.2", "QRC_No Financial Audits", None, None, None, "Finance Group", None, None, None),
        ("QR.62", "T3_v1", "QR_T3_No Privacy Policy", "IF: Any", "Question", "4.1", "Equal To", "No", "Create risk", "QRN_T3_No Privacy Policy", "High", "QRC_Pri_4.8", "QRC_No Privacy Policy", None, None, None, "Privacy Group", None, None, None),
        ("QR.63", "T3_v1", "QR_T3_No Information Security Policy", "IF: Any", "Question", "4.2", "Equal To", "No", "Create risk", "QRN_T3_No Information Security Policy", "High", "QRC_Sec_4.27", "QRC_No Information Security Policy", None, None, None, "Security Group", None, None, None),
        ("QR.64", "T3_v1", "QR_T3_No RM for Information Security", "IF: Any", "Question", "4.3", "Equal To", "No", "Create risk", "QRN_T3_No RM for Information Security", "High", "QRC_Sec_4.28", "QRC_No RM for Information Security", None, None, None, "Security Group", None, None, None),
        ("QR.65", "T3_v1", "QR_T3_No Encryption Used", "IF: Any", "Question", "4.4", "Equal To", "No", "Create risk", "QRN_T3_No Encryption Used", "High", "QRC_Sec_4.24", "QRC_No Encryption Used", None, None, None, "Security Group", None, None, None),
        ("QR.66", "T3_v1", "QR_T3_No Cyber Insurance", "IF: Any", "Question", "4.5", "Equal To", "No", "Create risk", "QRN_T3_No Cyber Insurance", "High", "QRC_Sec_4.35", "QRC_No Cyber Insurance", None, None, None, "Security Group", None, None, None),
        ("QR.67", "T3_v1", "QR_T3_No Notification to Cadence", "IF: Any", "Question", "5.2", "Equal To", "No", "Create risk", "QRN_T3_No Notification to Cadence", "High", "QRC_Sec_4.23", "QRC_No Notification to Cadence", None, None, None, "Security Group", None, None, None),
        ("QR.68", "T3_v1", "QR_T3_No Business Continuity Plan", "IF: Any", "Question", "6.1", "Equal To", "No", "Create risk", "QRN_T3_No Business Continuity Plan", "High", "QRC_RR_8.2", "QRC_No Business Continuity Plan", None, None, None, "Security Group", None, None, None),
        ("QR.69", "T3_v1", "QR_T3_No Disaster Recovery Plan", "IF: Any", "Question", "6.2", "Equal To", "No", "Create risk", "QRN_T3_No Disaster Recovery Plan", "High", "QRC_RR_8.3", "QRC_No Disaster Recovery Plan", None, None, None, "Security Group", None, None, None),
        # QR.70 to QR.73: Tier 3 Task, Scoring & Auto-Approval Rules
        ("QR.70", "T3_v1", "QR_T3_Task Assessment Completed", "Condition 1 OR Condition 2", "Question", "1.2 OR 4.5", "Contains Any", "Yes and No", "Create task upon submission", None, None, None, None, "Assessment Submitted_T3", "Assessment workflow approvers", "ALL TPRM Groups", "Vendor Risk Management Group", None, None, None),
        ("QR.71", "T3_v1", "QR_T3_Template score rule", "IF: Any", "Assessment Score", "Tier 1 and 2 assessment scoring", "Less than", "40", "Create task upon submission", None, None, None, None, "Template score rule_T3", "N/A", "TPRM_Vendor Risk Management Team", "Vendor Risk Management Group", None, None, "Source references 'Tier 1 and 2 assessment scoring' in Question column for QR.71."),
        ("QR.72", "T3_v1", "Tier 3 assessment scoring", "ALL", "Scoring", "ALL Yes and No questions", "Average", "Average", "Scoring Type: Average", None, None, None, None, None, None, None, "Vendor Risk Management Group", None, None, None),
        ("QR.73", "T3_v1", "QR_T3_Auto Approve", "IF: ALL", "Question", "All required questions", "Equal To", "Yes / No", "Auto-Complete Assessment Upon Submission", None, None, None, None, None, None, None, "Vendor Risk Management Group", "Approved", "The third-party is Approved", "Evaluates that all required questions are answered with favorable responses (no adverse risk triggers)."),
        # QR.74 to QR.82: T1-2 Department-Specific Task Rules
        ("QR.74", "T1-2_v1", "QR_Task Legal Risk", "IF: Any", "Question", "Added as per requirement (Section 1: 1.3, 1.8, 1.9, 1.11)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Legal Risk Identified for Third-Party", "--", "TPRM_Legal Group", "Legal Group", None, None, "Triggered when any Legal section risk question is answered adversely."),
        ("QR.75", "T1-2_v1", "QR_Task Procurement Risk", "IF: Any", "Question", "Added as per requirement (Section 7: 7.2, 7.3)", "Equal to, Contains Any", "Yes and No, Options", "Create task upon submission", None, None, None, None, "Procurement Risk Identified for Third-Party", "--", "TPRM_Procurement Group", "Procurement Group", None, None, "Triggered when any Procurement section risk question is answered adversely."),
        ("QR.76", "T1-2_v1", "QR_Task Compliance Risk", "IF: Any", "Question", "Added as per requirement (Section 2: 2.2, 2.3, 2.6, 2.7)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Compliance Risk Identified for Third-Party", "--", "TPRM_Compliance Group", "Compliance Group", None, None, "Triggered when any Compliance section risk question is answered adversely."),
        ("QR.77", "T1-2_v1", "QR_Task Finance Risk", "IF: Any", "Question", "Added as per requirement (Section 3: 3.3, 3.5)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Finance Risk Identified for Third-Party", "--", "TPRM_Finance Group", "Finance Group", None, None, "Triggered when any Finance section risk question is answered adversely."),
        ("QR.78", "T1-2_v1", "QR_Task Privacy Risk", "IF: Any", "Question", "Added as per requirement (Section 4 Privacy: 4.1-4.14)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Privacy Risk Identified for Third-Party", "--", "TPRM_Privacy Group", "Privacy Group", None, None, "Triggered when any Privacy/AI section risk question is answered adversely."),
        ("QR.79", "T1-2_v1", "QR_Task Data Quality Risk", "IF: Any", "Question", "Added as per requirement (Data Quality / Marketing: 6.1, 6.2, 6.3)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Data Quality Risk Identified for Third-Party", "--", "TPRM_Data Quality Group", "Data Quality Group", None, None, "Triggered when any Data Quality / targeting data risk question is answered adversely."),
        ("QR.80", "T1-2_v1", "QR_Task Security Risk", "IF: Any", "Question", "Added as per requirement (Section 4 Security: 4.15-4.50, 8.3, 8.4)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Security Risk Identified for Third-Party", "--", "TPRM_Security Group", "Security Group", None, None, "Triggered when any Security section risk question is answered adversely."),
        ("QR.81", "T1-2_v1", "QR_Task IT Risk", "IF: Any", "Question", "5.6", "Equal to", "No", "Create task upon submission", None, None, None, None, "IT Risk Identified for Third-Party", "--", "TPRM_IT Group", "IT Group", None, None, "Explicitly mapped to Question 5.6 = No in Appendix E."),
        ("QR.82", "T1-2_v1", "QR_Task IT Requirement", "IF: Any", "Question", "5.1", "Equal to", "Yes", "Create task upon submission", None, None, None, None, "IT Requirement Identified for Third-Party", "--", "TPRM_IT Group", "IT Group", None, None, "Explicitly mapped to Question 5.1 = Yes in Appendix E."),
        # QR.83 to QR.90: Tier 3 Department-Specific Task Rules
        ("QR.83", "T3_v1", "QR_T3_Task Legal Risk", "IF: Any", "Question", "Added as per requirement (Section 1: 1.2)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Legal Risk Identified for Third-Party_T3", "--", "TPRM_Legal Group", "Legal Group", None, None, None),
        ("QR.84", "T3_v1", "QR_T3_Task Procurement Risk", "IF: Any", "Question", "Added as per requirement", "Equal to", "Yes and No, Options", "Create task upon submission", None, None, None, None, "Procurement Risk Identified for Third-Party_T3", "--", "TPRM_Procurement Group", "Procurement Group", None, None, None),
        ("QR.85", "T3_v1", "QR_T3_Task Compliance Risk", "IF: Any", "Question", "Added as per requirement (Section 2: 2.2)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Compliance Risk Identified for Third-Party_T3", "--", "TPRM_Compliance Group", "Compliance Group", None, None, None),
        ("QR.86", "T3_v1", "QR_T3_Task Finance Risk", "IF: Any", "Question", "Added as per requirement (Section 3: 3.3, 3.4)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Finance Risk Identified for Third-Party_T3", "--", "TPRM_Finance Group", "Finance Group", None, None, None),
        ("QR.87", "T3_v1", "QR_T3_Task Privacy Risk", "IF: Any", "Question", "Added as per requirement (Section 4: 4.1)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Privacy Risk Identified for Third-Party_T3", "--", "TPRM_Privacy Group", "Privacy Group", None, None, None),
        ("QR.88", "T3_v1", "QR_T3_Task Security Risk", "IF: Any", "Question", "Added as per requirement (Section 4-6: 4.2-4.5, 5.2, 6.1, 6.2)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "Security Risk Identified for Third-Party_T3", "--", "TPRM_Security Group", "Security Group", None, None, None),
        ("QR.89", "T3_v1", "QR_T3_Task IT Requirement", "IF: Any", "Question", "5.1", "Equal to", "Yes", "Create task upon submission", None, None, None, None, "IT Requirement Identified for Third-Party_T3", "--", "TPRM_IT Group", "IT Group", None, None, "Explicitly mapped to Question 5.1 = Yes in Appendix E."),
        ("QR.90", "T3_v1", "QR_Task IT Risk", "IF: Any", "Question", "Added as per requirement (5.2)", "Equal to", "Yes and No", "Create task upon submission", None, None, None, None, "IT Risk Identified for Third-Party_T3", "--", "TPRM_IT Group", "IT Group", None, None, "Preserves exact rule name 'QR_Task IT Risk' for QR.90 in Appendix E."),
    ]

    for (
        r_code, t_code, r_name, c_logic, trig_t, q_code, op, val, act,
        r_n, inh, c_id, c_n, t_name, assignee, collab, grp, res_st, res_cm, notes
    ) in risk_rules_data:
        if not db.query(RiskRule).filter_by(rule_code=r_code).first():
            db.add(RiskRule(
                rule_code=r_code,
                template_code=t_code,
                rule_name=r_name,
                condition_logic=c_logic,
                trigger_type=trig_t,
                trigger_question_code=q_code,
                trigger_operator=op,
                trigger_response=val,
                action_type=act,
                risk_name=r_n,
                inherent_risk=inh,
                control_id=c_id,
                control_name=c_n,
                task_name=t_name,
                assignee=assignee,
                collaborator_group=collab,
                responsible_group=grp,
                result_status=res_st,
                result_comments=res_cm,
                source_notes=notes,
            ))
    db.flush()

    # 13. Realistic Initial Vendors across categories & tiers
    initial_vendors = [
        ("Apex Cloud Infrastructure Ltd", "Technology", "Critical", "security@apexcloud.com", "daniela.figueroa@cadence.com", "Tier 1", "Service Provider and Vendor", "https://apexcloud.com", "Live", "CD_Service Providers Workflow", "Live", datetime.now(timezone.utc) - timedelta(days=285)),
        ("Global Staffing Partners LLC", "Operations", "Medium", "contact@globalstaffing.com", "chris.schmitz@cadence.com", "Tier 2", "Staffing Vendor", "https://globalstaffing.com", "Live", "CD_Staffing Vendors Workflow", "Live", datetime.now(timezone.utc) - timedelta(days=500)),
        ("OmniChannel Revenue Growth Inc", "Strategic", "High", "admin@omnichannelrev.com", "shimane.smith@cadence.com", "Tier 1", "Revenue Partner", "https://omnichannelrev.com", "In Progress", "CD_Revenue Partners Workflow", "Launching RevPart", None),
        ("Digital Horizon Marketing Agency", "Consulting", "Medium", "ops@digitalhorizon.com", "daniela.figueroa@cadence.com", "Tier 2", "Marketing Partner", "https://digitalhorizon.com", "Review Reject", "CD_Marketing Partners Workflow", "Review Reject MarPart", None),
        ("EuroData Consult GmbH", "Regulatory", "High", "privacy@eurodataconsult.de", "dayo.seton@cadence.com", "Tier 1", "International Vendor", "https://eurodataconsult.de", "In Progress", "CD_International Vendors Workflow", "Launching IntVen", None),
        ("Swift Courier Express", "Operations", "Low", "dispatch@swiftcourier.com", "rob.tilney@cadence.com", "Tier 3", "Service Provider and Vendor", "https://swiftcourier.com", "Live", "CD_Tier3 Workflow", "Live", datetime.now(timezone.utc) - timedelta(days=100)),
        ("NexGen AI Labs Inc", "Technology", "Critical", "security@nexgenai.io", "daniela.figueroa@cadence.com", "Tier 1", "Service Provider and Vendor", "https://nexgenai.io", "In Progress", "CD_Service Providers Workflow", "Launching ServPro", None),
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

            wf_obj = db.query(Workflow).filter_by(name=wf_name).first()
            if wf_obj:
                inst = WorkflowInstance(
                    workflow_id=wf_obj.id,
                    vendor_id=vendor.id,
                    current_stage=stage,
                    started_at=datetime.now(timezone.utc) - timedelta(days=10),
                )
                db.add(inst)
                db.flush()
                db.add(WorkflowTransition(
                    instance_id=inst.id,
                    actor_email="system@cadence.com",
                    from_stage="New Third Party",
                    to_stage=stage,
                    trigger_name="On_T_Assign Workflow",
                    rule_name="WR.ON.6" if v_tier == "Tier 3" else "WR.ON.*",
                    decision_reason=f"Automated routing for {v_cat} ({v_tier})",
                ))

            # Create an assessment record
            template_code = "T3_v1" if v_tier == "Tier 3" else "T1-2_v1"
            asm_status = "Approved" if status == "Live" else ("Rejected" if "Reject" in stage else "In Review")
            asm = Assessment(
                vendor_id=vendor.id,
                template_code=template_code,
                respondent_email=pvc,
                approver_group="Vendor Risk Management Group",
                status=asm_status,
                overall_score=92.0 if asm_status == "Approved" else (35.0 if asm_status == "Rejected" else 74.5),
                due_date=datetime.now(timezone.utc) + timedelta(days=9),
                submitted_at=datetime.now(timezone.utc) - timedelta(days=2),
                completed_at=last_comp or (datetime.now(timezone.utc) if asm_status in ["Approved", "Rejected"] else None),
                decision_reason="The third-party is Approved" if (asm_status == "Approved" and v_tier == "Tier 3") else ("Assessment approved following VRM team review" if asm_status == "Approved" else ("Rejected due to missing SOC 2 certification and unmitigated high risks" if asm_status == "Rejected" else None)),
                decision_by="daniela.figueroa@cadence.com" if asm_status in ["Approved", "Rejected"] else None,
            )
            db.add(asm)
            db.flush()

            # Pre-populate realistic responses for assessments
            sample_responses = {"1.1": v_name, "1.2": "Yes", "1.3": "Yes", "2.2": "Yes", "3.3": "Yes", "4.14": "Yes", "4.18": "Yes", "4.34": "Yes", "4.49": "Yes", "4.50": "Yes"}
            if v_name == "EuroData Consult GmbH":
                sample_responses.update({"1.3": "No", "1.5": "Yes", "1.8": "5-10", "4.1": "Yes", "4.4": "Yes", "4.10": "Yes", "4.11": "Yes"})
            elif v_name == "Digital Horizon Marketing Agency":
                sample_responses.update({"4.18": "No", "4.49": "No", "6.1": "Yes", "6.2": "Yes"})
            for q_c, r_v in sample_responses.items():
                db.add(QuestionResponse(assessment_id=asm.id, question_code=q_c, response_value=r_v))

            # Create contracts
            contract = Contract(
                vendor_id=vendor.id,
                contract_reference=f"IC-{v_tier.replace(' ', '').upper()}-{vendor.id[:6].upper()}",
                title=f"Master Services Agreement — {v_name}",
                source="Ironclad",
                status="Executed" if status == "Live" else "In Negotiation",
                effective_date=datetime.now(timezone.utc).date() - timedelta(days=60),
                expiration_date=datetime.now(timezone.utc).date() + timedelta(days=305),
            )
            db.add(contract)
            db.flush()

            if status == "Live":
                db.add(RenewalDecision(
                    vendor_id=vendor.id,
                    assessment_id=asm.id,
                    contract_id=contract.id,
                    decision="Pending Reassessment" if v_name == "Apex Cloud Infrastructure Ltd" else "Renewed",
                    decided_by="daniela.figueroa@cadence.com",
                    rationale="Annual/Bi-annual renewal tracked against reassessment SLA.6/SLA.7.",
                    open_findings_at_decision="0",
                    next_renewal_date=contract.expiration_date,
                ))

            # Add tasks and findings if adverse or in review
            if "Reject" in stage:
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=asm.id,
                    task_type="Review Reject Followup",
                    title=f"Notify MarPart Reject: {v_name}",
                    description="Vendor rejected during assessment. Follow up with business owner within 14 days per WR.MP.5.",
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
                    mitigation_recommendation="Vendor must furnish SOC 2 Type II or ISO 27001 certification before onboarding approval.",
                    due_date=datetime.now(timezone.utc) + timedelta(days=9)
                ))
                db.add(RiskFinding(
                    assessment_id=asm.id,
                    vendor_id=vendor.id,
                    rule_code="QR.23",
                    risk_name="QRN_No MFA",
                    inherent_risk="Medium",
                    control_id="QRC_Sec_4.12",
                    control_name="QRC_No MFA",
                    responsible_group="Security Group",
                    status="Open",
                    mitigation_recommendation="Enforce mandatory Multi-Factor Authentication across all administrative and remote access.",
                    due_date=datetime.now(timezone.utc) + timedelta(days=14)
                ))

            if v_name == "EuroData Consult GmbH":
                db.add(RiskFinding(
                    assessment_id=asm.id,
                    vendor_id=vendor.id,
                    rule_code="QR.1",
                    risk_name="QRN_Non US Company",
                    inherent_risk="High",
                    control_id="QRC_CL_1.1",
                    control_name="QRC_Non US Company",
                    responsible_group="Legal Group",
                    status="Open",
                    mitigation_recommendation="Execute Standard Contractual Clauses (SCCs) and GDPR Cross-Border Transfer Impact Assessment.",
                    due_date=datetime.now(timezone.utc) + timedelta(days=9)
                ))
                db.add(RiskFinding(
                    assessment_id=asm.id,
                    vendor_id=vendor.id,
                    rule_code="QR.12",
                    risk_name="QRN_Cust_Data Outside US",
                    inherent_risk="High",
                    control_id="QRC_Pri_4.1",
                    control_name="QRC_Cust_Data Outside US",
                    responsible_group="Privacy Group",
                    status="Open",
                    mitigation_recommendation="Verify regional data residency controls and execute Privacy Group DPA addendum.",
                    due_date=datetime.now(timezone.utc) + timedelta(days=9)
                ))
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=asm.id,
                    task_type="Departmental Risk Review",
                    title=f"Privacy Risk Identified for Third-Party: {v_name}",
                    description="Review cross-border customer data transfer and AI interaction responses under QR.78 / SLA.2 (4 days).",
                    assignee_email="dayo.seton@cadence.com",
                    collaborator_group="Privacy Group",
                    due_date=datetime.now(timezone.utc) + timedelta(days=4),
                    reminder_date=datetime.now(timezone.utc) + timedelta(days=2),
                    status="Pending"
                ))

            if status == "In Progress":
                db.add(Task(
                    vendor_id=vendor.id,
                    assessment_id=asm.id,
                    task_type="Assessment Approval",
                    title=f"Assessment Submitted: {v_name}",
                    description="Evaluate questionnaire responses, departmental reviews, and record VRM approval/rejection decision (QR.56 / SLA.2).",
                    assignee_email="daniela.figueroa@cadence.com",
                    collaborator_group="Vendor Risk Management Group",
                    due_date=datetime.now(timezone.utc) + timedelta(days=4),
                    reminder_date=datetime.now(timezone.utc) + timedelta(days=2),
                    status="Pending"
                ))

            db.add(Notification(
                recipient_email="daniela.figueroa@cadence.com",
                subject=f"TPRM Workflow Active: {v_name} ({v_tier})",
                body=f"{v_name} is in workflow '{wf_name}' at stage '{stage}'.",
                notification_type="InApp",
                link_url=f"/vendors/{vendor.id}"
            ))

            db.add(AuditLog(
                actor_email="system@cadence.com",
                action="VENDOR_SEEDED_AND_ROUTED",
                entity_type="VENDOR",
                entity_id=vendor.id,
                details={
                    "vendor_name": v_name,
                    "category": v_cat,
                    "tier": v_tier,
                    "workflow": wf_name,
                    "stage": stage,
                    "assessment_id": asm.id
                }
            ))

    db.commit()
