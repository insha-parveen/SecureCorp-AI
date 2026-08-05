---
github_id: GH-PR-002
repository: securecorp-backend
artifact_type: pull_request
classification: department_internal
allowed_roles: [manager, it, admin]
author: Neha Kapoor
reviewers: ['Sunita Rao', 'Rahul Sharma']
assignees: ['Neha Kapoor']
related_documents: ['ENG-003']
related_jira: ['JIRA-ORION-002']
related_slack: ['SLK-ENG-BE-002']
related_emails: ['EMAIL-030']
related_meetings: ['MEET-ENG-001']
related_project: Project Orion
created_date: 2026-03-20
updated_date: 2026-03-22
source_type: github
tags: ['api', 'error-handling', 'eng-003']
---

# [PR] Align all API error responses to standard envelope format

## Description
Updates all API endpoints to return the standard error envelope (code, message, details, requestId) as defined in ENG-003. Adds contract tests for error handling.

Closes JIRA-ORION-002.

## Files Changed
- app/errors.py
- app/routes/incidents.py
- app/routes/alerts.py
- tests/contract/test_error_format.py

## Commits
- f6a5b4c Standardize error envelope
- 8d9e0f1 Add contract tests for error responses

## Code Review Comments
- Rahul Sharma: Good job standardizing the error responses.
- Sunita Rao: Please use PATCH instead of PUT for partial updates per ENG-003.
- Neha Kapoor: Updated - changed the alerts endpoint to PATCH.

## Requested Changes
Sunita Rao: Ensure 429 Too Many Requests also uses the standard envelope.

## Approvals
Rahul Sharma, Sunita Rao

## Merge Status
MERGED

---
*End of GH-PR-002*
