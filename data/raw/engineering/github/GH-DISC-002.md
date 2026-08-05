---
github_id: GH-DISC-002
repository: auth-service
artifact_type: discussion
classification: department_internal
allowed_roles: [manager, it, admin]
author: Rohit Verma
reviewers: ['Sunita Rao', 'Rahul Sharma']
assignees: []
related_documents: ['ITSEC-002', 'ENG-003']
related_jira: ['JIRA-SEC-005']
related_slack: ['SLK-ENG-BE-001']
related_emails: ['EMAIL-013']
related_meetings: ['MEET-SEC-001']
related_project: Security
created_date: 2026-02-09
updated_date: 2026-02-10
source_type: github
tags: ['jwt', 'rbac', 'security']
---

# [Discussion] RBAC enforcement for token-based auth in microservices

## Description
Discussion on improving RBAC enforcement across the auth-service and downstream microservices to ensure token permissions are consistently applied.

We need to ensure that RBAC roles are enforced consistently across all services. The current token only carries the user ID; we should add role claims.

Per ITSEC-002 and the access control model in the Company Bible.

## Replies
- Sunita Rao: Adding role claims to the JWT is the right approach. Ensure the roles are current at token refresh.
- Rahul Sharma: We'll need to update all services to validate the role claims per ENG-003.
- Rohit Verma: This aligns with the RBAC model defined in the authorization dimensions.

---
*End of GH-DISC-002*
