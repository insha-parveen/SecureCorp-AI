---
github_id: GH-PR-006
repository: auth-service
artifact_type: pull_request
classification: department_internal
allowed_roles: [manager, it, admin]
author: Rahul Sharma
reviewers: ['Sunita Rao', 'Rohit Verma']
assignees: ['Rahul Sharma']
related_documents: ['ITSEC-002', 'ENG-003']
related_jira: ['JIRA-SEC-005']
related_slack: ['SLK-ENG-BE-001']
related_emails: ['EMAIL-013']
related_meetings: ['MEET-SEC-001']
related_project: Security
created_date: 2026-02-09
updated_date: 2026-02-10
source_type: github
tags: ['jwt', 'token', 'security', 'compliance']
---

# [PR] Align refresh token validation with ITSEC-002 requirements

## Description
Updates the refresh token validation logic to fully align with the Password Policy (ITSEC-002) requirements for token handling and security.

Resolves JIRA-SEC-005.

## Files Changed
- auth/refresh_token.py
- auth/tests/test_refresh_policy.py

## Commits
- b1c2d3e Align token validation with ITSEC-002
- d4e5f6a Add compliance test for token handling

## Code Review Comments
- Rohit Verma: Verify the token lifetime and rotation rules match ITSEC-002.
- Sunita Rao: Looks correct. Approved after the compliance test passes.

## Requested Changes
Rohit Verma: Add a check for password rotation within the token flow.

## Approvals
Rohit Verma, Sunita Rao

## Merge Status
MERGED

---
*End of GH-PR-006*
