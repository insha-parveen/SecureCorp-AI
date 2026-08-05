---
issue_id: JIRA-PLATFORM-001
project: Internal Platform
issue_type: Bug
priority: High
status: Testing
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rahul Sharma
reporter: Sunita Rao
department: ENG
related_documents: ['ENG-002']
related_emails: ['none']
related_slack: ['SLK-OPS-002']
related_meetings: ['none']
created_date: 2026-05-10
updated_date: 2026-05-12
source_type: jira
tags: ['internal-platform', 'database', 'performance', 'bug']
---

# Database migration causing performance regression

## Description
The database migration caused a performance regression, slowing down queries on the internal metrics service.

## Background
After migrating the internal metrics database, query performance degraded due to missing indexes and config changes.

## Steps to Reproduce
1. Run a standard metrics query.
2. Observe query latency.
3. Compare to baseline.

## Expected Behaviour
Query latency should match pre-migration baseline.

## Actual Behaviour
Query latency increased by 300% post-migration.

## Business Impact
Slow internal dashboards and reduced operational visibility.

## Technical Notes
Review index configuration and query plans post-migration.

## Acceptance Criteria
1. Add missing indexes.
2. Optimize queries.
3. Restore baseline performance.

## Comments
- **Sunita Rao:** The database migration caused a performance regression.
- **Rahul Sharma:** Investigating missing indexes. Adding them now.

## Activity Log
- 2026-05-10 09:00: Created by Sunita Rao
- 2026-05-12 14:00: Testing

## Attachments
['Profiler_Report.pdf']

---
*End of Issue JIRA-PLATFORM-001*
