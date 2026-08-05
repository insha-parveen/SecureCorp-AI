---
github_id: GH-ISS-001
repository: securecorp-backend
artifact_type: issue
classification: department_internal
allowed_roles: [manager, it, admin]
author: Neha Kapoor
reviewers: ['Sunita Rao']
assignees: ['Rahul Sharma']
related_documents: ['ENG-003']
related_jira: ['JIRA-ORION-003']
related_slack: ['SLK-ACME-002']
related_emails: ['EMAIL-061']
related_meetings: ['MEET-ACME-002']
related_project: Project Orion
created_date: 2026-05-18
updated_date: 2026-06-01
source_type: github
tags: ['performance', 'caching', 'dashboard']
---

# [Issue] Dashboard slow for historical data > 7 days

## Problem
The analytics dashboard is slow when viewing historical data for more than 7 days. Queries hit cold storage which is not optimized for large time ranges.

## Reproduction
1. Navigate to the dashboard.
2. Select a date range greater than 7 days.
3. Observe query latency above 10 seconds.

## Expected Result
Historical data queries should complete within 2 seconds.

## Actual Result
Queries for ranges > 7 days take 10+ seconds.

## Discussion
- Sunita Rao: We may need to add caching for common historical queries. Refer to the data lifecycle section in ENG-001.
- Meera Iyer: ACME is asking for a timeline. This impacts UAT.
- Rahul Sharma: Adding a pre-aggregation step will help, but it takes longer. Caching fix can be done this week.

## Labels
performance, caching, p2

## Milestone
Project Orion v1.5

---
*End of GH-ISS-001*
