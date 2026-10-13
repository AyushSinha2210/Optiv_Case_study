# Requirements Traceability Matrix: Cadence TPRM Application

**Source Authority:** `Cadence_TPRM_Training.docx`  
**Status Values:** `NOT_ASSESSED`, `EXISTING_VERIFIED`, `EXISTING_BROKEN`, `NOT_IMPLEMENTED`, `IN_PROGRESS`, `IMPLEMENTED`, `TESTED`, `BLOCKED`  

---

## 1. Vendor Taxonomy & Core Attributes (Section 2.1, 4.1, 5.2, Table 4, Table 9)

| Req ID | Document Ref | Description | Data Model / Field | Target Implementation | Status |
|---|---|---|---|---|---|
| **REQ-CAT-1** | Sec 2.1, Tab 4 | Service Providers and Vendors Category | `Vendor.category == "Service Provider and Vendor"` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-CAT-2** | Sec 2.1, Tab 4 | Revenue Partners Category | `Vendor.category == "Revenue Partner"` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-CAT-3** | Sec 2.1, Tab 4 | Marketing Partners Category | `Vendor.category == "Marketing Partner"` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-CAT-4** | Sec 2.1, Tab 4 | International Vendors Category | `Vendor.category == "International Vendor"` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-CAT-5** | Sec 2.1, Tab 4 | Staffing Vendors Category | `Vendor.category == "Staffing Vendor"` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-TIER-1** | Sec 2.1, Tab 9 | Vendor Tier (Tier 1, Tier 2, Tier 3) | `Vendor.tier in ["Tier 1", "Tier 2", "Tier 3"]` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-ATTR-1** | Table 9 | Name (Vendor Name) | `Vendor.name: str` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-ATTR-2** | Table 9 | Type (Consulting, Operations, Regulatory, Strategic, Technology, Unknown) | `Vendor.type: VendorTypeEnum` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-ATTR-3** | Table 9 | Criticality (Critical, High, Medium, Low) | `Vendor.criticality: CriticalityEnum` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-ATTR-4** | Table 9 | Primary Vendor Contact (PVC Email) | `Vendor.primary_vendor_contact: EmailStr` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-ATTR-5** | Table 9 | Business Owner (Internal Email) | `Vendor.business_owner: EmailStr` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |
| **REQ-ATTR-6** | Table 9 | Website (Domain URL) | `Vendor.website: str` | `src/cadence_tprm/models/vendor.py` | IN_PROGRESS |

---

## 2. Organization, User Groups & RBAC (Section 2.3, 4.2, 6.1, Table 5)

| Req ID | Group Name | Document Permissions | Authoritative Members | Implemented Model / Access | Status |
|---|---|---|---|---|---|
| **REQ-GRP-1** | Vendor Risk Management Group | Admin | Daniela Figueroa, Bridgett Gatewood, KC Burney, Jyoti Karwal | `Role == "TPRM_ADMIN"`, Full workflow management, approve/reject | IN_PROGRESS |
| **REQ-GRP-2** | Vendor Risk Management Group | Edit | Tamika Oliver, Shimane Smith, Chris Schmitz, Chris Ott, Rob Tilney | `Role == "VRM_REVIEWER"`, Edit access, assessment review | IN_PROGRESS |
| **REQ-GRP-3** | Legal Group | Edit | Shimane Smith, Daniela Figueroa | Review Legal / Contracting section | IN_PROGRESS |
| **REQ-GRP-4** | Procurement Group | Edit | Chris Schmitz | Review Procurement section | IN_PROGRESS |
| **REQ-GRP-5** | Finance Group | Edit | Daniela Figueroa | Review Finance / Oracle onboarding | IN_PROGRESS |
| **REQ-GRP-6** | IT Group | Edit | Rob Tilney, Jyoti Karwal, Jonathan Szeto, Marc Otani | Review IT / SSO / SCIM requirements | IN_PROGRESS |
| **REQ-GRP-7** | Compliance Group | Edit | Tamika Oliver | Review Compliance / AML section | IN_PROGRESS |
| **REQ-GRP-8** | Privacy Group | Edit | Dayo Seton | Review Privacy / AI / Data Processing | IN_PROGRESS |
| **REQ-GRP-9** | Security Group | Edit | Chris Ott, Melisa Cardozo, DK Koran, Erik Hansen | Review Security / SOC / Certs / Pen Tests | IN_PROGRESS |
| **REQ-GRP-10**| Data Quality Group | Edit | Daniela Figueroa | Review Data Quality & consistency | IN_PROGRESS |

