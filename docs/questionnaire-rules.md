# Questionnaire & Risk Engine Rules Specification

**Authority:** `Cadence_TPRM_Training.docx` Section 6.3, Appendices B, C, E, Tables 11, 12, 14  

---

## 1. Questionnaire Templates

### 1.1 `Due Diligence Questionnaire T1-2 v1` (Tier 1 & Tier 2)
8 Sections:
1. **Contracting and Legal:** Corporate structure, state of incorporation, foreign government ownership, operational longevity, subsidiaries, mergers & acquisitions.
2. **Compliance and Legal:** Compliance reports, regulatory legal framework, consumer complaints policies, AML programs, independent AML audits.
3. **Finance:** Audited financial statements, third-party audit reports, Oracle Vendor Onboarding form.
4. **Data Privacy and Security:** Cross-border customer data, high-risk operational regions, personal data categories, sub-processors, AI/LLM interaction with customer data, AI risk management, privacy policies, IAM, least privilege, password complexity, Multi-Factor Authentication (MFA), remote VPN access, network monitoring, vulnerability scanning, environment segregation, penetration testing & remediation, secure software development, incident response plan, 24-month incident disclosure, breach notification timelines, Cadence notification SLA, encryption at rest & in transit, Data Loss Prevention (DLP), data retention, information security policy, background checks, offboarding revoking, BYOD policies, Mobile Device Management (MDM), data deletion guarantees, SOC/ISO/PCI certifications, cyber liability insurance.
5. **IT Systems and Integration:** SSO (SAML/OIDC) & SCIM user provisioning, IT operational integrations.
6. **Marketing:** Sensitive targeting audience data, publicity rights, co-branding disclosures.
7. **Procurement:** Non-solicitation / anti-poaching policies, Environmental, Social, and Governance (ESG) policies.
8. **Resiliency & Business Continuity:** SLA/KPI contractual definitions, Business Continuity Plan (BCP), Disaster Recovery (DR) Plan.

### 1.2 `Due Diligence Questionnaire T3 v1` (Tier 3)
Simplified 6 sections for low-risk vendors:
1. Company Information & US Entity confirmation.
2. Compliance & AML requirements.
3. Financial audit & Oracle vendor intake.
4. Essential privacy, information security policy, encryption, and cyber insurance.
5. Notification commitments to Cadence.
6. Essential Business Continuity & Disaster Recovery plans.

---

## 2. Conditional Show-Logic Rules (Appendix C, Table 12: CL.1 to CL.14)

| Rule ID | Questionnaire | Trigger Question & Answer | Questions Revealed Dynamically |
|---|---|---|---|
| **CL.1** | DDQ T1-2 v1 | Q1.5 == "Yes" | Show Q1.6 (State/place of incorporation, affiliates, foreign government ownership), Q1.7 (Date of incorporation), Q1.8 (Duration in business: 0-5, 5-10, 10+). |
| **CL.2** | DDQ T1-2 v1 | Q2.4 == "Yes" | Show Q2.5 (Copy of policy for handling consumer complaints). |
| **CL.3** | DDQ T1-2 v1 | Q3.6 == "No" | Show Q3.7 (Oracle Vendor Onboarding Form completion link & evidence upload). |
| **CL.4** | DDQ T1-2 v1 | Q4.4 == "Yes" | Show Q4.5 (Cadence data subjects), Q4.6 (Personal data categories). |
| **CL.5** | DDQ T1-2 v1 | Q4.10 == "Yes" | Show Q4.11 (AI customer interaction / sensitive data), Q4.12 (Use of AI/LLMs in data processing), Q4.13 (Processes for AI risk management). |
| **CL.6** | DDQ T1-2 v1 | Q4.18 == "No" | Show Q4.19 (Explanation why MFA is not required / compensating controls). |
| **CL.7** | DDQ T1-2 v1 | Q4.20 == "Yes" | Show Q4.21 (VPN security details & user role access). |
| **CL.8** | DDQ T1-2 v1 | Q4.24 == "Yes" | Show Q4.25 (Separation method: Logical, Physical, VLAN, Cloud tenant). |
| **CL.9** | DDQ T1-2 v1 | Q4.26 == "Yes" | Show Q4.27 (Remediation process & timelines for penetration testing findings). |
| **CL.10** | DDQ T1-2 v1 | Q4.30 == "Yes" | Show Q4.31 (Incident type, remediation actions, timeline, residual risk). |
| **CL.11** | DDQ T1-2 v1 | Q4.34 == "Yes" | Show Q4.35 (Encryption key management & access restriction procedures). |
| **CL.12** | DDQ T1-2 v1 | Q4.36 == "Yes" | Show Q4.37 (DLP scope: End-user devices, email, storage, database, cloud). |
| **CL.13** | DDQ T1-2 v1 | Q8.1 == "Yes" | Show Q8.2 (KPIs or SLAs linked to engagement). |
| **CL.14** | DDQ T3 v1 | Q3.4 == "No" | Show Q3.5 (Oracle Vendor Onboarding Form completion & evidence upload). |

