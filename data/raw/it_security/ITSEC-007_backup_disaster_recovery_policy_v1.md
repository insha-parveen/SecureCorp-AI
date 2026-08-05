---
document_id: ITSEC-007
title: Backup & Disaster Recovery Policy
document_type: policy
department: ITSEC
classification: department_internal
allowed_roles:
  - manager
  - it
  - admin
allowed_departments:
  - ITSEC
  - OPS
owner_department: ITSEC
document_version: v1
effective_date: 2026-01-15
status: active
created_date: 2025-12-20
last_reviewed_date: 2026-01-15
supersedes_document_version: null
related_documents:
  - ITSEC-001
  - ITSEC-005
  - ITSEC-006
  - FIN-001
tags:
  - security
  - backup
  - disaster-recovery
  - business-continuity
  - policy
source_type: generated
---

# Backup & Disaster Recovery Policy

## 1. Purpose
The purpose of this policy is to establish the framework for backing up NexaCore Solutions Pvt. Ltd.'s critical data and systems, and to define the procedures for recovering operations in the event of a disaster or significant disruption. Data loss can result from a wide range of events, including hardware failures, cyberattacks such as ransomware, natural disasters, human error, and software bugs. A robust backup and disaster recovery capability ensures that NexaCore can restore critical data and resume operations with minimal downtime, protecting the company's business continuity, client commitments, and regulatory compliance.

This policy is subordinate to and must be read in conjunction with the Information Security Policy (ITSEC-001), which establishes the overarching security framework for the organization.

## 2. Scope
This policy applies to all critical data and systems owned or managed by NexaCore Solutions, including:
- Corporate data stored on servers, cloud environments, and endpoints.
- Client data held as part of consulting and managed services engagements.
- Source code and development environments.
- Financial records and invoices.
- Employee records and HR data.
- Email and collaboration data.

The policy applies to all departments and locations, including Lucknow, Bengaluru, Dubai, and Singapore.

## 3. Roles and Responsibilities

### 3.1 IT and Security Department
The IT and Security department, under the leadership of the CISO, **Rohit Verma**, is responsible for:
- Designing, implementing, and maintaining backup and recovery solutions.
- Monitoring backup jobs and verifying their success.
- Conducting regular recovery testing.
- Coordinating disaster recovery activities.

### 3.2 Data Owners
Department heads are responsible for:
- Identifying and classifying the data within their department (refer to the Data Classification Policy, ITSEC-006).
- Confirming that all critical data is included in backup schedules.
- Prioritizing recovery of their department's systems and data.

### 3.3 Operations Department
The Operations department, under the leadership of **Ayesha Khan**, is responsible for:
- Coordinating business continuity activities during a disaster.
- Communicating with employees, clients, and stakeholders during a disruption.
- Ensuring that operational processes can continue during recovery.

## 4. Backup Requirements

### 4.1 Backup Frequency
Backup frequency is determined by the criticality and change rate of the data:

| Data Type | Backup Frequency | Retention Period |
|---|---|---|
| Critical databases | Daily full backup + continuous transaction log | 30 days |
| Source code repositories | Continuous (on commit) | 12 months |
| Email and collaboration data | Daily | 12 months |
| Financial records | Daily | 7 years (per FIN-001) |
| Employee records | Daily | Per HR retention policy |
| File shares and documents | Daily incremental, weekly full | 90 days |
| Client project data | Daily | Per client contract |

### 4.2 Backup Types
NexaCore uses a combination of backup types to balance storage efficiency and recovery speed:
- **Full Backups:** Complete copies of all data, performed weekly.
- **Incremental Backups:** Copies of changes since the last backup, performed daily.
- **Transaction Log Backups:** Continuous capture of database transactions for point-in-time recovery.

### 4.3 Backup Storage
Backups must be stored in a manner that protects them from the same threats that could affect the primary data:
- **Offsite Storage:** At least one copy of critical backups must be stored offsite, either in a different geographic region or in a separate cloud availability zone.
- **Immutable Backups:** Critical backups must be stored in an immutable format that cannot be modified or deleted, protecting them from ransomware attacks.
- **Encryption:** All backups must be encrypted at rest and in transit, in accordance with the Data Classification Policy (ITSEC-006).