---

## 3. Workflows & State Machine Rules (Section 4.2, 5.1, 6.4, Tables 6, 7, 8, 10)

| Rule ID | Stage / Trigger | Conditions | Action / Destination | Status |
|---|---|---|---|---|
| **WR.ON.1** | Onboarding -> Launching | Category: Revenue Partner, Tier: 1 or 2 | Switch to `CD_Revenue Partners Workflow`, stage `Launching RevPart` | IN_PROGRESS |
| **WR.ON.2** | Onboarding -> Launching | Category: Marketing Partner, Tier: 1 or 2 | Switch to `CD_Marketing Partners Workflow`, stage `Launching MarPart` | IN_PROGRESS |
| **WR.ON.3** | Onboarding -> Launching | Category: International Vendor, Tier: 1 or 2 | Switch to `CD_International Vendors Workflow`, stage `Launching IntVen` | IN_PROGRESS |
| **WR.ON.4** | Onboarding -> Launching | Category: Service Provider, Tier: 1 or 2 | Switch to `CD_Service Providers Workflow`, stage `Launching ServPro` | IN_PROGRESS |
| **WR.ON.5** | Onboarding -> Launching | Category: Staffing Vendor, Tier: 1 or 2 | Switch to `CD_Staffing Vendors Workflow`, stage `Launching StafVen` | IN_PROGRESS |
| **WR.ON.6** | Onboarding -> Launching | Category: Any, Tier: Tier 3 | Switch to `CD_Tier3 Workflow`, stage `Launching Tier3` | IN_PROGRESS |
| **WR.*.1**  | Initiated -> Launching | Category match && Tier != Tier 3 | Advance to Launching stage | IN_PROGRESS |
| **WR.*.2**  | Launching stage rule | Category match && Tier != Tier 3 | Launch `Due Diligence Questionnaire T1-2 v1`, Approver: VRM, Respondent: PVC | IN_PROGRESS |
| **WR.*.3**  | Launching -> Live | Assessment Completed, Approved by VRM | Advance to `Live`, notify approval | IN_PROGRESS |
| **WR.*.4**  | Launching -> Review Reject | Assessment Completed, Rejected by VRM | Advance to `Review Reject`, notify reject | IN_PROGRESS |
| **WR.*.5**  | Review Reject stage rule| In Review Reject stage | Notify rejection, Create Task for Business Owner, Collaborator: VRM (14d SLA) | IN_PROGRESS |
| **WR.*.6**  | Live stage rule | In Live stage | Send approval notification | IN_PROGRESS |
| **WR.T3.1** | Tier 3 Initiated | Any Category, Tier == Tier 3 | Advance to `Launching Tier3` | IN_PROGRESS |
| **WR.T3.2** | Tier 3 Launching | Tier == Tier 3 | Launch `Due Diligence Questionnaire T3 v1`, Approver: VRM, Respondent: PVC | IN_PROGRESS |
| **WR.T3.3** | Tier 3 Auto-Approve | Completed with clean responses (QR.73) | Auto-advance to `Live`, Result: Approved | IN_PROGRESS |
| **WR.T3.4** | Tier 3 Rejection | Rejected manually or failed criteria | Advance to `Review Reject Tier3` | IN_PROGRESS |
| **WR.T3.5** | Tier 3 Reject Stage Rule| Tier == Tier 3 in Review Reject | Notify reject, Create Task for Business Owner (14d SLA) | IN_PROGRESS |
| **WR.T3.6** | Tier 3 Approval Stage | Tier == Tier 3 in Live | Send approval notification | IN_PROGRESS |
| **AR.T1.1** | Automation Reassessment | Tier 1, Days >= 275 | Issue reassessment (T1-2 v1), copy previous answers, notify Business Owner | IN_PROGRESS |
| **AR.T2.1** | Automation Reassessment | Tier 2, Days >= 640 | Issue reassessment (T1-2 v1), copy previous answers, notify Business Owner | IN_PROGRESS |
| **AR.T3.1** | Automation Reassessment | Tier 3, Days >= 640 | Issue reassessment (T3 v1), copy previous answers, notify Business Owner | IN_PROGRESS |

---

## 4. Conditional Show-Logic Rules (Appendix C, Table 12)

