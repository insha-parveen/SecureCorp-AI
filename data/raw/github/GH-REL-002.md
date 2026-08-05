---
github_id: GH-REL-002
repository: auth-service
artifact_type: release_notes
classification: department_internal
allowed_roles: [manager, it, admin]
author: Rohit Verma
reviewers: []
assignees: []
related_documents: ['ITSEC-002', 'ENG-003']
related_jira: ['JIRA-SEC-005']
related_slack: ['SLK-SEC-003']
related_emails: ['EMAIL-033']
related_meetings: ['none']
related_project: Security
created_date: 2026-02-12
updated_date: 2026-02-12
source_type: github
tags: ['release', 'auth-service', 'v2.1']
---

# [Release] auth-service v2.1 Release Notes

## Version
v2.1

## Features
- Refresh token validation aligned with ITSEC-002 Password Policy
- RBAC role claims added to JWT tokens (per discussion GH-DISC-002)
- Improved MFA recovery process with identity verification

## Bug Fixes
- Fixed account lockout policy edge cases (JIRA-SEC-006)
- Fixed JWT clock skew validation (JIRA-ORION-001)

## Breaking Changes
- Tokens now include role claims - services must validate the new claims.
- Refresh token rotation interval changed per ITSEC-002.

## Known Issues
- Legacy API keys will be deprecated in v2.2 - migration guidance in README.

---
*End of GH-REL-002*
