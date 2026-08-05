---
issue_id: JIRA-ACME-001
project: Customer ACME
issue_type: Bug
priority: High
status: Testing
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Sunita Rao
reporter: Meera Iyer
department: ENG
related_documents: ['ENG-003', 'CLIENT-001']
related_emails: ['none']
related_slack: ['SLK-ENG-FE-001']
related_meetings: ['none']
created_date: 2026-03-20
updated_date: 2026-03-20
source_type: jira
tags: ['acme', 'cors', 'dashboard', 'bug']
---

# CORS issue blocking ACME dashboard access

## Description
The dashboard fails to load for the ACME Manufacturing tenant due to a CORS configuration issue on the API gateway.

## Background
After a frontend deployment, the ACME tenant origin was not added to the API gateway allowed origins, causing the browser to block responses.

## Steps to Reproduce
1. Open dashboard for ACME tenant.
2. Check browser console for CORS errors.
3. Observe blank charts.

## Expected Behaviour
ACME dashboard should load normally.

## Actual Behaviour
Dashboard is blank with CORS errors in console.

## Business Impact
ACME team unable to perform UAT, impacting the implementation timeline per CLIENT-001.

## Technical Notes
Add the ACME origin to the API gateway allowed origins. Add automated check for tenant coverage.

## Acceptance Criteria
1. ACME origin added to API gateway config.
2. Redeploy gateway.
3. Automated check to validate tenant origins.

## Comments
- **Ayesha Khan:** ACME is doing UAT this week per CLIENT-001. Let's get this fixed quickly.
- **Neha Kapoor:** Dashboard is loading now for the ACME tenant. Confirmed.
- **Rahul Sharma:** Config updated and redeploying now.

## Activity Log
- 2026-03-20 11:30: Created by Meera Iyer
- 2026-03-20 11:58: Fixed, Testing

## Attachments
['Screenshot.png']

---
*End of Issue JIRA-ACME-001*
