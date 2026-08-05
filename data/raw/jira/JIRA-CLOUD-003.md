---
issue_id: JIRA-CLOUD-003
project: Cloud Migration
issue_type: Bug
priority: Medium
status: Code Review
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rahul Sharma
reporter: Ayesha Khan
department: ENG
related_documents: ['ITSEC-007', 'OPS-002', 'OPS-003']
related_emails: ['EMAIL-052']
related_slack: ['SLK-OPS-003']
related_meetings: ['MEET-DR-001']
created_date: 2026-06-03
updated_date: 2026-06-05
source_type: jira
tags: ['cloud-migration', 'backup', 'bug', 'monitoring']
---

# Backup job for analytics database silently failing

## Description
A backup job for the analytics database is failing silently when it should be alerting. This was identified during the DR exercise.

## Background
The DR exercise (OPS-002) identified that an incremental backup of the legacy reporting database failed silently and the monitoring alert was suppressed.

## Steps to Reproduce
1. Run backup job.
2. Observe whether it succeeds or fails.
3. Check if alert fires.

## Expected Behaviour
Failed backup should trigger immediate alert.

## Actual Behaviour
Backup fails but no alert is triggered.

## Business Impact
Data loss risk and RPO miss with no visibility.

## Technical Notes
Fix silent failure handling and re-enable alerting per ITSEC-007.

## Acceptance Criteria
1. Silent failure handling fixed.
2. Alerting re-enabled.
3. Monitoring thresholds reviewed per ITSEC-007.

## Comments
- **Rohit Verma:** The monitoring alert fired correctly this time, confirming the fix from the DR test is working. The issue is a transient storage error.
- **Ayesha Khan:** This confirms the monitoring fix from the DR test is working.

## Activity Log
- 2026-06-03 02:15: Created by Ayesha Khan
- 2026-06-05 09:00: Code Review

## Attachments
['Incident_Report.pdf']

---
*End of Issue JIRA-CLOUD-003*
