# Questionnaire & Risk Engine Rules Specification (Appendix B, C & E)

**Source Authority:** `Cadence_TPRM_Training.docx` Section 6.3, Appendices B, C, E  
**Total Conditional Rules:** 14 (`CL.1` – `CL.14`)  
**Total Questionnaire Risk, Scoring, Auto-Approve & Departmental Task Rules:** 90 (`QR.1` – `QR.90`)  

---

## 1. Conditional Display Rules (Appendix C: CL.1 to CL.14)

| Logic ID | Template | Trigger Question | Operator | Response | Primary Shown | Copy Logic To | Description |
|---|---|---|---|---|---|---|---|
| `CL.1` | `T1-2_v1` | `1.5` | `Equal To` | `Yes` | `1.6` | `1.7, 1.8` | 1.6 Please provide the following: State of Incorporation, Principal Place of Business, Parent Company / Affiliates, Ownership/investment by foreign governments? 1.7 Please provide the date of incorporation. 1.8 How long has your company been in business? |
| `CL.2` | `T1-2_v1` | `2.4` | `Equal To` | `Yes` | `2.5` | `None` | 2.5 Please provide a copy of your policy for handling consumer complaints. |
| `CL.3` | `T1-2_v1` | `3.6` | `Equal To` | `No` | `3.7` | `None` | 3.7 If no, please complete the form here: Oracle Vendor Onboarding Form (link). Please provide the confirmation or upload evidence once completed. |
| `CL.4` | `T1-2_v1` | `4.4` | `Equal To` | `Yes` | `4.5` | `4.6` | 4.5 Select Cadence data subjects. 4.6 Describe (Select) personal data categories. |
| `CL.5` | `T1-2_v1` | `4.10` | `Equal To` | `Yes` | `4.11` | `4.12, 4.13` | 4.11 Will the AI a) interact with Cadence customers, b) have access to customer data (PI), or sensitive employee information. 4.12 Does the organization use AI or large language models in data processing? 4.13 Are there processes established for managing risks related to Artificial Intelligence? |
| `CL.6` | `T1-2_v1` | `4.18` | `Equal To` | `No` | `4.19` | `None` | 4.19 If No - Please explain why MFA is not required (e.g., compensating controls, acceptable risk) |
| `CL.7` | `T1-2_v1` | `4.20` | `Equal To` | `Yes` | `4.21` | `None` | 4.21 If Yes - (a) How is VPN secured? (b) Is access control based on user role or uniform for all users? |
| `CL.8` | `T1-2_v1` | `4.24` | `Equal To` | `Yes` | `4.25` | `None` | 4.25 If Yes - Please describe separation method (Logical, Physical, VLAN, Cloud tenant separation, Other) |
| `CL.9` | `T1-2_v1` | `4.26` | `Equal To` | `Yes` | `4.27` | `None` | 4.27 Do you have a process for remediating critical and high-risk findings from penetration tests, including your defined timelines for remediation and how you communicate updates to clients? |
| `CL.10` | `T1-2_v1` | `4.30` | `Equal To` | `Yes` | `4.31` | `None` | 4.31 If Yes - Please describe: (a) Incident type (b) Remediation actions (c) Timeline (d) Any residual risk or findings post remediation. |
| `CL.11` | `T1-2_v1` | `4.34` | `Equal To` | `Yes` | `4.35` | `None` | 4.35 How do you manage and store encryption keys? (e.g., access restrictions, storage method) |
| `CL.12` | `T1-2_v1` | `4.36` | `Equal To` | `Yes` | `4.37` | `None` | 4.37 If Yes - Indicate scope of DLP (End-user devices, Email, File storage, Database, Cloud apps, Other). |
| `CL.13` | `T1-2_v1` | `8.1` | `Equal To` | `Yes` | `8.2` | `None` | 8.2 What KPIs or SLAs are linked to this engagement? Please provide details. (Note: Appendix C table lists Section as 'Data Privacy and Security' for Question 8.1). |
| `CL.14` | `T3_v1` | `3.4` | `Equal To` | `No` | `3.5` | `None` | 3.5 If No, please complete the form here: Oracle Vendor Onboarding Form (link). Please provide the confirmation or upload evidence once completed. |

