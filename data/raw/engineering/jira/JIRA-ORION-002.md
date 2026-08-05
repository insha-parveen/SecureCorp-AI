---
issue_id: JIRA-ORION-002
project: Project Orion
issue_type: Bug
priority: High
status: Done
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Neha Kapoor
reporter: Rahul Sharma
department: ENG
related_documents: ['ENG-003']
related_emails: ['EMAIL-030']
related_slack: ['SLK-ENG-BE-002']
related_meetings: ['none']
created_date: 2026-03-18
updated_date: 2026-03-22
source_type: jira
tags: ['api', 'error-format', 'eng-003', 'project-orion']
---

# API error format does not conform to ENG-003 standard envelope

## Description
Several API endpoints return error responses in an inconsistent format, not following the standard error envelope defined in the API Design Guidelines.

## Background
During the API audit, multiple endpoints were found to return errors in an ad-hoc format, rather than the standard envelope with code, message, details, and requestId.

## Steps to Reproduce
1. Call any error-generating endpoint.
2. Observe the error response body.
3. Compare with the standard format in ENG-003.

## Expected Behaviour
Errors return the standard envelope: code, message, details, requestId.

## Actual Behaviour
Errors return varied structures without a standard envelope.

## Business Impact
API consumers, including ACME Manufacturing, have difficulty parsing error responses programmatically.

## Technical Notes
Align all endpoints to the standard error format per ENG-003.

## Acceptance Criteria
1. Update all endpoints to return standard error envelope.
2. Add contract tests for error responses.
3. Verify with ACME integration.

## Comments
- **Rahul Sharma:** Several endpoints return different error structures.
- **Sunita Rao:** Let's align all endpoints to the standard error format per ENG-003.
- **Neha Kapoor:** Updated the error responses across all endpoints.

## Activity Log
- 2026-03-18 14:00: Created by Rahul Sharma
- 2026-03-20 11:00: Code Review requested
- 2026-03-22 14:00: Marked Done

## Attachments
['none']

---
*End of Issue JIRA-ORION-002*
