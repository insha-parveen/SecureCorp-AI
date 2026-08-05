---
document_id: SEC-001
title: Security Audit Report Q1 2026
document_type: audit_report
department: ITSEC
classification: restricted
allowed_roles:
  - manager
  - it
  - admin
allowed_departments:
  - ITSEC
  - OPS
  - ENG
owner_department: ITSEC
document_version: v1
effective_date: 2026-03-30
status: active
created_date: 2026-03-15
last_reviewed_date: 2026-03-30
supersedes_document_version: null
related_documents:
  - ITSEC-001
  - ITSEC-002
  - ITSEC-003
  - ITSEC-005
  - ITSEC-006
  - ENG-001
  - OPS-003
tags:
  - security-audit
  - audit-report
  - compliance
  - risk-assessment
  - ITSEC
source_type: google_drive
---

# Security Audit Report Q1 2026

## 1. Executive Summary
This report presents the findings of the Q1 FY2026 security audit conducted by the IT and Security department at NexaCore Solutions Pvt. Ltd. The audit assessed the effectiveness of the company's information security controls against the requirements of the Information Security Policy (ITSEC-001) and related security policies, and evaluated the security posture of the Project Orion platform (ENG-001).

The audit was conducted from 2026-03-01 to 2026-03-15 by the IT and Security team under the leadership of the CISO, **Rohit Verma**. The audit covered corporate infrastructure, the Project Orion platform, remote access, data handling practices, and third-party integrations.

The overall security posture is rated **Satisfactory**, with 82% of controls assessed as compliant. A total of 3 High, 7 Medium, and 12 Low severity findings were identified. All High severity findings are assigned for remediation with target dates in Q2 FY2026.

## 2. Audit Scope and Objectives

### 2.1 Scope
The audit covered:
- Corporate network and infrastructure.
- Project Orion platform (ENG-001).
- Identity and access management, including MFA compliance (ITSEC-002).
- VPN and remote access controls (ITSEC-008).
- Data classification and handling (ITSEC-006).
- Incident response capability (ITSEC-005).
- Acceptable use monitoring (ITSEC-003).

### 2.2 Objectives
- Assess compliance with the Information Security Policy (ITSEC-001).
- Identify security weaknesses and vulnerabilities.
- Evaluate the effectiveness of security controls.
- Provide recommendations for remediation and improvement.
- Baseline the security posture for ongoing monitoring.

## 3. Audit Methodology
The audit used a combination of control testing and evidence review:
- **Control Testing:** Review of configurations, logs, and access controls.
- **Vulnerability Scanning:** Automated scanning of infrastructure and applications.
- **Policy Compliance Review:** Verification of adherence to security policies.
- **Staff Interviews:** Discussions with engineering, operations, and security personnel.
- **Documentation Review:** Assessment of procedures and runbooks.

## 4. Overall Security Posture

| Area | Compliance Rating |
|---|---|
| Identity and Access Management | 90% |
| Remote Access and VPN | 88% |
| Data Classification | 85% |
| Incident Response | 82% |
| Network Security | 78% |
| Endpoint Security | 76% |
| Third-Party Risk | 75% |
| **Overall** | **82%** |

## 5. Findings by Severity

### 5.1 High Severity Findings

#### Finding H-01: Unused Privileged Accounts
- **Description:** Several privileged accounts associated with former vendors remained active in the cloud environment.
- **Risk:** Unauthorized access through stale credentials.
- **Compliance Gap:** Violates the Password Policy (ITSEC-002) and the Information Security Policy (ITSEC-001).
- **Recommendation:** Remove all inactive privileged accounts and implement automated lifecycle management for vendor accounts.

#### Finding H-02: Unencrypted Backup of Legacy Reporting DB
- **Description:** The backup of the legacy reporting database is stored without encryption at rest.
- **Risk:** Exposure of sensitive data if backup media is compromised.
- **Compliance Gap:** Violates the Data Classification Policy (ITSEC-006) and the Backup & Disaster Recovery Policy (ITSEC-007).
- **Recommendation:** Enable encryption at rest for all backup storage immediately.

#### Finding H-03: Missing MFA on a Third-Party Admin Console
- **Description:** One third-party management console used by a vendor does not enforce MFA.
- **Risk:** Compromised vendor credentials could lead to unauthorized access.
- **Compliance Gap:** Violates the Password Policy (ITSEC-002) MFA enforcement.
- **Recommendation:** Require MFA on the vendor console or restrict access until MFA is enforced.

### 5.2 Medium Severity Findings (Summary)
- **M-01:** Several endpoint devices missing the latest security patches.
- **M-02:** Log retention for some services does not meet the requirements in ITSEC-006.
- **M-03:** VPN access review frequency is not consistent across departments (ITSEC-008).
- **M-04:** Some employees use weak passwords despite the guidance in ITSEC-002.
- **M-05:** Incident response runbooks are not fully updated after the DR exercise (OPS-002).
- **M-06:** Third-party vendor risk assessments are not consistently completed.
- **M-07:** Data classification labels are not applied consistently across all document stores.

