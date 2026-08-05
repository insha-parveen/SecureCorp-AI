---
issue_id: JIRA-ATLAS-002
project: Project Atlas
issue_type: Story
priority: Medium
status: Open
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Neha Kapoor
reporter: Sunita Rao
department: ENG
related_documents: ['ENG-001', 'ENG-004', 'ENG-003']
related_emails: ['none']
related_slack: ['SLK-ATLAS-002']
related_meetings: ['MEET-ATLAS-001']
created_date: 2026-04-22
updated_date: 2026-05-01
source_type: jira
tags: ['project-atlas', 'frontend', 'dashboard', 'story']
---

# Atlas frontend - tenant-aware dashboard component

## Description
Implement the Atlas frontend with a tenant-aware dashboard that supports the lighter dashboard design for retail clients.

## Background
The Atlas frontend should reuse the Orion component library with tenant-aware configuration per the architecture review.

## Steps to Reproduce
1. Configure a new tenant.
2. Observe dashboard customization.

## Expected Behaviour
Different tenants can see their own dashboard configuration.

## Actual Behaviour
Not yet implemented.

## Business Impact
Enables multi-tenant delivery for Atlas clients.

## Technical Notes
Follow ENG-004 engineering standards and ENG-003 for any API integration.

## Acceptance Criteria
1. Tenant-aware dashboard component.
2. Feature flag for gradual rollout.
3. Test with Atlas pilot client.

## Comments
- **Neha Kapoor:** I'll create the component structure aligned with the architecture review.
- **Sunita Rao:** Make sure it follows the same pattern as Orion.

## Activity Log
- 2026-04-22 14:05: Created by Sunita Rao
- 2026-05-01 09:00: Open

## Attachments
['none']

---
*End of Issue JIRA-ATLAS-002*
