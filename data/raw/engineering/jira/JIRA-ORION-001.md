---
issue_id: JIRA-ORION-001
project: Project Orion
issue_type: Bug
priority: Critical
status: Closed
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rahul Sharma
reporter: Sunita Rao
department: ENG
related_documents: ['ENG-003', 'ITSEC-002', 'SEC-001']
related_emails: ['EMAIL-026']
related_slack: ['SLK-ENG-BE-001']
related_meetings: ['none']
created_date: 2026-03-14
updated_date: 2026-03-14
source_type: jira
tags: ['authentication', 'jwt', 'bug', 'project-orion']
---

# Authentication service failing after deployment - JWT clock skew tolerance removed

## Description
The Project Orion authentication service began failing after a deployment removed the JWT clock skew tolerance. Users experienced 401 errors on the token refresh endpoint.

## Background
The refresh token validation logic was modified during a recent deployment to tighten security. The change removed the clock skew tolerance, causing valid tokens to be rejected when the server and client clocks were slightly out of sync.

## Steps to Reproduce
1. Deploy the auth service with the clock skew change.
2. Attempt to refresh a token after 09:00 IST.
3. Observe 401 error on the refresh endpoint.

## Expected Behaviour
Tokens with minor clock differences should still be validated successfully.

## Actual Behaviour
Tokens with even 1-2 seconds of clock skew are rejected with 401.

## Business Impact
All Project Orion users were unable to authenticate for approximately 30 minutes during peak usage.

## Technical Notes
Fix involves restoring clock skew tolerance per API Design Guidelines (ENG-003). Compliance with ITSEC-002 Password Policy is required.

## Acceptance Criteria
1. Restore JWT clock skew tolerance.
2. Add regression test for clock skew scenario.
3. Obtain CISO sign-off per ITSEC-002.

## Comments
- **Sunita Rao:** Roll back the clock skew change and restore service first.
- **Rahul Sharma:** Rollback deployed, auth service is back up.
- **Rohit Verma:** Please log the incident and reference the fix. This aligns with SEC-001 findings on configuration drift.

## Activity Log
- 2026-03-14 09:22: Created by Sunita Rao
- 2026-03-14 09:50: Rollback deployed by Rahul Sharma
- 2026-03-14 10:15: Marked Closed

## Attachments
['Stacktrace.log']

---
*End of Issue JIRA-ORION-001*
