---
email_id: EMAIL-026
source_type: email
classification: department_internal
allowed_roles: ['manager', 'it', 'admin']
department: ENG
owner: Sunita Rao
participants: ['Sunita Rao', 'Rahul Sharma', 'Rohit Verma']
related_project: Project Orion
related_documents: ['ITSEC-005', 'SEC-001']
created_date: 2026-03-10
tags: ['engineering', 'incident', 'production', 'project-orion']
---

# Production Incident - Authentication Service Failure

**From:** Sunita Rao

**To:** Rahul Sharma

**CC:** Rohit Verma

**Date:** 2026-03-10

**Time:** 11:00

**Subject:** Production Incident - Authentication Service Failure

**Priority:** High

**Classification:** department_internal

**Department:** ENG

**Project:** Project Orion

**Attachments:** Incident_Report_INC1042.pdf

**Body:**

Hi Rahul,

As discussed in #eng-backend, the authentication service failed after yesterday's deployment. The root cause was the removal of clock skew tolerance in JWT validation.

Actions taken:
1. Rollback deployed - service restored
2. Regression test added for clock skew scenario
3. Post-incident review scheduled per ITSEC-005

Please prepare the incident report and reference the fix. This aligns with the findings in the Security Audit (SEC-001) regarding configuration drift.

Best regards,
Sunita Rao
VP Engineering, NexaCore Solutions Pvt. Ltd.
EMP-0002