---

## 3. Questionnaire Risk Scoring Rules (Appendix E, Table 14: QR.1 to QR.90)

### 3.1 Tier 1 & Tier 2 Risk Rules (QR.1 to QR.55)
- **QR.1:** Q1.3 == "No" -> Risk: `QRN_Non US Company` (Inherent: High) | Control: `QRC_CL_1.1` `QRC_Non US Company`
- **QR.2:** Q1.8 == "0-5" -> Risk: `QRN_Business duration_less` (Inherent: High) | Control: `QRC_CL_1.2`
- **QR.3:** Q1.8 == "5-10" -> Risk: `QRN_Business duration_medium` (Inherent: Medium) | Control: `QRC_CL_1.3`
- **QR.4:** Q1.9 == "Yes" -> Risk: `QRN_Subsidiaries and Affiliates` (Inherent: Medium) | Control: `QRC_CL_1.4`
- **QR.5:** Q1.11 == "Yes" -> Risk: `QRN_Recent M and A` (Inherent: Medium) | Control: `QRC_CL_1.5`
- **QR.6:** Q2.2 == "No" -> Risk: `QRN_No Compliance Report` (Inherent: High) | Control: `QRC_CmL_2.1`
- **QR.7:** Q2.3 == "No" -> Risk: `QRN_No Strong Laws` (Inherent: Medium) | Control: `QRC_CmL_2.2`
- **QR.8:** Q2.6 == "Yes" -> Risk: `QRN_AML Requirement` (Inherent: Medium) | Control: `QRC_CmL_2.3`
- **QR.9:** Q2.7 == "No" -> Risk: `QRN_No AML Audit` (Inherent: Medium) | Control: `QRC_CmL_2.4`
- **QR.10:** Q3.3 == "No" -> Risk: `QRN_No Financial Statement` (Inherent: High) | Control: `QRC_Fin_3.1`
- **QR.11:** Q3.5 == "No" -> Risk: `QRN_No Financial Audits` (Inherent: High) | Control: `QRC_Fin_3.2`
- **QR.12:** Q4.1 == "Yes" -> Risk: `QRN_Cust_Data Outside US` (Inherent: High) | Control: `QRC_Pri_4.1`
- **QR.13:** Q4.2 == "Yes" -> Risk: `QRN_Operations_Risk Regions` (Inherent: High) | Control: `QRC_Pri_4.2`
- **QR.14:** Q4.4 == "Yes" -> Risk: `QRN_Personal Data Collected` (Inherent: Medium) | Control: `QRC_Pri_4.3`
- **QR.15:** Q4.8 == "Yes" -> Risk: `QRN_Sub-processor Used` (Inherent: Medium) | Control: `QRC_Pri_4.4`
- **QR.16:** Q4.11 == "Yes" -> Risk: `QRN_AI Interaction with Data` (Inherent: Medium) | Control: `QRC_Pri_4.5`
- **QR.17:** Q4.12 == "Yes" -> Risk: `QRN_LLM Use in Data Processing` (Inherent: Medium) | Control: `QRC_Pri_4.6`
- **QR.18:** Q4.13 == "No" -> Risk: `QRN_No RM for AI` (Inherent: Medium) | Control: `QRC_Pri_4.7`
- **QR.19:** Q4.14 == "No" -> Risk: `QRN_No Privacy Policy` (Inherent: High) | Control: `QRC_Pri_4.8`
- **QR.20:** Q4.15 == "No" -> Risk: `QRN_No IAM Policy` (Inherent: High) | Control: `QRC_Sec_4.9`
- **QR.21:** Q4.16 == "No" -> Risk: `QRN_No Least Privilege Access` (Inherent: Medium) | Control: `QRC_Sec_4.10`
- **QR.22:** Q4.17 == "No" -> Risk: `QRN_No Password Policy` (Inherent: Medium) | Control: `QRC_Sec_4.11`
- **QR.23:** Q4.18 == "No" -> Risk: `QRN_No MFA` (Inherent: Medium) | Control: `QRC_Sec_4.12`
- **QR.24:** Q4.20 == "Yes" -> Risk: `QRN_Employee Remote Access` (Inherent: Medium) | Control: `QRC_Sec_4.13`
- **QR.25:** Q4.22 == "No" -> Risk: `QRN_Network Not Monitored` (Inherent: High) | Control: `QRC_Sec_4.14`
- **QR.26:** Q4.23 == "No" -> Risk: `QRN_No Tools for Vulnerability Scan` (Inherent: Medium) | Control: `QRC_Sec_4.15`
- **QR.27:** Q4.24 == "No" -> Risk: `QRN_System Not Segrated` (Inherent: Medium) | Control: `QRC_Sec_4.16`
- **QR.28:** Q4.26 == "No" -> Risk: `QRN_No Pen Test` (Inherent: High) | Control: `QRC_Sec_4.17`
- **QR.29:** Q4.27 == "No" -> Risk: `QRN_No Remediation for Findings` (Inherent: Medium) | Control: `QRC_Sec_4.18`
- **QR.30:** Q4.28 == "No" -> Risk: `QRN_No Security App Dev Policy` (Inherent: Medium) | Control: `QRC_Sec_4.19`
- **QR.31:** Q4.29 == "No" -> Risk: `QRN_No Incident Response Plan` (Inherent: High) | Control: `QRC_Sec_4.20`
- **QR.32:** Q4.30 == "Yes" -> Risk: `QRN_24 Mon Security Incident` (Inherent: High) | Control: `QRC_Sec_4.21`
- **QR.33:** Q4.32 == "No" -> Risk: `QRN_No Breach Notification Process` (Inherent: High) | Control: `QRC_Sec_4.22`
- **QR.34:** Q4.33 == "No" -> Risk: `QRN_No Notification to Cadence` (Inherent: High) | Control: `QRC_Sec_4.23`
- **QR.35:** Q4.34 == "No" -> Risk: `QRN_No Encryption Used` (Inherent: High) | Control: `QRC_Sec_4.24`
- **QR.36:** Q4.36 == "No" -> Risk: `QRN_No Data Loss Prevention` (Inherent: Medium) | Control: `QRC_Sec_4.25`
- **QR.37:** Q4.38 == "No" -> Risk: `QRN_No Data Retention Policy` (Inherent: Medium) | Control: `QRC_Sec_4.26`
- **QR.38:** Q4.39 == "No" -> Risk: `QRN_No Information Security Policy` (Inherent: High) | Control: `QRC_Sec_4.27`
- **QR.39:** Q4.40 == "No" -> Risk: `QRN_No RM for Information Security` (Inherent: High) | Control: `QRC_Sec_4.28`
- **QR.40:** Q4.42 == "No" -> Risk: `QRN_No Background checks for Emp` (Inherent: Medium) | Control: `QRC_Sec_4.29`
- **QR.41:** Q4.44 == "No" -> Risk: `QRN_No Offboarding Process` (Inherent: Medium) | Control: `QRC_Sec_4.30`
- **QR.42:** Q4.45 == "Yes" -> Risk: `QRN_BYOD Allowed` (Inherent: Medium) | Control: `QRC_Sec_4.31`
- **QR.43:** Q4.46 == "No" -> Risk: `QRN_No MDM Policy` (Inherent: Medium) | Control: `QRC_Sec_4.32`
- **QR.44:** Q4.48 == "No" -> Risk: `QRN_No Data Deletion Supported` (Inherent: Medium) | Control: `QRC_Sec_4.33`
- **QR.45:** Q4.49 == "No" -> Risk: `QRN_No Security Certifications` (Inherent: High) | Control: `QRC_Sec_4.34`
- **QR.46:** Q4.50 == "No" -> Risk: `QRN_No Cyber Insurance` (Inherent: High) | Control: `QRC_Sec_4.35`
- **QR.47:** Q5.6 == "No" -> Risk: `QRN_No SSO_SCIM Provisioning` (Inherent: Medium) | Control: `QRC_IT_5.1`
- **QR.48:** Q6.1 == "Yes" -> Risk: `QRN_Sensitive Targeting Data` (Inherent: Medium) | Control: `QRC_Mar_6.1`
- **QR.49:** Q6.2 == "Yes" -> Risk: `QRN_Publicity Rights` (Inherent: Medium) | Control: `QRC_Mar_6.2`
- **QR.50:** Q6.3 == "No" -> Risk: `QRN_No Co-branding Disclosures` (Inherent: Medium) | Control: `QRC_Mar_6.3`
- **QR.51:** Q7.2 == "No" -> Risk: `QRN_No Employee Poaching Policy` (Inherent: Medium) | Control: `QRC_Pcr_7.1`
- **QR.52:** Q7.3 == "No" -> Risk: `QRN_No ESG Policy` (Inherent: Medium) | Control: `QRC_Pcr_7.2`
- **QR.53:** Q8.1 == "No" -> Risk: `QRN_No SLA KPI in Contract` (Inherent: High) | Control: `QRC_RR_8.1`
- **QR.54:** Q8.3 == "No" -> Risk: `QRN_No Business Continuity Plan` (Inherent: High) | Control: `QRC_RR_8.2`
- **QR.55:** Q8.4 == "No" -> Risk: `QRN_No Disaster Recovery Plan` (Inherent: High) | Control: `QRC_RR_8.3`

