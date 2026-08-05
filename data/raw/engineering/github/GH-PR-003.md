---
github_id: GH-PR-003
repository: securecorp-frontend
artifact_type: pull_request
classification: department_internal
allowed_roles: [manager, it, admin]
author: Neha Kapoor
reviewers: ['Sunita Rao']
assignees: ['Neha Kapoor']
related_documents: ['ENG-001', 'CLIENT-001']
related_jira: ['JIRA-ACME-001']
related_slack: ['SLK-ENG-FE-001']
related_emails: ['none']
related_meetings: ['none']
related_project: Customer ACME
created_date: 2026-03-20
updated_date: 2026-03-20
source_type: github
tags: ['cors', 'frontend', 'dashboard', 'fix']
---

# [PR] Fix CORS configuration for ACME tenant dashboard

## Description
Adds the ACME tenant origin to the API gateway allowed origins to resolve the CORS error blocking the dashboard. Adds an automated check that validates allowed origins cover all active tenants.

Resolves JIRA-ACME-001 and the #eng-frontend thread.

## Files Changed
- src/config/gateway.json
- src/utils/corsCheck.js
- tests/test_cors_coverage.py

## Commits
- c3d4e5f Add ACME origin to gateway config
- 0a1b2c3 Add automated tenant origin coverage check

## Code Review Comments
- Sunita Rao: This is exactly the kind of configuration drift SEC-001 flagged. Good catch adding the automated check.
- Neha Kapoor: Thanks! The automated check will prevent this from recurring.

## Requested Changes
None

## Approvals
Sunita Rao

## Merge Status
MERGED

---
*End of GH-PR-003*
