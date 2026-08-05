---
issue_id: JIRA-SEC-003
project: Security
issue_type: Task
priority: High
status: Done
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rohit Verma
reporter: Arvind Malhotra
department: ITSEC
related_documents: ['SEC-001', 'ITSEC-001', 'ITSEC-002']
related_emails: ['EMAIL-070']
related_slack: ['SLK-LDR-002']
related_meetings: ['MEET-SEC-001']
created_date: 2026-04-10
updated_date: 2026-04-30
source_type: jira
tags: ['security', 'privileged-accounts', 'task']
---

# Remove inactive privileged accounts from cloud environment

## Description
Remove privileged accounts associated with former vendors that remained active in the cloud environment per SEC-001 Finding H-01.

## Background
The Security Audit (SEC-001) identified 7 privileged accounts associated with former vendors that remained active. These need to be removed per ITSEC-001 and ITSEC-002.

## Steps to Reproduce
1. List all privileged accounts.
2. Identify inactive vendor accounts.
3. Remove them.

## Expected Behaviour
No inactive privileged accounts remain.

## Actual Behaviour
7 inactive vendor accounts were active.

## Business Impact
Unauthorized access risk through stale credentials.

## Technical Notes
Remove inactive accounts and implement automated lifecycle management per SEC-001 H-01.

## Acceptance Criteria
1. Inactive accounts removed.
2. Lifecycle management implemented.
3. Finding H-01 closed.

## Comments
- **Rohit Verma:** Found 7 inactive vendor accounts. Removing them.
- **Arvind Malhotra:** Ensure this is resolved quickly per the security audit.

## Activity Log
- 2026-04-10 09:00: Created by Arvind Malhotra
- 2026-04-30 10:00: Done

## Attachments
['none']

---
*End of Issue JIRA-SEC-003*
