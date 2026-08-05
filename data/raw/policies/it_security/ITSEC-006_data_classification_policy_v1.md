---
document_id: ITSEC-006
title: Data Classification Policy
document_type: policy
department: ITSEC
classification: public
allowed_roles:
  - employee
  - manager
  - hr
  - finance
  - it
  - admin
allowed_departments:
  - "*"
owner_department: ITSEC
document_version: v1
effective_date: 2026-01-15
status: active
created_date: 2025-12-20
last_reviewed_date: 2026-01-15
supersedes_document_version: null
related_documents:
  - ITSEC-001
  - ITSEC-003
  - ITSEC-005
  - ITSEC-007
  - HR-006
  - FIN-001
tags:
  - security
  - data-classification
  - data-handling
  - confidentiality
  - policy
source_type: generated
---

# Data Classification Policy

## 1. Purpose
The purpose of this policy is to establish a standardized framework for classifying data based on its sensitivity and criticality, and to define the handling, storage, transmission, and retention requirements for each classification level. Effective data classification is fundamental to protecting NexaCore Solutions Pvt. Ltd.'s information assets, ensuring that appropriate security controls are applied based on the value and sensitivity of the data, and enabling compliance with contractual and regulatory obligations.

This policy is subordinate to and must be read in conjunction with the Information Security Policy (ITSEC-001), which establishes the overarching security framework for the organization.

## 2. Scope
This policy applies to all data created, received, stored, processed, or transmitted by NexaCore Solutions, regardless of the medium or format. This includes:
- Electronic data stored on company systems, cloud environments, and portable devices.
- Physical documents and records.
- Data transmitted via email, messaging, or other communication channels.
- Data held on behalf of clients as part of consulting and managed services engagements.

The policy applies to all employees, contractors, and third-party partners who handle NexaCore data.

## 3. Data Classification Levels
NexaCore classifies all data into four levels based on its sensitivity and the impact of unauthorized disclosure. These levels align with the authorization model defined in the Company Bible and are used to determine access controls, handling requirements, and retention periods.

### 3.1 Public
**Definition:** Information that is intended for public dissemination or that would cause no harm if disclosed. This data is not sensitive and may be shared freely.

**Examples:**
- Marketing materials and public website content.
- Published press releases.
- Job postings and public company information.

**Handling Requirements:**
- No special handling or access controls required.
- May be shared with external parties without restriction.

### 3.2 Internal
**Definition:** Information that is not intended for public disclosure but would cause limited harm if disclosed within the organization. This data is accessible to all employees on a need-to-know basis.

**Examples:**
- Internal policies and procedures.
- General operational documents.
- Non-sensitive project documentation.
- Internal announcements.

**Handling Requirements:**
- Accessible to all employees.
- Must not be shared with external parties without authorization.
- Standard security controls apply.

### 3.3 Restricted
**Definition:** Information that is sensitive and would cause significant harm to NexaCore, its clients, or its employees if disclosed to unauthorized parties. Access is limited to specific roles or departments.

**Examples:**
- Client data and confidential project information.
- Employee personal data (salary, performance reviews, medical information).
- Financial records and invoices.
- Source code and proprietary intellectual property.
- Security-related information (e.g., vulnerability reports, incident details).

**Handling Requirements:**
- Access limited to authorized personnel on a need-to-know basis.
- Must be encrypted in transit and at rest.
- Must not be stored on personal devices or personal cloud storage.
- Transmission requires secure channels (e.g., encrypted email, secure file transfer).
- Access to Restricted data is governed by the authorization model, which considers role, department, ownership, and manager scope.

### 3.4 Confidential
**Definition:** Information that is highly sensitive and would cause severe or irreparable harm to NexaCore, its clients, or its employees if disclosed. Access is limited to a very narrow scope of named individuals.

**Examples:**
- Board-level strategic plans and merger/acquisition discussions.
- Unannounced financial results.
- Legal documents and privileged communications.
- Client contracts with sensitive commercial terms.
- Credentials and cryptographic keys.

**Handling Requirements:**
- Access limited to explicitly named individuals with a demonstrated need.
- Strong encryption required in transit and at rest.
- Strict access logging and monitoring.
- Physical copies must be stored in locked, access-controlled locations.
- Disposal requires secure destruction (shredding or certified digital deletion).

## 4. Data Classification Responsibilities