| Logic ID | Questionnaire | Trigger Question & Answer | Shown Questions | Status |
|---|---|---|---|---|
| **CL.1**  | DDQ T1-2 v1 | Q1.5 == "Yes" | Show Q1.6, Q1.7, Q1.8 (Incorporation, state, affiliates) | IN_PROGRESS |
| **CL.2**  | DDQ T1-2 v1 | Q2.4 == "Yes" | Show Q2.5 (Consumer complaints policy copy) | IN_PROGRESS |
| **CL.3**  | DDQ T1-2 v1 | Q3.6 == "No" | Show Q3.7 (Oracle Vendor Onboarding Form upload) | IN_PROGRESS |
| **CL.4**  | DDQ T1-2 v1 | Q4.4 == "Yes" | Show Q4.5, Q4.6 (Cadence data subjects, personal data categories) | IN_PROGRESS |
| **CL.5**  | DDQ T1-2 v1 | Q4.10 == "Yes"| Show Q4.11, Q4.12, Q4.13 (AI customer interaction, LLMs, AI risk processes)| IN_PROGRESS |
| **CL.6**  | DDQ T1-2 v1 | Q4.18 == "No" | Show Q4.19 (MFA non-requirement justification) | IN_PROGRESS |
| **CL.7**  | DDQ T1-2 v1 | Q4.20 == "Yes"| Show Q4.21 (VPN security & role-based access details) | IN_PROGRESS |
| **CL.8**  | DDQ T1-2 v1 | Q4.24 == "Yes"| Show Q4.25 (Separation method: Logical, Physical, VLAN, Cloud) | IN_PROGRESS |
| **CL.9**  | DDQ T1-2 v1 | Q4.26 == "Yes"| Show Q4.27 (Penetration testing remediation timelines & reporting) | IN_PROGRESS |
| **CL.10** | DDQ T1-2 v1 | Q4.30 == "Yes"| Show Q4.31 (Security incident details: type, remediation, residual risk) | IN_PROGRESS |
| **CL.11** | DDQ T1-2 v1 | Q4.34 == "Yes"| Show Q4.35 (Encryption key storage and management procedures) | IN_PROGRESS |
| **CL.12** | DDQ T1-2 v1 | Q4.36 == "Yes"| Show Q4.37 (Data Loss Prevention scope) | IN_PROGRESS |
| **CL.13** | DDQ T1-2 v1 | Q8.1 == "Yes" | Show Q8.2 (Contractual SLA/KPI engagement details) | IN_PROGRESS |
| **CL.14** | DDQ T3 v1   | Q3.4 == "No"  | Show Q3.5 (Oracle Vendor Onboarding Form upload for Tier 3) | IN_PROGRESS |

---

## 5. Service-Level Agreements & Tasks (Appendix D, Table 13)

| SLA ID | Name | Duration | Reminder | Implementation / Target | Status |
|---|---|---|---|---|---|
| **SLA.1** | Assessment Completion | 9 Days | 5 Days | Assessment deadline calculation & reminder event | IN_PROGRESS |
| **SLA.2** | Review Responses | 4 Days | 2 Days | Reviewer group response SLA | IN_PROGRESS |
| **SLA.3** | High Risk Response | 5 + 4 = 9 Days | 3 Days | High Risk acknowledgment task | IN_PROGRESS |
| **SLA.4** | Medium Risk Response | 10 + 4 = 14 Days | 7 Days | Medium Risk acknowledgment task | IN_PROGRESS |
| **SLA.5** | Low Risk Response | 15 + 4 = 19 Days | 10 Days | Low Risk acknowledgment task | IN_PROGRESS |
| **SLA.6** | Renewal Lead Time T1 | 275 Days (Annual - 90d)| N/A | Daily automation check triggers reassessment | IN_PROGRESS |
| **SLA.7** | Renewal Lead Time T2/3| 640 Days (24m - 90d)  | N/A | Daily automation check triggers reassessment | IN_PROGRESS |

---

## 6. Questionnaire Risk Evaluation Rules (Appendix E, Table 14: QR.1 to QR.90)