---

## 2. Complete 90 Questionnaire Rules (Appendix E: QR.1 to QR.90)

| Rule ID | Template | Rule Name | Trigger Type | Question / Source | Operator | Response | Action | Risk / Task Name | Inherent Risk | Control ID | Control Name | Group / Collaborator |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `QR.1` | `T1-2_v1` | `QR_Non US Company` | `Question` | `1.3` | `Equal To` | `No` | `Create risk` | `QRN_Non US Company` | `High` | `QRC_CL_1.1` | `QRC_Non US Company` | `Legal Group` |
| `QR.2` | `T1-2_v1` | `QR_Business duration_less` | `Question` | `1.8` | `Equal To` | `0-5` | `Create risk` | `QRN_Business duration_less` | `High` | `QRC_CL_1.2` | `QRC_ Business duration_less` | `Legal Group` |
| `QR.3` | `T1-2_v1` | `QR_Business duration_medium` | `Question` | `1.8` | `Equal To` | `5-10` | `Create risk` | `QRN_Business duration_medium` | `Medium` | `QRC_CL_1.3` | `QRC_ Business duration_medium` | `Legal Group` |
| `QR.4` | `T1-2_v1` | `QR_Subsidiaries and Affiliates` | `Question` | `1.9` | `Equal To` | `Yes` | `Create risk` | `QRN_Subsidiaries and Affiliates` | `Medium` | `QRC_CL_1.4` | `QRC_Subsidiaries and Affiliates` | `Legal Group` |
| `QR.5` | `T1-2_v1` | `QR_Recent M and A` | `Question` | `1.11` | `Equal To` | `Yes` | `Create risk` | `QRN_Recent M and A` | `Medium` | `QRC_CL_1.5` | `QRC_Recent M and A` | `Legal Group` |
| `QR.6` | `T1-2_v1` | `QR_No Compliance Report` | `Question` | `2.2` | `Equal To` | `No` | `Create risk` | `QRN_No Compliance Report` | `High` | `QRC_CmL_2.1` | `QRC_No Compliance Report` | `Compliance Group` |
| `QR.7` | `T1-2_v1` | `QR_No Strong Laws` | `Question` | `2.3` | `Equal To` | `No` | `Create risk` | `QRN_No Strong Laws` | `Medium` | `QRC_CmL_2.2` | `QRC_No Strong Laws` | `Compliance Group` |
| `QR.8` | `T1-2_v1` | `QR_AML Requirement` | `Question` | `2.6` | `Equal To` | `Yes` | `Create risk` | `QRN_AML Requirement` | `Medium` | `QRC_CmL_2.3` | `QRC_AML Requirement` | `Compliance Group` |
| `QR.9` | `T1-2_v1` | `QR_No AML Audit` | `Question` | `2.7` | `Equal To` | `No` | `Create risk` | `QRN_No AML Audit` | `Medium` | `QRC_CmL_2.4` | `QRC_No AML Audit` | `Compliance Group` |
| `QR.10` | `T1-2_v1` | `QR_No Financial Statement` | `Question` | `3.3` | `Equal To` | `No` | `Create risk` | `QRN_No Financial Statement` | `High` | `QRC_Fin_3.1` | `QRC_No Financial Statement` | `Finance Group` |
| `QR.11` | `T1-2_v1` | `QR_No Financial Audits` | `Question` | `3.5` | `Equal To` | `No` | `Create risk` | `QRN_No Financial Audits` | `High` | `QRC_Fin_3.2` | `QRC_No Financial Audits` | `Finance Group` |
| `QR.12` | `T1-2_v1` | `QR_Cust_Data Outside US` | `Question` | `4.1` | `Equal To` | `Yes` | `Create risk` | `QRN_Cust_Data Outside US` | `High` | `QRC_Pri_4.1` | `QRC_Cust_Data Outside US` | `Privacy Group` |
| `QR.13` | `T1-2_v1` | `QR_Operations_Risk Regions` | `Question` | `4.2` | `Equal To` | `Yes` | `Create risk` | `QRN_Operations_Risk Regions` | `High` | `QRC_Pri_4.2` | `QRC_Operations_Risk Regions` | `Privacy Group` |
| `QR.14` | `T1-2_v1` | `QR_Personal Data Collected` | `Question` | `4.4` | `Equal To` | `Yes` | `Create risk` | `QRN_Personal Data Collected` | `Medium` | `QRC_Pri_4.3` | `QRC_Personal Data Collected` | `Privacy Group` |
| `QR.15` | `T1-2_v1` | `QR_Sub-processor Used` | `Question` | `4.8` | `Equal To` | `Yes` | `Create risk` | `QRN_Sub-processor Used` | `Medium` | `QRC_Pri_4.4` | `QRC_Sub-processor Used` | `Privacy Group` |
| `QR.16` | `T1-2_v1` | `QR_AI Interaction with Data` | `Question` | `4.11` | `Equal To` | `Yes` | `Create risk` | `QRN_AI Interaction with Data` | `Medium` | `QRC_Pri_4.5` | `QRC_AI Interaction with Data` | `Privacy Group` |
| `QR.17` | `T1-2_v1` | `QR_LLM Use in Data Processing` | `Question` | `4.12` | `Equal To` | `Yes` | `Create risk` | `QRN_LLM Use in Data Processing` | `Medium` | `QRC_Pri_4.6` | `QRC_LLM Use in Data Processing` | `Privacy Group` |
| `QR.18` | `T1-2_v1` | `QR_No RM for AI` | `Question` | `4.13` | `Equal To` | `No` | `Create risk` | `QRN_No RM for AI` | `Medium` | `QRC_Pri_4.7` | `QRC_No RM for AI` | `Privacy Group` |
| `QR.19` | `T1-2_v1` | `QR_No Privacy Policy` | `Question` | `4.14` | `Equal To` | `No` | `Create risk` | `QRN_No Privacy Policy` | `High` | `QRC_Pri_4.8` | `QRC_No Privacy Policy` | `Privacy Group` |
| `QR.20` | `T1-2_v1` | `QR_No IAM Policy` | `Question` | `4.15` | `Equal To` | `No` | `Create risk` | `QRN_No IAM Policy` | `High` | `QRC_Sec_4.9` | `QRC_No IAM Policy` | `Security Group` |
| `QR.21` | `T1-2_v1` | `QR_No Least Privilege Access` | `Question` | `4.16` | `Equal To` | `No` | `Create risk` | `QRN_No Least Privilege Access` | `Medium` | `QRC_Sec_4.10` | `QRC_No Least Privilege Access` | `Security Group` |
| `QR.22` | `T1-2_v1` | `QR_No Password Policy` | `Question` | `4.17` | `Equal To` | `No` | `Create risk` | `QRN_No Password Policy` | `Medium` | `QRC_Sec_4.11` | `QRC_No Password Policy` | `Security Group` |
| `QR.23` | `T1-2_v1` | `QR_No MFA` | `Question` | `4.18` | `Equal To` | `No` | `Create risk` | `QRN_No MFA` | `Medium` | `QRC_Sec_4.12` | `QRC_No MFA` | `Security Group` |
| `QR.24` | `T1-2_v1` | `QR_Employee Remote Access` | `Question` | `4.20` | `Equal To` | `Yes` | `Create risk` | `QRN_Employee Remote Access` | `Medium` | `QRC_Sec_4.13` | `QRC_Employee Remote Access` | `Security Group` |
| `QR.25` | `T1-2_v1` | `QR_Network Not Monitored` | `Question` | `4.22` | `Equal To` | `No` | `Create risk` | `QRN_Network Not Monitored` | `High` | `QRC_Sec_4.14` | `QRC_Network Not Monitored` | `Security Group` |
| `QR.26` | `T1-2_v1` | `QR_No Tools for Vulnerability Scan` | `Question` | `4.23` | `Equal To` | `No` | `Create risk` | `QRN_No Tools for Vulnerability Scan` | `Medium` | `QRC_Sec_4.15` | `QRC_No Tools for Vulnerability Scan` | `Security Group` |
| `QR.27` | `T1-2_v1` | `QR_System Not Segrated` | `Question` | `4.24` | `Equal To` | `No` | `Create risk` | `QRN_System Not Segrated` | `Medium` | `QRC_Sec_4.16` | `QRC_System Not Segrated` | `Security Group` |
| `QR.28` | `T1-2_v1` | `QR_No Pen Test` | `Question` | `4.26` | `Equal To` | `No` | `Create risk` | `QRN_No Pen Test` | `High` | `QRC_Sec_4.17` | `QRC_No Pen Test` | `Security Group` |
| `QR.29` | `T1-2_v1` | `QR_No Remediation for Findings` | `Question` | `4.27` | `Equal To` | `No` | `Create risk` | `QRN_No Remediation for Findings` | `Medium` | `QRC_Sec_4.18` | `QRC_No Remediation for Findings` | `Security Group` |
| `QR.30` | `T1-2_v1` | `QR_No Security App Dev Policy` | `Question` | `4.28` | `Equal To` | `No` | `Create risk` | `QRN_No Security App Dev Policy` | `Medium` | `QRC_Sec_4.19` | `QRC_No Security App Dev Policy` | `Security Group` |
| `QR.31` | `T1-2_v1` | `QR_No Incident Response Plan` | `Question` | `4.29` | `Equal To` | `No` | `Create risk` | `QRN_No Incident Response Plan` | `High` | `QRC_Sec_4.20` | `QRC_No Incident Response Plan` | `Security Group` |
| `QR.32` | `T1-2_v1` | `QR_24 Mon Security Incident` | `Question` | `4.30` | `Equal To` | `Yes` | `Create risk` | `QRN_24 Mon Security Incident` | `High` | `QRC_Sec_4.21` | `QRC_24 Mon Security Incident` | `Security Group` |
| `QR.33` | `T1-2_v1` | `QR_No Breach Notification Process` | `Question` | `4.32` | `Equal To` | `No` | `Create risk` | `QRN_No Breach Notification Process` | `High` | `QRC_Sec_4.22` | `QRC_No Breach Notification Process` | `Security Group` |
| `QR.34` | `T1-2_v1` | `QR_No Notification to Cadence` | `Question` | `4.33` | `Equal To` | `No` | `Create risk` | `QRN_No Notification to Cadence` | `High` | `QRC_Sec_4.23` | `QRC_No Notification to Cadence` | `Security Group` |
| `QR.35` | `T1-2_v1` | `QR_No Encryption Used` | `Question` | `4.34` | `Equal To` | `No` | `Create risk` | `QRN_No Encryption Used` | `High` | `QRC_Sec_4.24` | `QRC_No Encryption Used` | `Security Group` |
| `QR.36` | `T1-2_v1` | `QR_No Data Loss Prevention` | `Question` | `4.36` | `Equal To` | `No` | `Create risk` | `QRN_No Data Loss Prevention` | `Medium` | `QRC_Sec_4.25` | `QRC_No Data Loss Prevention` | `Security Group` |
| `QR.37` | `T1-2_v1` | `QR_No Data Retention Policy` | `Question` | `4.38` | `Equal To` | `No` | `Create risk` | `QRN_No Data Retention Policy` | `Medium` | `QRC_Sec_4.26` | `QRC_No Data Retention Policy` | `Security Group` |
| `QR.38` | `T1-2_v1` | `QR_No Information Security Policy` | `Question` | `4.39` | `Equal To` | `No` | `Create risk` | `QRN_No Information Security Policy` | `High` | `QRC_Sec_4.27` | `QRC_No Information Security Policy` | `Security Group` |
| `QR.39` | `T1-2_v1` | `QR_No RM for Information Security` | `Question` | `4.40` | `Equal To` | `No` | `Create risk` | `QRN_No RM for Information Security` | `High` | `QRC_Sec_4.28` | `QRC_No RM for Information Security` | `Security Group` |
| `QR.40` | `T1-2_v1` | `QR_No Background checks for Emp` | `Question` | `4.42` | `Equal To` | `No` | `Create risk` | `QRN_No Background checks for Emp` | `Medium` | `QRC_Sec_4.29` | `QRC_No Background checks for Emp` | `Security Group` |
| `QR.41` | `T1-2_v1` | `QR_No Offboarding Process` | `Question` | `4.44` | `Equal To` | `No` | `Create risk` | `QRN_No Offboarding Process` | `Medium` | `QRC_Sec_4.30` | `QRC_No Offboarding Process` | `Security Group` |
| `QR.42` | `T1-2_v1` | `QR_BYOD Allowed` | `Question` | `4.45` | `Equal To` | `Yes` | `Create risk` | `QRN_BYOD Allowed` | `Medium` | `QRC_Sec_4.31` | `QRC_BYOD Allowed` | `Security Group` |
| `QR.43` | `T1-2_v1` | `QR_No MDM Policy` | `Question` | `4.46` | `Equal To` | `No` | `Create risk` | `QRN_No MDM Policy` | `Medium` | `QRC_Sec_4.32` | `QRC_No MDM Policy` | `Security Group` |
| `QR.44` | `T1-2_v1` | `QR_No Data Deletion Supported` | `Question` | `4.48` | `Equal To` | `No` | `Create risk` | `QRN_No Data Deletion Supported` | `Medium` | `QRC_Sec_4.33` | `QRC_No Data Deletion Supported` | `Security Group` |
| `QR.45` | `T1-2_v1` | `QR_No Security Certifications` | `Question` | `4.49` | `Equal To` | `No` | `Create risk` | `QRN_No Security Certifications` | `High` | `QRC_Sec_4.34` | `QRC_No Security Certifications` | `Security Group` |
| `QR.46` | `T1-2_v1` | `QR_No Cyber Insurance` | `Question` | `4.50` | `Equal To` | `No` | `Create risk` | `QRN_No Cyber Insurance` | `High` | `QRC_Sec_4.35` | `QRC_No Cyber Insurance` | `Security Group` |
| `QR.47` | `T1-2_v1` | `QR_No SSO_SCIM Provisioning` | `Question` | `5.6` | `Equal To` | `No` | `Create risk` | `QRN_No SSO_SCIM Provisioning` | `Medium` | `QRC_IT_5.1` | `QRC_No SSO_SCIM Provisioning` | `IT Group` |
| `QR.48` | `T1-2_v1` | `QR_Sensitive Targeting Data` | `Question` | `6.1` | `Equal To` | `Yes` | `Create risk` | `QRN_Sensitive Targeting Data` | `Medium` | `QRC_Mar_6.1` | `QRC_Sensitive Targeting Data` | `Legal Group` |
| `QR.49` | `T1-2_v1` | `QR_Publicity Rights` | `Question` | `6.2` | `Equal To` | `Yes` | `Create risk` | `QRN_Publicity Rights` | `Medium` | `QRC_Mar_6.2` | `QRC_Publicity Rights` | `Legal Group` |
| `QR.50` | `T1-2_v1` | `QR_No Co-branding Disclosures` | `Question` | `6.3` | `Equal To` | `No` | `Create risk` | `QRN_No Co-branding Disclosures` | `Medium` | `QRC_Mar_6.3` | `QRC_No Co-branding Disclosures` | `Legal Group` |
| `QR.51` | `T1-2_v1` | `QR_No Employee Poaching Policy` | `Question` | `7.2` | `Equal To` | `No` | `Create risk` | `QRN_No Employee Poaching Policy` | `Medium` | `QRC_Pcr_7.1` | `QRC_No Employee Poaching Policy` | `Procurement Group` |
| `QR.52` | `T1-2_v1` | `QR_No ESG Policy` | `Question` | `7.3` | `Equal To` | `No` | `Create risk` | `QRN_No ESG Policy` | `Medium` | `QRC_Pcr_7.2` | `QRC_No ESG Policy` | `Procurement Group` |
| `QR.53` | `T1-2_v1` | `QR_No SLA KPI in Contract` | `Question` | `8.1` | `Equal To` | `No` | `Create risk` | `QRN_No SLA KPI in Contract` | `High` | `QRC_RR_8.1` | `QRC_No SLA KPI in Contract` | `Compliance Group` |
| `QR.54` | `T1-2_v1` | `QR_No Business Continuity Plan` | `Question` | `8.3` | `Equal To` | `No` | `Create risk` | `QRN_No Business Continuity Plan` | `High` | `QRC_RR_8.2` | `QRC_No Business Continuity Plan` | `Security Group` |
| `QR.55` | `T1-2_v1` | `QR_No Disaster Recovery Plan` | `Question` | `8.4` | `Equal To` | `No` | `Create risk` | `QRN_No Disaster Recovery Plan` | `High` | `QRC_RR_8.3` | `QRC_No Disaster Recovery Plan` | `Security Group` |
| `QR.56` | `T1-2_v1` | `QR_Task Assessment Completed` | `Question` | `1.3 OR 4.50` | `Contains Any` | `Yes and No` | `Create task upon submission` | `Assessment Submitted` | `—` | `—` | `—` | `ALL TPRM Groups` |
| `QR.57` | `T1-2_v1` | `QR_Template score rule` | `Assessment Score` | `Tier 1 and 2 assessment scoring` | `Less than` | `40` | `Create task upon submission` | `Low Assessment Score` | `—` | `—` | `—` | `TPRM_Vendor Risk Management Team` |
| `QR.58` | `T1-2_v1` | `Tier1 and 2 assessment scoring` | `Scoring` | `ALL Yes and No and one Options based (0-5,5-10 and 10+)` | `Average` | `Average` | `Scoring Type: Average` | `Average` | `—` | `—` | `—` | `Vendor Risk Management Group` |
| `QR.59` | `T3_v1` | `QR_T3_Non-US Company` | `Question` | `1.2` | `Equal To` | `No` | `Create risk` | `QRN_T3_ Non-US Company` | `High` | `QRC_T3_CL_1.1` | `QRC_T3_Non US Company` | `Legal Group` |
| `QR.60` | `T3_v1` | `QR_T3_AML Requirement` | `Question` | `2.2` | `Equal To` | `Yes` | `Create risk` | `QRN_T3_AML Requirement` | `Medium` | `QRC_CmL_2.3` | `QRC_AML Requirement` | `Compliance Group` |
| `QR.61` | `T3_v1` | `QR_T3_No Financial Audits` | `Question` | `3.3` | `Equal To` | `No` | `Create risk` | `QRN_T3_No Financial Audits` | `High` | `QRC_Fin_3.2` | `QRC_No Financial Audits` | `Finance Group` |
| `QR.62` | `T3_v1` | `QR_T3_No Privacy Policy` | `Question` | `4.1` | `Equal To` | `No` | `Create risk` | `QRN_T3_No Privacy Policy` | `High` | `QRC_Pri_4.8` | `QRC_No Privacy Policy` | `Privacy Group` |
| `QR.63` | `T3_v1` | `QR_T3_No Information Security Policy` | `Question` | `4.2` | `Equal To` | `No` | `Create risk` | `QRN_T3_No Information Security Policy` | `High` | `QRC_Sec_4.27` | `QRC_No Information Security Policy` | `Security Group` |
| `QR.64` | `T3_v1` | `QR_T3_No RM for Information Security` | `Question` | `4.3` | `Equal To` | `No` | `Create risk` | `QRN_T3_No RM for Information Security` | `High` | `QRC_Sec_4.28` | `QRC_No RM for Information Security` | `Security Group` |
| `QR.65` | `T3_v1` | `QR_T3_No Encryption Used` | `Question` | `4.4` | `Equal To` | `No` | `Create risk` | `QRN_T3_No Encryption Used` | `High` | `QRC_Sec_4.24` | `QRC_No Encryption Used` | `Security Group` |
| `QR.66` | `T3_v1` | `QR_T3_No Cyber Insurance` | `Question` | `4.5` | `Equal To` | `No` | `Create risk` | `QRN_T3_No Cyber Insurance` | `High` | `QRC_Sec_4.35` | `QRC_No Cyber Insurance` | `Security Group` |
| `QR.67` | `T3_v1` | `QR_T3_No Notification to Cadence` | `Question` | `5.2` | `Equal To` | `No` | `Create risk` | `QRN_T3_No Notification to Cadence` | `High` | `QRC_Sec_4.23` | `QRC_No Notification to Cadence` | `Security Group` |
| `QR.68` | `T3_v1` | `QR_T3_No Business Continuity Plan` | `Question` | `6.1` | `Equal To` | `No` | `Create risk` | `QRN_T3_No Business Continuity Plan` | `High` | `QRC_RR_8.2` | `QRC_No Business Continuity Plan` | `Security Group` |
| `QR.69` | `T3_v1` | `QR_T3_No Disaster Recovery Plan` | `Question` | `6.2` | `Equal To` | `No` | `Create risk` | `QRN_T3_No Disaster Recovery Plan` | `High` | `QRC_RR_8.3` | `QRC_No Disaster Recovery Plan` | `Security Group` |
| `QR.70` | `T3_v1` | `QR_T3_Task Assessment Completed` | `Question` | `1.2 OR 4.5` | `Contains Any` | `Yes and No` | `Create task upon submission` | `Assessment Submitted_T3` | `—` | `—` | `—` | `ALL TPRM Groups` |
| `QR.71` | `T3_v1` | `QR_T3_Template score rule` | `Assessment Score` | `Tier 1 and 2 assessment scoring` | `Less than` | `40` | `Create task upon submission` | `Template score rule_T3` | `—` | `—` | `—` | `TPRM_Vendor Risk Management Team` |
| `QR.72` | `T3_v1` | `Tier 3 assessment scoring` | `Scoring` | `ALL Yes and No questions` | `Average` | `Average` | `Scoring Type: Average` | `Average` | `—` | `—` | `—` | `Vendor Risk Management Group` |
| `QR.73` | `T3_v1` | `QR_T3_Auto Approve` | `Question` | `All required questions` | `Equal To` | `Yes / No` | `Auto-Complete Assessment Upon Submission` | `The third-party is Approved` | `—` | `—` | `—` | `Vendor Risk Management Group` |
| `QR.74` | `T1-2_v1` | `QR_Task Legal Risk` | `Question` | `Added as per requirement (Section 1: 1.3, 1.8, 1.9, 1.11)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Legal Risk Identified for Third-Party` | `—` | `—` | `—` | `TPRM_Legal Group` |
| `QR.75` | `T1-2_v1` | `QR_Task Procurement Risk` | `Question` | `Added as per requirement (Section 7: 7.2, 7.3)` | `Equal to, Contains Any` | `Yes and No, Options` | `Create task upon submission` | `Procurement Risk Identified for Third-Party` | `—` | `—` | `—` | `TPRM_Procurement Group` |
| `QR.76` | `T1-2_v1` | `QR_Task Compliance Risk` | `Question` | `Added as per requirement (Section 2: 2.2, 2.3, 2.6, 2.7)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Compliance Risk Identified for Third-Party` | `—` | `—` | `—` | `TPRM_Compliance Group` |
| `QR.77` | `T1-2_v1` | `QR_Task Finance Risk` | `Question` | `Added as per requirement (Section 3: 3.3, 3.5)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Finance Risk Identified for Third-Party` | `—` | `—` | `—` | `TPRM_Finance Group` |
| `QR.78` | `T1-2_v1` | `QR_Task Privacy Risk` | `Question` | `Added as per requirement (Section 4 Privacy: 4.1-4.14)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Privacy Risk Identified for Third-Party` | `—` | `—` | `—` | `TPRM_Privacy Group` |
| `QR.79` | `T1-2_v1` | `QR_Task Data Quality Risk` | `Question` | `Added as per requirement (Data Quality / Marketing: 6.1, 6.2, 6.3)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Data Quality Risk Identified for Third-Party` | `—` | `—` | `—` | `TPRM_Data Quality Group` |
| `QR.80` | `T1-2_v1` | `QR_Task Security Risk` | `Question` | `Added as per requirement (Section 4 Security: 4.15-4.50, 8.3, 8.4)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Security Risk Identified for Third-Party` | `—` | `—` | `—` | `TPRM_Security Group` |
| `QR.81` | `T1-2_v1` | `QR_Task IT Risk` | `Question` | `5.6` | `Equal to` | `No` | `Create task upon submission` | `IT Risk Identified for Third-Party` | `—` | `—` | `—` | `TPRM_IT Group` |
| `QR.82` | `T1-2_v1` | `QR_Task IT Requirement` | `Question` | `5.1` | `Equal to` | `Yes` | `Create task upon submission` | `IT Requirement Identified for Third-Party` | `—` | `—` | `—` | `TPRM_IT Group` |
| `QR.83` | `T3_v1` | `QR_T3_Task Legal Risk` | `Question` | `Added as per requirement (Section 1: 1.2)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Legal Risk Identified for Third-Party_T3` | `—` | `—` | `—` | `TPRM_Legal Group` |
| `QR.84` | `T3_v1` | `QR_T3_Task Procurement Risk` | `Question` | `Added as per requirement` | `Equal to` | `Yes and No, Options` | `Create task upon submission` | `Procurement Risk Identified for Third-Party_T3` | `—` | `—` | `—` | `TPRM_Procurement Group` |
| `QR.85` | `T3_v1` | `QR_T3_Task Compliance Risk` | `Question` | `Added as per requirement (Section 2: 2.2)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Compliance Risk Identified for Third-Party_T3` | `—` | `—` | `—` | `TPRM_Compliance Group` |
| `QR.86` | `T3_v1` | `QR_T3_Task Finance Risk` | `Question` | `Added as per requirement (Section 3: 3.3, 3.4)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Finance Risk Identified for Third-Party_T3` | `—` | `—` | `—` | `TPRM_Finance Group` |
| `QR.87` | `T3_v1` | `QR_T3_Task Privacy Risk` | `Question` | `Added as per requirement (Section 4: 4.1)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Privacy Risk Identified for Third-Party_T3` | `—` | `—` | `—` | `TPRM_Privacy Group` |
| `QR.88` | `T3_v1` | `QR_T3_Task Security Risk` | `Question` | `Added as per requirement (Section 4-6: 4.2-4.5, 5.2, 6.1, 6.2)` | `Equal to` | `Yes and No` | `Create task upon submission` | `Security Risk Identified for Third-Party_T3` | `—` | `—` | `—` | `TPRM_Security Group` |
| `QR.89` | `T3_v1` | `QR_T3_Task IT Requirement` | `Question` | `5.1` | `Equal to` | `Yes` | `Create task upon submission` | `IT Requirement Identified for Third-Party_T3` | `—` | `—` | `—` | `TPRM_IT Group` |
| `QR.90` | `T3_v1` | `QR_Task IT Risk` | `Question` | `Added as per requirement (5.2)` | `Equal to` | `Yes and No` | `Create task upon submission` | `IT Risk Identified for Third-Party_T3` | `—` | `—` | `—` | `TPRM_IT Group` |
