---
issue_id: JIRA-ORION-004
project: Project Orion
issue_type: Spike
priority: Medium
status: Done
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rahul Sharma
reporter: Sunita Rao
department: ENG
related_documents: ['ENG-001']
related_emails: ['EMAIL-075']
related_slack: ['SLK-ATLAS-002']
related_meetings: ['MEET-ATLAS-001']
created_date: 2026-04-22
updated_date: 2026-04-30
source_type: jira
tags: ['streaming', 'analytics', 'project-atlas', 'spike']
---

# Evaluate streaming-first approach for Project Atlas analytics

## Description
Evaluate whether a streaming-first approach for the analytics data pipeline is necessary to support Project Atlas near real-time analytics requirements.

## Background
Project Atlas client requires near real-time analytics, which differs from the batch-oriented pipeline in Project Orion. This spike evaluates the architectural options.

## Steps to Reproduce
1. Review current Orion data pipeline architecture in ENG-001.
2. Evaluate streaming technologies.
3. Assess effort for Atlas.

## Expected Behaviour
Recommendation on whether to adopt streaming-first for Atlas.

## Actual Behaviour
No recommendation yet.

## Business Impact
Supports decision-making for Project Atlas architecture.

## Technical Notes
Streaming-first approach may be needed for near real-time analytics in Atlas.

## Acceptance Criteria
1. Publish evaluation results.
2. Recommend approach.
3. Document risks.

## Comments
- **Sunita Rao:** Valid point. We may need a streaming-first approach for Atlas.
- **Neha Kapoor:** Evaluated Kafka and Flink options. Recommendation attached.

## Activity Log
- 2026-04-22 14:00: Created by Sunita Rao
- 2026-04-30 16:00: Evaluation complete, mark Done

## Attachments
['Architecture.png']

---
*End of Issue JIRA-ORION-004*
