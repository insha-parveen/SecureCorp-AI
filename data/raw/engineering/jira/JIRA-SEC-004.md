---
issue_id: JIRA-SEC-004
project: Security
issue_type: Improvement
priority: Medium
status: In Progress
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rohit Verma
reporter: Sunita Rao
department: ITSEC
related_documents: ['SEC-001', 'ITSEC-002']
related_emails: ['EMAIL-058']
related_slack: ['SLK-LDR-002']
related_meetings: ['MEET-SEC-001']
created_date: 2026-04-10
updated_date: 2026-06-05
source_type: jira
tags: ['security', 'mfa', 'vendor', 'improvement']
---

# Enforce MFA on third-party vendor console

## Description
Enforce multi-factor authentication on a third-party vendor management console per SEC-001 Finding H-03 and ITSEC-002.

## Background
The vendor console used by a third-party does not enforce MFA, violating ITSEC-002. Access was restricted until MFA is enforced.

## Steps to Reproduce
1. Access vendor console.
2. Attempt without MFA.
3. Verify MFA is enforced.

## Expected Behaviour
MFA enforced on vendor console.

## Actual Behaviour
MFA not currently enforced.

## Business Impact
Compromised vendor credentials could lead to unauthorized access.

## Technical Notes
Require MFA on the vendor console per SEC-001 H-03 and ITSEC-002.

## Acceptance Criteria
1. MFA enforced.
2. Access restored.
3. Finding H-03 closed.

## Comments
- **Rohit Verma:** The vendor has been notified, and access is restricted until MFA is enforced.
- **Kabir Nair:** Security is important, but I need to plan costs.
- **Rohit Verma:** Minimal cost, mostly operational controls.

## Activity Log
- 2026-04-10 09:00: Created by Sunita Rao
- 2026-06-05 09:00: In Progress

## Attachments
['none']

---
*End of Issue JIRA-SEC-004*