### 3.2 Submission Tasks, Scoring & Tier 3 Rules (QR.56 to QR.90)
- **QR.56:** Assessment Completed Task -> Assignee: Approvers, Collaborators: All TPRM Groups.
- **QR.57 / QR.58:** Assessment Score < 40% -> Task: `Low Assessment Score` -> Collaborator: `Vendor Risk Management Group`.
- **QR.59:** Q1.2 == "No" -> Risk: `QRN_T3_Non-US Company` (High) | Control: `QRC_T3_CL_1.1`
- **QR.60:** Q2.2 == "Yes" -> Risk: `QRN_T3_AML Requirement` (Medium) | Control: `QRC_CmL_2.3`
- **QR.61:** Q3.3 == "No" -> Risk: `QRN_T3_No Financial Audits` (High) | Control: `QRC_Fin_3.2`
- **QR.62:** Q4.1 == "No" -> Risk: `QRN_T3_No Privacy Policy` (High) | Control: `QRC_Pri_4.8`
- **QR.63:** Q4.2 == "No" -> Risk: `QRN_T3_No Information Security Policy` (High) | Control: `QRC_Sec_4.27`
- **QR.64:** Q4.3 == "No" -> Risk: `QRN_T3_No RM for Information Security` (High) | Control: `QRC_Sec_4.28`
- **QR.65:** Q4.4 == "No" -> Risk: `QRN_T3_No Encryption Used` (High) | Control: `QRC_Sec_4.24`
- **QR.66:** Q4.5 == "No" -> Risk: `QRN_T3_No Cyber Insurance` (High) | Control: `QRC_Sec_4.35`
- **QR.67:** Q5.2 == "No" -> Risk: `QRN_T3_No Notification to Cadence` (High) | Control: `QRC_Sec_4.23`
- **QR.68:** Q6.1 == "No" -> Risk: `QRN_T3_No Business Continuity Plan` (High) | Control: `QRC_RR_8.2`
- **QR.69:** Q6.2 == "No" -> Risk: `QRN_T3_No Disaster Recovery Plan` (High) | Control: `QRC_RR_8.3`
- **QR.70:** Assessment Submitted_T3 Task created.
- **QR.71 / QR.72:** Tier 3 Assessment Score calculation.
- **QR.73:** Auto-Approval rule: If all questions answered favorably -> Auto-Complete Assessment with Approved status.
- **QR.74 to QR.90:** Department-specific risk tasks for Legal, Procurement, Compliance, Finance, Privacy, Data Quality, Security, and IT.
