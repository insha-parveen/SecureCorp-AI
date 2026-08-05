---
github_id: GH-PR-007
repository: securecorp-frontend
artifact_type: pull_request
classification: department_internal
allowed_roles: [manager, it, admin]
author: Neha Kapoor
reviewers: ['Sunita Rao']
assignees: ['Neha Kapoor']
related_documents: ['ENG-001', 'CLIENT-001']
related_jira: ['JIRA-ACME-002']
related_slack: ['SLK-ACME-001']
related_emails: ['EMAIL-059']
related_meetings: ['MEET-ACME-002']
related_project: Customer ACME
created_date: 2026-06-12
updated_date: 2026-06-15
source_type: github
tags: ['dashboard', 'tiered-alerting', 'frontend']
---

# [PR] Add tier classification display to dashboard

## Description
Updates the dashboard to display system tier classification so ACME can see which systems are in Tier 1/2/3, supporting the tiered alerting feature per JIRA-ACME-002.

## Files Changed
- src/components/TierBadge.js
- src/views/DashboardView.jsx
- src/styles/tier.css

## Commits
- e1f2a3b Add tier badge component
- c4d5e6f Integrate tier display in dashboard view

## Code Review Comments
- Sunita Rao: The tier display looks clean. Ensure it works for the ACME tenant specifically.
- Neha Kapoor: Tested with the ACME tenant - confirmed working per CLIENT-001.

## Requested Changes
None

## Approvals
Sunita Rao

## Merge Status
OPEN

---
*End of GH-PR-007*