| Rule ID | Questionnaire | Trigger Question & Answer | Inherent Risk | Control ID & Name | Status |
|---|---|---|---|---|---|
| **QR.1** | DDQ T1-2 v1 | Q1.3 == "No" | High | `QRC_CL_1.1` QRC_Non US Company | IN_PROGRESS |
| **QR.2** | DDQ T1-2 v1 | Q1.8 == "0-5" | High | `QRC_CL_1.2` QRC_Business duration_less | IN_PROGRESS |
| **QR.3** | DDQ T1-2 v1 | Q1.8 == "5-10" | Medium | `QRC_CL_1.3` QRC_Business duration_medium | IN_PROGRESS |
| **QR.4** | DDQ T1-2 v1 | Q1.9 == "Yes" | Medium | `QRC_CL_1.4` QRC_Subsidiaries and Affiliates | IN_PROGRESS |
| **QR.5** | DDQ T1-2 v1 | Q1.11 == "Yes" | Medium | `QRC_CL_1.5` QRC_Recent M and A | IN_PROGRESS |
| **QR.6** | DDQ T1-2 v1 | Q2.2 == "No" | High | `QRC_CmL_2.1` QRC_No Compliance Report | IN_PROGRESS |
| **QR.7** | DDQ T1-2 v1 | Q2.3 == "No" | Medium | `QRC_CmL_2.2` QRC_No Strong Laws | IN_PROGRESS |
| **QR.8** | DDQ T1-2 v1 | Q2.6 == "Yes" | Medium | `QRC_CmL_2.3` QRC_AML Requirement | IN_PROGRESS |
| **QR.9** | DDQ T1-2 v1 | Q2.7 == "No" | Medium | `QRC_CmL_2.4` QRC_No AML Audit | IN_PROGRESS |
| **QR.10** | DDQ T1-2 v1 | Q3.3 == "No" | High | `QRC_Fin_3.1` QRC_No Financial Statement | IN_PROGRESS |
| **QR.11** | DDQ T1-2 v1 | Q3.5 == "No" | High | `QRC_Fin_3.2` QRC_No Financial Audits | IN_PROGRESS |
| **QR.12** | DDQ T1-2 v1 | Q4.1 == "Yes" | High | `QRC_Pri_4.1` QRC_Cust_Data Outside US | IN_PROGRESS |
| **QR.13** | DDQ T1-2 v1 | Q4.2 == "Yes" | High | `QRC_Pri_4.2` QRC_Operations_Risk Regions | IN_PROGRESS |
| **QR.14** | DDQ T1-2 v1 | Q4.4 == "Yes" | Medium | `QRC_Pri_4.3` QRC_Personal Data Collected | IN_PROGRESS |
| **QR.15** | DDQ T1-2 v1 | Q4.8 == "Yes" | Medium | `QRC_Pri_4.4` QRC_Sub-processor Used | IN_PROGRESS |
| **QR.16** | DDQ T1-2 v1 | Q4.11 == "Yes" | Medium | `QRC_Pri_4.5` QRC_AI Interaction with Data | IN_PROGRESS |
| **QR.17** | DDQ T1-2 v1 | Q4.12 == "Yes" | Medium | `QRC_Pri_4.6` QRC_LLM Use in Data Processing | IN_PROGRESS |
| **QR.18** | DDQ T1-2 v1 | Q4.13 == "No" | Medium | `QRC_Pri_4.7` QRC_No RM for AI | IN_PROGRESS |
| **QR.19** | DDQ T1-2 v1 | Q4.14 == "No" | High | `QRC_Pri_4.8` QRC_No Privacy Policy | IN_PROGRESS |
| **QR.20** | DDQ T1-2 v1 | Q4.15 == "No" | High | `QRC_Sec_4.9` QRC_No IAM Policy | IN_PROGRESS |
| **QR.21** | DDQ T1-2 v1 | Q4.16 == "No" | Medium | `QRC_Sec_4.10` QRC_No Least Privilege Access | IN_PROGRESS |
| **QR.22** | DDQ T1-2 v1 | Q4.17 == "No" | Medium | `QRC_Sec_4.11` QRC_No Password Policy | IN_PROGRESS |
| **QR.23** | DDQ T1-2 v1 | Q4.18 == "No" | Medium | `QRC_Sec_4.12` QRC_No MFA | IN_PROGRESS |
| **QR.24** | DDQ T1-2 v1 | Q4.20 == "Yes" | Medium | `QRC_Sec_4.13` QRC_Employee Remote Access | IN_PROGRESS |
| **QR.25** | DDQ T1-2 v1 | Q4.22 == "No" | High | `QRC_Sec_4.14` QRC_Network Not Monitored | IN_PROGRESS |
| **QR.26** | DDQ T1-2 v1 | Q4.23 == "No" | Medium | `QRC_Sec_4.15` QRC_No Tools for Vulnerability Scan | IN_PROGRESS |
| **QR.27** | DDQ T1-2 v1 | Q4.24 == "No" | Medium | `QRC_Sec_4.16` QRC_System Not Segrated | IN_PROGRESS |
| **QR.28** | DDQ T1-2 v1 | Q4.26 == "No" | High | `QRC_Sec_4.17` QRC_No Pen Test | IN_PROGRESS |
| **QR.29** | DDQ T1-2 v1 | Q4.27 == "No" | Medium | `QRC_Sec_4.18` QRC_No Remediation for Findings | IN_PROGRESS |
| **QR.30** | DDQ T1-2 v1 | Q4.28 == "No" | Medium | `QRC_Sec_4.19` QRC_No Security App Dev Policy | IN_PROGRESS |
| **QR.31** | DDQ T1-2 v1 | Q4.29 == "No" | High | `QRC_Sec_4.20` QRC_No Incident Response Plan | IN_PROGRESS |
| **QR.32** | DDQ T1-2 v1 | Q4.30 == "Yes" | High | `QRC_Sec_4.21` QRC_24 Mon Security Incident | IN_PROGRESS |
| **QR.33** | DDQ T1-2 v1 | Q4.32 == "No" | High | `QRC_Sec_4.22` QRC_No Breach Notification Process | IN_PROGRESS |
| **QR.34** | DDQ T1-2 v1 | Q4.33 == "No" | High | `QRC_Sec_4.23` QRC_No Notification to Cadence | IN_PROGRESS |
| **QR.35** | DDQ T1-2 v1 | Q4.34 == "No" | High | `QRC_Sec_4.24` QRC_No Encryption Used | IN_PROGRESS |
| **QR.36** | DDQ T1-2 v1 | Q4.36 == "No" | Medium | `QRC_Sec_4.25` QRC_No Data Loss Prevention | IN_PROGRESS |
| **QR.37** | DDQ T1-2 v1 | Q4.38 == "No" | Medium | `QRC_Sec_4.26` QRC_No Data Retention Policy | IN_PROGRESS |
| **QR.38** | DDQ T1-2 v1 | Q4.39 == "No" | High | `QRC_Sec_4.27` QRC_No Information Security Policy | IN_PROGRESS |
| **QR.39** | DDQ T1-2 v1 | Q4.40 == "No" | High | `QRC_Sec_4.28` QRC_No RM for Information Security | IN_PROGRESS |
| **QR.40** | DDQ T1-2 v1 | Q4.42 == "No" | Medium | `QRC_Sec_4.29` QRC_No Background checks for Emp | IN_PROGRESS |
| **QR.41** | DDQ T1-2 v1 | Q4.44 == "No" | Medium | `QRC_Sec_4.30` QRC_No Offboarding Process | IN_PROGRESS |
| **QR.42** | DDQ T1-2 v1 | Q4.45 == "Yes" | Medium | `QRC_Sec_4.31` QRC_BYOD Allowed | IN_PROGRESS |
| **QR.43** | DDQ T1-2 v1 | Q4.46 == "No" | Medium | `QRC_Sec_4.32` QRC_No MDM Policy | IN_PROGRESS |
| **QR.44** | DDQ T1-2 v1 | Q4.48 == "No" | Medium | `QRC_Sec_4.33` QRC_No Data Deletion Supported | IN_PROGRESS |
| **QR.45** | DDQ T1-2 v1 | Q4.49 == "No" | High | `QRC_Sec_4.34` QRC_No Security Certifications | IN_PROGRESS |
| **QR.46** | DDQ T1-2 v1 | Q4.50 == "No" | High | `QRC_Sec_4.35` QRC_No Cyber Insurance | IN_PROGRESS |
| **QR.47** | DDQ T1-2 v1 | Q5.6 == "No" | Medium | `QRC_IT_5.1` QRC_No SSO_SCIM Provisioning | IN_PROGRESS |
| **QR.48** | DDQ T1-2 v1 | Q6.1 == "Yes" | Medium | `QRC_Mar_6.1` QRC_Sensitive Targeting Data | IN_PROGRESS |
| **QR.49** | DDQ T1-2 v1 | Q6.2 == "Yes" | Medium | `QRC_Mar_6.2` QRC_Publicity Rights | IN_PROGRESS |
| **QR.50** | DDQ T1-2 v1 | Q6.3 == "No" | Medium | `QRC_Mar_6.3` QRC_No Co-branding Disclosures | IN_PROGRESS |
| **QR.51** | DDQ T1-2 v1 | Q7.2 == "No" | Medium | `QRC_Pcr_7.1` QRC_No Employee Poaching Policy | IN_PROGRESS |
| **QR.52** | DDQ T1-2 v1 | Q7.3 == "No" | Medium | `QRC_Pcr_7.2` QRC_No ESG Policy | IN_PROGRESS |
| **QR.53** | DDQ T1-2 v1 | Q8.1 == "No" | High | `QRC_RR_8.1` QRC_No SLA KPI in Contract | IN_PROGRESS |
| **QR.54** | DDQ T1-2 v1 | Q8.3 == "No" | High | `QRC_RR_8.2` QRC_No Business Continuity Plan | IN_PROGRESS |
| **QR.55** | DDQ T1-2 v1 | Q8.4 == "No" | High | `QRC_RR_8.3` QRC_No Disaster Recovery Plan | IN_PROGRESS |
| **QR.56** | DDQ T1-2 v1 | Submission Event | Task | Assessment Submitted task -> Approvers & All Groups | IN_PROGRESS |
| **QR.57** | DDQ T1-2 v1 | Score < 40 | Task | Low Assessment Score -> VRM Group | IN_PROGRESS |
| **QR.58** | DDQ T1-2 v1 | Scoring Algorithm | Score | Average score over all Yes/No and 0-5, 5-10, 10+ questions | IN_PROGRESS |
| **QR.59** | DDQ T3 v1   | Q1.2 == "No" | High | `QRC_T3_CL_1.1` QRC_T3_Non US Company | IN_PROGRESS |
| **QR.60** | DDQ T3 v1   | Q2.2 == "Yes" | Medium | `QRC_CmL_2.3` QRC_AML Requirement | IN_PROGRESS |
| **QR.61** | DDQ T3 v1   | Q3.3 == "No" | High | `QRC_Fin_3.2` QRC_No Financial Audits | IN_PROGRESS |
| **QR.62** | DDQ T3 v1   | Q4.1 == "No" | High | `QRC_Pri_4.8` QRC_No Privacy Policy | IN_PROGRESS |
| **QR.63** | DDQ T3 v1   | Q4.2 == "No" | High | `QRC_Sec_4.27` QRC_No Information Security Policy | IN_PROGRESS |
| **QR.64** | DDQ T3 v1   | Q4.3 == "No" | High | `QRC_Sec_4.28` QRC_No RM for Information Security | IN_PROGRESS |
| **QR.65** | DDQ T3 v1   | Q4.4 == "No" | High | `QRC_Sec_4.24` QRC_No Encryption Used | IN_PROGRESS |
| **QR.66** | DDQ T3 v1   | Q4.5 == "No" | High | `QRC_Sec_4.35` QRC_No Cyber Insurance | IN_PROGRESS |
| **QR.67** | DDQ T3 v1   | Q5.2 == "No" | High | `QRC_Sec_4.23` QRC_No Notification to Cadence | IN_PROGRESS |
| **QR.68** | DDQ T3 v1   | Q6.1 == "No" | High | `QRC_RR_8.2` QRC_No Business Continuity Plan | IN_PROGRESS |
| **QR.69** | DDQ T3 v1   | Q6.2 == "No" | High | `QRC_RR_8.3` QRC_No Disaster Recovery Plan | IN_PROGRESS |
| **QR.70** | DDQ T3 v1   | Submission Event | Task | Assessment Submitted_T3 task -> Approvers & Groups | IN_PROGRESS |
| **QR.71** | DDQ T3 v1   | Score < 40 | Task | Template score rule_T3 -> VRM Group | IN_PROGRESS |
| **QR.72** | DDQ T3 v1   | Scoring Algorithm | Score | Average score over all Tier 3 Yes/No questions | IN_PROGRESS |
| **QR.73** | DDQ T3 v1   | All required answers favorable | Auto-Approve | Auto-Complete Assessment -> Approved | IN_PROGRESS |
| **QR.74-90**| DDQ T1-2/T3| Section specific risk flagged | Task | Creates Department-specific tasks (Legal, Procurement, Compliance, Finance, Privacy, Data Quality, Security, IT) | IN_PROGRESS |
