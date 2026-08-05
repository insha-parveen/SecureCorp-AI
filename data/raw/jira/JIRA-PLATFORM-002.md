---
issue_id: JIRA-PLATFORM-002
project: Internal Platform
issue_type: Improvement
priority: Medium
status: Code Review
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Neha Kapoor
reporter: Sunita Rao
department: ENG
related_documents: ['PM-001', 'ENG-003']
related_emails: ['none']
related_slack: ['SLK-ENG-BE-002']
related_meetings: ['MEET-ENG-001']
created_date: 2026-06-02
updated_date: 2026-06-08
source_type: jira
tags: ['internal-platform', 'search', 'reranker', 'improvement']
---

# Hybrid search enhancement - Cross-Encoder reranker optimization

## Description
Optimize the hybrid search enhancement and Cross-Encoder reranker to improve search relevance and performance.

## Background
The internal platform's hybrid search uses a Cross-Encoder reranker. The optimization aims to improve relevance scores and reduce inference latency.

## Steps to Reproduce
1. Run a set of test queries.
2. Measure relevance and latency.
3. Compare with current baseline.

## Expected Behaviour
Improved relevance and reduced reranker latency.

## Actual Behaviour
Current reranker is accurate but slow for large result sets.

## Business Impact
Slow search responses affect internal tooling and client-facing features.

## Technical Notes
Optimize the Cross-Encoder reranker model and batching per PM-001 AI strategy.

## Acceptance Criteria
1. Optimized reranker.
2. Measured relevance improvement.
3. Reduced latency.

## Comments
- **Sunita Rao:** The Cross-Encoder reranker is a key part of the hybrid search enhancement.
- **Neha Kapoor:** Optimized the batching and model. Code review requested.

## Activity Log
- 2026-06-02 10:00: Created by Sunita Rao
- 2026-06-08 14:00: Code Review

## Attachments
['Profiler_Report.pdf']

---
*End of Issue JIRA-PLATFORM-002*