### 4.1 Data Owners
Each department head is the Data Owner for data created or managed within their department. Data Owners are responsible for:
- Assigning the initial classification level to data.
- Reviewing and updating classifications as data sensitivity changes.
- Approving access requests for Restricted and Confidential data.
- Ensuring that handling requirements are met.

### 4.2 Data Custodians
The IT and Security department serves as the Data Custodian for most corporate data, responsible for:
- Implementing and enforcing technical controls that align with classification levels.
- Ensuring that data is stored, backed up, and disposed of in accordance with this policy.
- Monitoring access to Restricted and Confidential data.

### 4.3 Data Users
All employees who access or handle data are Data Users and are responsible for:
- Handling data in accordance with its classification level.
- Reporting any suspected data mishandling or security incidents to the IT and Security department.
- Not reclassifying data without authorization from the Data Owner.

## 5. Data Handling Requirements by Classification

| Requirement | Public | Internal | Restricted | Confidential |
|---|---|---|---|---|
| Access Control | None | All employees | Need-to-know | Named individuals |
| Encryption in Transit | Not required | Recommended | Required | Required |
| Encryption at Rest | Not required | Recommended | Required | Required |
| Personal Device Storage | Permitted | Permitted | Prohibited | Prohibited |
| Personal Cloud Storage | Permitted | Prohibited | Prohibited | Prohibited |
| External Sharing | Permitted | With approval | With approval | With approval |
| Retention Period | As needed | As needed | Per policy | Per policy |
| Disposal | Standard | Standard | Secure deletion | Secure destruction |

## 6. Data Retention and Disposal

### 6.1 Retention Periods
Data must be retained for the period required by applicable laws, regulations, and contractual obligations. The HR department manages retention for employee records, and the Finance department manages retention for financial records in accordance with the Procurement Policy (FIN-001) and other applicable requirements.

### 6.2 Disposal
Data that has reached the end of its retention period must be disposed of securely:
- **Physical Documents:** Shredded using cross-cut shredders.
- **Digital Data:** Securely deleted using certified deletion methods that prevent recovery.
- **Storage Media:** Degaussed or physically destroyed when no longer needed.

## 7. Data Classification in Practice

### 7.1 Email and Communication
Employees must consider the classification of data before sending it via email or messaging:
- **Internal data:** May be sent via standard corporate email.
- **Restricted data:** Must be sent using encrypted email or secure file transfer.
- **Confidential data:** Must be sent using approved secure channels with access controls.

### 7.2 Cloud Storage
All corporate data must be stored in company-approved cloud environments. Employees must not use personal cloud services (e.g., personal Dropbox, Google Drive) to store Restricted or Confidential data. Refer to the Acceptable Use Policy (ITSEC-003) for cloud service requirements.

### 7.3 Client Data
Client data is typically classified as Restricted or Confidential, depending on the sensitivity of the data and the terms of the client contract. Employees must comply with all client-specific data handling requirements and must never copy client data to personal devices or personal accounts.

## 8. Data Classification and Incident Response
The classification level of data involved in a Security Incident directly impacts the severity assessment and response. Incidents involving Restricted or Confidential data are typically classified as Medium or High severity and require immediate escalation under the Incident Response Plan (ITSEC-005).

## 9. Training and Awareness
All employees must complete data classification training as part of the mandatory security awareness program. Training covers how to identify classification levels, apply handling requirements, and report suspected data mishandling.

## 10. Enforcement
Failure to comply with this policy may result in disciplinary action, up to and including termination of employment, in accordance with the Code of Conduct (HR-006). Data mishandling that results in a Security Incident will be investigated under the Incident Response Plan (ITSEC-005).

## 11. Related Documents
- **ITSEC-001 — Information Security Policy**: Overarching security framework.
- **ITSEC-003 — Acceptable Use Policy**: Cloud service and data handling requirements.
- **ITSEC-005 — Incident Response Plan**: Incident severity assessment based on data classification.
- **ITSEC-007 — Backup & Disaster Recovery Policy**: Backup and retention requirements.
- **HR-006 — Code of Conduct**: Disciplinary framework for policy violations.
- **FIN-001 — Procurement Policy**: Financial record retention requirements.

---

## 12. Revision History

| Version | Date | Change Description | Author | Approved By |
|---|---|---|---|---|
| v1 | 2026-01-15 | Initial Release of Data Classification Policy | Rohit Verma | Arvind Malhotra |

---
*End of Document*
