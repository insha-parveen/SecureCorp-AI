---
document_id: OPS-002
title: Disaster Recovery Test Report
document_type: incident_report
department: OPS
classification: department_internal
allowed_roles:
  - manager
  - it
  - admin
allowed_departments:
  - OPS
  - ITSEC
  - ENG
owner_department: OPS
document_version: v1
effective_date: 2026-02-25
status: active
created_date: 2026-02-20
last_reviewed_date: 2026-02-25
supersedes_document_version: null
related_documents:
  - ENG-001
  - ITSEC-005
  - ITSEC-006
  - ITSEC-007
  - OPS-003
  - SEC-001
tags:
  - disaster-recovery
  - testing
  - operations
  - business-continuity
  - report
source_type: google_drive
---

# Disaster Recovery Test Report

## 1. Executive Summary
This report documents the results of the Q1 FY2026 disaster recovery (DR) exercise conducted on 2026-02-18 by NexaCore Solutions Pvt. Ltd. The exercise was designed to validate the recovery readiness of the Project Orion platform and internal systems in accordance with the Backup & Disaster Recovery Policy (ITSEC-007).

The exercise successfully demonstrated the ability to restore Tier 1 systems within the target Recovery Time Objective (RTO) of 4 hours and the Recovery Point Objective (RPO) of 15 minutes. A total of 14 of 16 tested components met their recovery targets. Two components missed their RPO targets, and corrective actions have been identified.

The DR exercise was coordinated by the Operations department under Ayesha Khan, with participation from Engineering (Sunita Rao) and the IT and Security department (Rohit Verma).

## 2. Test Objectives
The primary objectives of the DR exercise were to:
- Validate that critical systems can be restored within defined RTO and RPO targets.
- Verify the integrity and usability of backups.
- Test the failover procedures for cloud environments.
- Assess the effectiveness of the incident response and recovery runbooks.
- Identify gaps and improvement opportunities for future exercises.

## 3. Scope
The exercise covered:
- Project Orion core services (ingestion, analytics, presentation).
- Critical internal systems (identity provider, ticketing, document management).
- Financial and client data stores.
- The VPN infrastructure used for remote recovery operations (ITSEC-008).

The exercise did not cover third-party client environments not managed directly by NexaCore.

## 4. Test Methodology

### 4.1 Scenario
The test simulated a significant regional outage in the primary cloud region, requiring failover to the secondary region.

### 4.2 Timeline

| Time | Activity |
|---|---|
| 09:00 IST | Test initiation; notification of DR team |
| 09:15 IST | Isolation of primary region; activation of DR plan |
| 09:30 IST | Restoration of critical databases from backups |
| 10:30 IST | Failover of stateless services to secondary region |
| 12:00 IST | Restoration of core Orion services |
| 12:45 IST | Data integrity verification |
| 14:30 IST | Verification of client-facing dashboards |
| 15:00 IST | Test completion and initial debrief |

### 4.3 Success Criteria
- Tier 1 systems recovered within 4 hours (RTO).
- Data loss not exceeding 15 minutes (RPO).
- All restored systems pass integrity checks.
- No unrecoverable data loss.

## 5. Test Results

### 5.1 Recovery Performance Summary

| System | Target RTO | Actual RTO | Target RPO | Actual RPO | Status |
|---|---|---|---|---|---|
| Orion Core - Ingestion | 4h | 3h 15m | 15m | 12m | ✅ |
| Orion Core - Analytics | 4h | 3h 30m | 15m | 12m | ✅ |
| Orion Core - Presentation | 4h | 3h 45m | 15m | 10m | ✅ |
| Identity Provider | 4h | 3h 10m | 15m | 8m | ✅ |
| Ticketing System | 24h | 5h | 24h | 20m | ✅ |
| Document Management | 24h | 6h | 24h | 30m | ✅ |
| Financial Data Store | 4h | 3h 30m | 15m | 10m | ✅ |
| Client Data Store | 4h | 3h 20m | 15m | 12m | ✅ |
| VPN Infrastructure | 4h | 2h 45m | 15m | 9m | ✅ |
| Backup Monitoring | 4h | 3h 5m | 15m | 11m | ✅ |
| Email System | 24h | 7h | 24h | 40m | ✅ |
| Analytics ML Pipelines | 24h | 8h | 24h | 55m | ⚠️ |
| Reporting Service | 4h | 3h 50m | 15m | 14m | ✅ |
| API Gateway | 4h | 3h 25m | 15m | 12m | ✅ |
| Notification Service | 24h | 5h 30m | 24h | 45m | ✅ |
| Legacy Reporting DB | 72h | 68h | 48h | 70m | ⚠️ |

### 5.2 Notable Findings
- **Analytics ML Pipelines:** The ML model artifacts were not readily available for restoration, causing the RPO to be missed. The model registry backup schedule needs to be verified against ITSEC-006 retention requirements.
- **Legacy Reporting DB:** The backup set included stale data because of an incomplete incremental backup. The backup monitoring was not configured to alert on this gap, which is a gap in Backup & Disaster Recovery Policy (ITSEC-007) compliance.