### 5.3 Low Severity Findings (Summary)
Low severity findings include minor documentation gaps, inconsistent naming conventions, and non-critical configuration hardening opportunities. These are detailed in the full audit appendix.

## 6. Compliance Assessment Summary

### 6.1 Information Security Policy (ITSEC-001)
Overall compliance with ITSEC-001 is rated Satisfactory. The majority of controls are implemented and operating effectively. Gaps exist primarily in the areas of privileged access management and endpoint patching.

### 6.2 Password Policy (ITSEC-002)
MFA adoption is strong at over 95% across the organization. The primary gaps relate to service account password rotation and the third-party console finding (H-03).

### 6.3 Data Classification Policy (ITSEC-006)
Data classification is generally well implemented, but application of labels across unstructured document stores is inconsistent. Encryption at rest for backups is a critical gap (H-02).

### 6.4 Incident Response Plan (ITSEC-005)
The incident response capability is functioning, as demonstrated by the DR exercise (OPS-002). Runbooks require refresh to incorporate lessons learned.

## 7. Recommendations and Remediation Plan

| # | Finding | Priority | Owner | Target Date |
|---|---|---|---|---|
| 1 | Remove inactive privileged accounts | High | Rohit Verma | 2026-04-15 |
| 2 | Enable backup encryption | High | Sunita Rao | 2026-04-10 |
| 3 | Enforce MFA on vendor console | High | Rohit Verma | 2026-04-20 |
| 4 | Patch endpoint devices | Medium | Sunita Rao | 2026-05-15 |
| 5 | Complete vendor risk assessments | Medium | Rohit Verma | 2026-05-30 |
| 6 | Update incident response runbooks | Medium | Ayesha Khan | 2026-05-15 |
| 7 | Standardize data classification labels | Medium | Sunita Rao | 2026-06-15 |

## 8. Positive Observations
The audit identified several areas of strong performance:
- **MFA Adoption:** Over 95% of accounts have MFA enabled.
- **Security Awareness:** Employees demonstrate good awareness of phishing risks.
- **Monitoring:** The Project Orion observability platform provides comprehensive visibility.
- **DR Readiness:** The DR exercise demonstrated effective recovery capability.
- **Security Ownership:** The CISO and security team demonstrate strong ownership of security initiatives.

## 9. Conclusion
The Q1 FY2026 security audit indicates a generally healthy security posture with key areas for improvement. The High severity findings, particularly around privileged access and backup encryption, require prompt remediation and are being tracked to closure. Continued investment in security awareness, monitoring, and process automation will further strengthen NexaCore's security position.

The findings from this audit will be incorporated into the Quarterly Operations Report (OPS-003) and will inform the ongoing security roadmap aligned with the Information Security Policy (ITSEC-001).

## Detailed Findings

### 1. High Severity Findings Detail

**Finding H-01: Unused Privileged Accounts**
The audit identified 7 privileged accounts associated with former vendors that remained active in the cloud environment. These accounts had not been deprovisioned after the vendor engagements ended. The risk is that these accounts could be used for unauthorized access if the credentials are compromised. The remediation plan includes immediate removal of these accounts and implementation of automated lifecycle management for vendor accounts.

**Finding H-02: Unencrypted Backup of Legacy Reporting DB**
The backup of the legacy reporting database is stored without encryption at rest. This violates the Data Classification Policy (ITSEC-006) and the Backup & Disaster Recovery Policy (ITSEC-007). The backup contains sensitive financial and operational data. The remediation plan includes enabling encryption at rest for all backup storage immediately.

**Finding H-03: Missing MFA on a Third-Party Admin Console**
One third-party management console used by a vendor does not enforce MFA. This violates the Password Policy (ITSEC-002) MFA enforcement requirements. The vendor has been notified, and access will be restricted until MFA is enforced.

### 2. Medium Severity Findings Detail
The medium severity findings include endpoint patching gaps, log retention inconsistencies, VPN access review frequency issues, weak password usage, outdated incident response runbooks, incomplete vendor risk assessments, and inconsistent data classification labels. Each finding has been assigned an owner and a target remediation date.

## 10. Related Documents
- **ITSEC-001 — Information Security Policy**: Audit baseline.
- **ITSEC-002 — Password Policy**: MFA and password compliance.
- **ITSEC-003 — Acceptable Use Policy**: Monitoring practices.
- **ITSEC-005 — Incident Response Plan**: Response capability.
- **ITSEC-006 — Data Classification Policy**: Data handling compliance.
- **ENG-001 — Project Orion Architecture Overview**: Platform security scope.
- **OPS-003 — Quarterly Operations Report**: Operational context.
- **OPS-002 — Disaster Recovery Test Report**: DR findings.

---

## 11. Revision History

| Version | Date | Change Description | Author | Approved By |
|---|---|---|---|---|
| v1 | 2026-03-30 | Initial Release of Security Audit Report Q1 2026 | Rohit Verma | Arvind Malhotra |

---
*End of Document*
