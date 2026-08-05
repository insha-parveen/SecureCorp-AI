---
github_id: GH-ISS-003
repository: auth-service
artifact_type: issue
classification: department_internal
allowed_roles: [manager, it, admin]
author: Rohit Verma
reviewers: ['Sunita Rao']
assignees: ['Rahul Sharma']
related_documents: ['ITSEC-002', 'SEC-001']
related_jira: ['JIRA-SEC-004']
related_slack: ['SLK-LDR-002']
related_emails: ['EMAIL-058']
related_meetings: ['MEET-SEC-001']
related_project: Security
created_date: 2026-04-10
updated_date: 2026-06-05
source_type: github
tags: ['security', 'mfa', 'vendor']
---

# [Issue] Third-party vendor console does not enforce MFA

## Problem
A third-party vendor management console does not enforce multi-factor authentication, violating the Password Policy (ITSEC-002) and the Security Audit finding SEC-001 H-03.

## Reproduction
1. Access the vendor console without MFA.
2. Observe that access is permitted.

## Expected Result
MFA should be required for all vendor console access.

## Actual Result
MFA is not currently enforced.

## Discussion
- Rohit Verma: This is a High finding from SEC-001. The vendor has been notified, and access is restricted until MFA is enforced.
- Kabir Nair: Any cost impact? Security is important but I need to plan.
- Rohit Verma: Minimal cost - mostly operational controls and process changes.

## Labels
security, mfa, vendor, p1

## Milestone
Security Q2 Remediation

---
*End of GH-ISS-003*