## 6. Data Integrity Verification
Post-restoration integrity checks were performed on all restored data stores. The checks included hash comparison of sample records, consistency verification, and query validation. No data corruption was detected in any restored system.

## 7. Detailed Test Observations

### 7.1 Ingestion Layer Recovery
The ingestion layer was restored successfully within the target RTO. The collectors reconnected to the secondary region without manual intervention, and telemetry buffering prevented data loss during the failover window.

### 7.2 Analytics Layer Recovery
The analytics layer was restored within the target RTO. However, the ML model artifacts were not available in the backup set, requiring model retraining. This was the primary cause of the RPO miss for the analytics pipelines.

### 7.3 Financial Data Store Recovery
The financial data store was restored successfully with no data loss. The transaction log backups enabled point-in-time recovery to within 10 minutes of the failover.

### 7.4 Client Data Store Recovery
The client data store was restored successfully. Data integrity checks confirmed that all client records were intact and consistent.

### 7.5 VPN Infrastructure Recovery
The VPN infrastructure was restored ahead of target, enabling remote access for the recovery team. This validated the alignment with the VPN & Remote Access Policy (ITSEC-008).

## 8. Test Environment and Team Performance

### 8.1 Test Environment
The DR test was conducted in a dedicated recovery environment in the secondary region. This environment mirrors the production configuration as closely as practical, allowing the recovery procedures to be validated under realistic conditions.

### 8.2 Team Performance
The DR team demonstrated strong coordination and efficiency during the exercise. Communication was effective, and the incident command structure defined in the Incident Response Plan (ITSEC-005) was followed correctly. The debrief highlighted areas for further training in the recovery of ML pipelines and legacy systems.

### 8.3 Tooling Gaps
The exercise identified a need for improved tooling to automate the validation of backup freshness and integrity. This tooling will reduce manual effort and improve the reliability of recurring DR testing.

## 9. Issues, Root Causes, and Lessons Learned

### 9.1 Issue 1: ML Model Artifacts Not Restorable (High)
- **Root Cause:** Model artifacts were stored outside the primary backup scope; only the model registry metadata was backed up.
- **Impact:** RPO missed; models had to be retrained on restored data.
- **Corrective Action:** Update the backup configuration to include the model artifact store in the daily backup and verify restoration in the next quarterly test.

### 9.2 Issue 2: Stale Incremental Backup in Legacy Reporting DB (Medium)
- **Root Cause:** An incremental backup of the legacy reporting database failed silently, and the monitoring alert was suppressed.
- **Impact:** RPO exceeded; up to 70 minutes of data was unavailable.
- **Corrective Action:** Fix the silent failure handling, re-enable alerting, and review monitoring thresholds per ITSEC-007.

### 9.3 Backup Scope Completeness
The exercise highlighted the importance of ensuring that all data types, including ML model artifacts, are included in the backup scope. The backup configuration has been updated to include the model artifact store.

### 9.4 Monitoring and Alerting
Silent backup failures must be detected and alerted immediately. The monitoring configuration has been updated to alert on any failed or incomplete backup job.

### 9.5 Runbook Accuracy
Several runbooks required updates based on the exercise. All runbooks have been reviewed and updated to reflect the actual recovery procedures.

## 10. Recommendations

| # | Recommendation | Priority | Owner | Target Date |
|---|---|---|---|---|
| 1 | Include ML model artifacts in backup scope | High | Sunita Rao | 2026-03-10 |
| 2 | Fix silent backup failures and alerting | High | Rohit Verma | 2026-03-15 |
| 3 | Automate validation of backup freshness | Medium | Sunita Rao | 2026-03-31 |
| 4 | Expand DR test to include client-managed environments | Medium | Ayesha Khan | 2026-06-30 |
| 5 | Integrate DR test findings into Quarterly Operations Report | Low | Ayesha Khan | 2026-04-10 |

## 11. Conclusion
The Q1 FY2026 DR exercise demonstrated overall readiness of critical systems. The Project Orion platform and core internal services met their RTO and RPO targets, and no data corruption was encountered. Two improvement areas were identified, primarily related to backup scope and monitoring. These have been prioritized and are tracked as action items.

The findings will be incorporated into the next iteration of the Backup & Disaster Recovery Policy (ITSEC-007) and the Quarterly Operations Report (OPS-003).

## 12. Related Documents
- **ENG-001 — Project Orion Architecture Overview**: System architecture subject to test.
- **ITSEC-005 — Incident Response Plan**: Incident response procedures.
- **ITSEC-006 — Data Classification Policy**: Data retention requirements.
- **ITSEC-007 — Backup & Disaster Recovery Policy**: Recovery objectives.
- **OPS-003 — Quarterly Operations Report**: Ongoing operational review.
- **SEC-001 — Security Audit Report Q1 2026**: Security posture context.

---

## 13. Revision History

| Version | Date | Change Description | Author | Approved By |
|---|---|---|---|---|
| v1 | 2026-02-25 | Initial Release of Disaster Recovery Test Report | Ayesha Khan | Arvind Malhotra |

---
*End of Document*
