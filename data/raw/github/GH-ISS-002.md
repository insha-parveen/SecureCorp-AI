---
github_id: GH-ISS-002
repository: securecorp-frontend
artifact_type: issue
classification: department_internal
allowed_roles: [manager, it, admin]
author: Rahul Sharma
reviewers: ['Sunita Rao']
assignees: ['Neha Kapoor']
related_documents: ['ENG-004']
related_jira: ['JIRA-PLATFORM-005']
related_slack: ['SLK-ENG-FE-002']
related_emails: ['EMAIL-067']
related_meetings: ['MEET-ENG-001']
related_project: Internal Platform
created_date: 2026-05-30
updated_date: 2026-06-03
source_type: github
tags: ['deployment', 'feature-flag', 'bug']
---

# [Issue] Feature flag not working for dashboard component library

## Problem
The feature flag for the new dashboard component library does not properly enable/disable the new components.

## Reproduction
1. Toggle the feature flag.
2. Attempt to use the component library.
3. Observe whether the components change.

## Expected Result
Feature flag correctly controls component library availability.

## Actual Result
Component library appears regardless of flag state.

## Discussion
- Neha Kapoor: The component library is ready behind the feature flag per the architecture review.
- Rahul Sharma: Investigating the flag evaluation logic - it looks like the flag is not being read correctly.
- Sunita Rao: Please fix the flag and test the gradual rollout.

## Labels
bug, deployment, p1

## Milestone
Internal Platform Q2

---
*End of GH-ISS-002*
