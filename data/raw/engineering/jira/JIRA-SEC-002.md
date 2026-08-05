---
issue_id: JIRA-SEC-002
project: Security
issue_type: Task
priority: High
status: Done
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rohit Verma
reporter: Sunita Rao
department: ITSEC
related_documents: ['SEC-001', 'ITSEC-006', 'ITSEC-007']
related_emails: ['EMAIL-070']
related_slack: ['SLK-OPS-003']
related_meetings: ['MEET-SEC-001']
created_date: 2026-04-10
updated_date: 2026-04-30
source_type: jira
tags: ['security', 'encryption', 'backup', 'task']
---

# Implement Encryption at rest for legacy reporting DB backup

## Description
Enable encryption at rest for the legacy reporting database backup to comply with ITSEC-006 and ITSEC-007.

## Background
The Security Audit (SEC-001) identified that the backup of the legacy reporting database is stored without encryption at rest (Finding H-02).

## Steps to Reproduce
1. Identify backup storage.
2. Enable encryption at rest.
3. Verify encryption is active.

## Expected Behaviour
Backup stored with encryption at rest.

## Actual Behaviour
Backup is currently unencrypted.

## Business Impact
Sensitive data at risk of exposure per ITSEC-006.

## Technical Notes
Enable encryption at rest for all backup storage per SEC-001 H-02.

## Acceptance Criteria
1. Encryption enabled.
2. Backup verified encrypted.
3. Finding H-02 closed.

## Comments
- **Rohit Verma:** This is a High finding from SEC-001. Enable encryption at rest immediately.
- **Sunita Rao:** Encryption enabled on the backup storage.

## Activity Log
- 2026-04-10 09:00: Created by Sunita Rao
- 2026-04-30 10:00: Done

## Attachments
['none']

---
*End of Issue JIRA-SEC-002*
