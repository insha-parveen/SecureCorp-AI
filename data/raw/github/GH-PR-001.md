---
github_id: GH-PR-001
repository: auth-service
artifact_type: pull_request
classification: department_internal
allowed_roles: [manager, it, admin]
author: Rahul Sharma
reviewers: ['Sunita Rao', 'Rohit Verma']
assignees: ['Rahul Sharma']
related_documents: ['ENG-003', 'ITSEC-002']
related_jira: ['JIRA-ORION-001']
related_slack: ['SLK-ENG-BE-001']
related_emails: ['EMAIL-013']
related_meetings: ['MEET-ENG-001']
related_project: Project Orion
created_date: 2026-03-14
updated_date: 2026-03-14
source_type: github
tags: ['jwt', 'authentication', 'security', 'fix']
---

# [PR] Restore JWT clock skew tolerance in refresh token validation

## Description
Restores the JWT clock skew tolerance that was removed in the previous deployment, causing the auth service to reject valid refresh tokens. Aligns with ENG-003 and ITSEC-002 requirements.

Resolves JIRA-ORION-001 and the #eng-backend discussion.

## Files Changed
- auth/token_validation.py
- auth/tests/test_token_refresh.py
- openapi.yaml

## Commits
- a1b2c3d Restore clock skew tolerance in JWT validation
- e4f5g6h Add regression test for clock skew scenario

## Code Review Comments
- Rohit Verma: Ensure this aligns with ITSEC-002 Password Policy. Token handling must match our auth standards.
- Sunita Rao: LGTM. Add a note in the commit message referencing the incident.
- Rahul Sharma: Done - referenced JIRA-ORION-001 in the description.

## Requested Changes
Rohit Verma: Please add an explicit unit test for a 30-second clock skew case.

## Approvals
Sunita Rao, Rohit Verma

## Merge Status
MERGED

---
*End of GH-PR-001*
