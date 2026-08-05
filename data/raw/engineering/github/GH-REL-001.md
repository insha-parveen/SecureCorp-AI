---
github_id: GH-REL-001
repository: securecorp-backend
artifact_type: release_notes
classification: department_internal
allowed_roles: [manager, it, admin]
author: Sunita Rao
reviewers: []
assignees: []
related_documents: ['ENG-001', 'ENG-003']
related_jira: ['none']
related_slack: ['SLK-ORION-001']
related_emails: ['none']
related_meetings: ['MEET-ENG-001']
related_project: Project Orion
created_date: 2026-03-25
updated_date: 2026-03-25
source_type: github
tags: ['release', 'project-orion', 'v1.4']
---

# [Release] Project Orion v1.4 Release Notes

## Version
v1.4

## Features
- Improved ingestion throughput by 25% through pipeline optimization
- Standardized API error envelope across all endpoints (ENG-003)
- Dashboard performance improvements for large time ranges

## Bug Fixes
- Fixed JWT clock skew tolerance in refresh token validation (JIRA-ORION-001)
- Fixed CORS configuration for ACME tenant (JIRA-ACME-001)
- Fixed silent backup failure alerting (JIRA-CLOUD-003)

## Breaking Changes
- API error responses now use the standard envelope format - clients parsing error bodies must update.
- Rate limiting headers are now returned on all API responses.

## Known Issues
- Analytics ML pipelines still have backup scope gaps - tracked in JIRA-CLOUD-003 follow-up.
- Dashboard historical queries > 7 days remain slow pending caching work (JIRA-ORION-003).

---
*End of GH-REL-001*
