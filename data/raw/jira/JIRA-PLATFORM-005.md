---
issue_id: JIRA-PLATFORM-005
project: Internal Platform
issue_type: Bug
priority: Medium
status: Blocked
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rahul Sharma
reporter: Sunita Rao
department: ENG
related_documents: ['ENG-004']
related_emails: ['EMAIL-067']
related_slack: ['SLK-ENG-FE-002']
related_meetings: ['MEET-ENG-001']
created_date: 2026-05-30
updated_date: 2026-06-03
source_type: jira
tags: ['internal-platform', 'deployment', 'feature-flag', 'bug', 'blocked']
---

# Deployment issue - feature flag not working for component library

## Description
The feature flag for the new dashboard component library is not working as expected, blocking the gradual rollout.

## Background
The component library feature flag (per JIRA discussion in #eng-frontend) does not properly enable/disable the new components.

## Steps to Reproduce
1. Toggle the feature flag.
2. Attempt to use the component library.
3. Observe whether it changes.

## Expected Behaviour
Feature flag correctly controls component library availability.

## Actual Behaviour
Component library appears regardless of flag state.

## Business Impact
Blocks gradual rollout of the new dashboard components.

## Technical Notes
Investigate the feature flag evaluation logic.

## Acceptance Criteria
1. Feature flag works.
2. Gradual rollout enabled.
3. Component library tested with ACME.

## Comments
- **Neha Kapoor:** The component library is ready behind a feature flag.
- **Rahul Sharma:** The feature flag logic is not working. Investigating.
- **Sunita Rao:** Please fix the flag and test the rollout.

## Activity Log
- 2026-05-30 09:00: Created by Sunita Rao
- 2026-06-03 10:00: Blocked

## Attachments
['Stacktrace.log']

---
*End of Issue JIRA-PLATFORM-005*