## 5. Recovery Objectives

### 5.1 Recovery Time Objective (RTO)
The RTO is the maximum acceptable time to restore a system or data after a disruption. NexaCore's target RTOs are:

| System Tier | RTO |
|---|---|
| Tier 1 (Critical systems, client-facing) | 4 hours |
| Tier 2 (Important systems) | 24 hours |
| Tier 3 (Non-critical systems) | 72 hours |

### 5.2 Recovery Point Objective (RPO)
The RPO is the maximum acceptable amount of data loss measured in time. NexaCore's target RPOs are:

| System Tier | RPO |
|---|---|
| Tier 1 (Critical databases) | 15 minutes |
| Tier 2 (Important systems) | 24 hours |
| Tier 3 (Non-critical systems) | 48 hours |

## 6. Backup Monitoring and Verification

### 6.1 Monitoring
All backup jobs must be monitored to ensure they complete successfully. The IT and Security team reviews backup logs daily and investigates any failed or incomplete backups immediately.

### 6.2 Recovery Testing
Backups are only valuable if they can be restored successfully. The IT and Security department conducts:
- **Quarterly Recovery Tests:** Full restoration of a sample of systems to verify backup integrity.
- **Annual Disaster Recovery Exercise:** A comprehensive test of the disaster recovery plan, including failover to alternate infrastructure.

### 6.3 Test Documentation
All recovery tests are documented, including the systems tested, the success or failure of the restoration, and any corrective actions taken.

## 7. Disaster Recovery Plan

### 7.1 Disaster Declaration
A disaster is declared when a disruption exceeds the RTO for critical systems or when the primary infrastructure is deemed unrecoverable. The CISO, in coordination with the Head of Operations, **Ayesha Khan**, declares a disaster and activates the disaster recovery plan.

### 7.2 Recovery Procedures
The disaster recovery plan includes:
- **Activation:** Notification of the disaster recovery team and activation of the plan.
- **Assessment:** Assessment of the extent of the disruption and the status of backups.
- **Restoration:** Restoration of critical systems and data from backups to alternate infrastructure.
- **Verification:** Verification that restored systems are functional and data is intact.
- **Resumption:** Resumption of business operations and communication with stakeholders.
- **Return to Normal:** Migration back to primary infrastructure once it is deemed safe.

### 7.3 Communication
During a disaster, the Operations department coordinates communication with:
- Employees, through internal channels.
- Clients, regarding the status of services and expected recovery timelines.
- Executive leadership, including the CEO, **Arvind Malhotra**, and the CFO, **Kabir Nair**, for financial impact assessment.

## 8. Ransomware and Malware Protection
Backups are a critical defense against ransomware attacks. To protect backups from ransomware:
- Backups must be stored in an immutable format.
- Backup systems must be isolated from the primary network where feasible.
- Backup credentials must be separate from production credentials and protected with MFA.
- Regular recovery testing ensures that backups can be restored even if the primary systems are compromised.

In the event of a ransomware attack, the Incident Response Plan (ITSEC-005) is activated, and the backup and recovery procedures in this policy are used to restore affected systems.

## 9. Data Retention and Disposal
Backups are retained for the periods specified in Section 4.1. At the end of the retention period, backups are securely disposed of in accordance with the Data Classification Policy (ITSEC-006). Financial records are retained for 7 years in accordance with the Procurement Policy (FIN-001) and applicable tax regulations.

## 10. Related Documents
- **ITSEC-001 — Information Security Policy**: Overarching security framework.
- **ITSEC-005 — Incident Response Plan**: Response to ransomware and other incidents.
- **ITSEC-006 — Data Classification Policy**: Data sensitivity and retention requirements.
- **FIN-001 — Procurement Policy**: Financial record retention requirements.

---

## 11. Revision History

| Version | Date | Change Description | Author | Approved By |
|---|---|---|---|---|
| v1 | 2026-01-15 | Initial Release of Backup & Disaster Recovery Policy | Rohit Verma | Arvind Malhotra |

---
*End of Document*
