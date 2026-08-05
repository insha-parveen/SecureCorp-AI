---
issue_id: JIRA-ACME-002
project: Customer ACME
issue_type: Story
priority: High
status: Ready for QA
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Sunita Rao
reporter: Meera Iyer
department: ENG
related_documents: ['ENG-001', 'CLIENT-001']
related_emails: ['EMAIL-059']
related_slack: ['SLK-ACME-001']
related_meetings: ['MEET-ACME-002']
created_date: 2026-06-10
updated_date: 2026-06-15
source_type: jira
tags: ['acme', 'alerting', 'tiered', 'story']
---

# Tiered alerting configuration for ACME non-critical systems

## Description
Adjust the alerting thresholds to be tier-based so ACME non-critical (Tier 2/3) systems do not generate excessive alerts.

## Background
ACME requested that alerts be tuned for their Tier 2 and Tier 3 systems as part of UAT feedback.

## Steps to Reproduce
1. Configure tier-based alerting.
2. Verify alerts for Tier 2/3 are reduced.

## Expected Behaviour
Alerts appropriate per system tier.

## Actual Behaviour
Current alerts are too sensitive for non-critical systems.

## Business Impact
ACME UAT feedback; affects client satisfaction.

## Technical Notes
Implement tiered alerting per ENG-001 architecture.

## Acceptance Criteria
1. Tier-based alerting.
2. Dashboard tier classification.
3. ACME sign-off.

## Comments
- **Meera Iyer:** They feel the alerts are too sensitive for their non-critical systems.
- **Sunita Rao:** We can adjust the alerting configuration per system tier. The architecture in ENG-001 supports tiered alerting.
- **Neha Kapoor:** I can update the dashboard to show the tier classification.

## Activity Log
- 2026-06-10 14:10: Created by Meera Iyer
- 2026-06-15 10:00: Ready for QA

## Attachments
['none']

---
*End of Issue JIRA-ACME-002*
