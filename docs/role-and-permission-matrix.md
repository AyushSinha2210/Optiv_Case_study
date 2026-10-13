# Role & Permission Matrix: Cadence TPRM Application

**Source Authority:** `Cadence_TPRM_Training.docx` Section 2.3, 4.2, 6.1, Table 5  

---

## 1. Authoritative User Groups & User Rosters

| User Group | Permissions | Role Identifier | Assigned Personnel (from Table 5) | Specific Department Responsibility |
|---|---|---|---|---|
| **Vendor Risk Management Group** | **Admin** | `TPRM_ADMIN` | Daniela Figueroa<br>Bridgett Gatewood<br>KC Burney<br>Jyoti Karwal | Decision-making body. Oversees all workflows, administers risk assessments, issues final approvals or rejections. |
| **Vendor Risk Management Group** | **Edit** | `VRM_REVIEWER` | Tamika Oliver<br>Shimane Smith<br>Chris Schmitz<br>Chris Ott<br>Rob Tilney | Edit access for questionnaire review, triaging operational risks with department reviewers. |
| **Legal Group** | **Edit** | `LEGAL_REVIEWER` | Shimane Smith<br>Daniela Figueroa | Review Contracting & Legal section (Q1.1–Q1.11, complaints policy Q2.5, dispute resolution). |
| **Procurement Group** | **Edit** | `PROCUREMENT_REVIEWER` | Chris Schmitz | Review Procurement section (employee poaching Q7.2, ESG policy Q7.3, supplier diversity). |
| **Finance Group** | **Edit** | `FINANCE_REVIEWER` | Daniela Figueroa | Review Financial statements (Q3.3), audits (Q3.5), Oracle Vendor Onboarding forms (Q3.7 / Q3.5). |
| **IT Group** | **Edit** | `IT_REVIEWER` | Rob Tilney<br>Jyoti Karwal<br>Jonathan Szeto<br>Marc Otani | Review IT Systems & Integration (SSO/SCIM provisioning Q5.6, IT infrastructure integrations). |
| **Compliance Group** | **Edit** | `COMPLIANCE_REVIEWER` | Tamika Oliver | Review Compliance & Legal section (compliance reports Q2.2, strong laws Q2.3, AML requirements Q2.6–Q2.7). |
| **Privacy Group** | **Edit** | `PRIVACY_REVIEWER` | Dayo Seton | Review Privacy section (cross-border data Q4.1, high-risk regions Q4.2, personal data Q4.4, AI/LLM Q4.10–Q4.13, privacy policy Q4.14). |
| **Security Group** | **Edit** | `SECURITY_REVIEWER` | Chris Ott<br>Melisa Cardozo<br>DK Koran<br>Erik Hansen | Review SOC/ISO/PCI certs (Q4.49), IAM (Q4.15), MFA (Q4.18), Pen Tests (Q4.26), Incidents (Q4.30), Encryption (Q4.34), Cyber Insurance (Q4.50). |
| **Data Quality Group** | **Edit** | `DATA_QUALITY_REVIEWER` | Daniela Figueroa | Review vendor metadata consistency, duplicate prevention, attribute accuracy. |

---

## 2. Operation & Capability Permission Matrix

| Capability / API Operation | TPRM Admin | VRM Reviewer | Legal | Procurement | Finance | IT | Compliance | Privacy | Security | Data Quality | Primary Vendor Contact |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Create New Vendor** | Yes | Yes | No | No | No | No | No | No | No | Yes | No |
| **Edit Vendor Attributes** | Yes | Yes | No | No | No | No | No | No | No | Yes | No |
| **Launch Assessment** | Yes | Yes | No | No | No | No | No | No | No | No | No |
| **Fill Questionnaire** | No | No | No | No | No | No | No | No | No | No | **Yes** (Assigned only) |
| **Review Assigned Section** | Yes | Yes | **Yes** (Sec 1) | **Yes** (Sec 7) | **Yes** (Sec 3) | **Yes** (Sec 5) | **Yes** (Sec 2) | **Yes** (Sec 4) | **Yes** (Sec 4) | Yes | No |
| **Log Finding Remediation** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | View Only |
| **Approve Assessment** | **Yes** | No | No | No | No | No | No | No | No | No | No |
| **Reject Assessment** | **Yes** | No | No | No | No | No | No | No | No | No | No |
| **Initiate Offboarding** | Yes | Yes | No | No | No | No | No | No | No | No | No |
| **Execute Reassessment** | Yes | Yes | No | No | No | No | No | No | No | No | No |
| **View Audit Logs** | Yes | Yes | View | View | View | View | View | View | View | View | No |
| **Manage Questionnaire Templates**| Yes | No | No | No | No | No | No | No | No | No | No |
| **System Settings & Integrations**| Yes | No | No | No | No | No | No | No | No | No | No |
