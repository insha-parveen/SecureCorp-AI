---
github_id: GH-DISC-004
repository: securecorp-backend
artifact_type: discussion
classification: department_internal
allowed_roles: [manager, it, admin]
author: Neha Kapoor
reviewers: ['Sunita Rao', 'Rahul Sharma']
assignees: []
related_documents: ['PM-001', 'ENG-003']
related_jira: ['JIRA-PLATFORM-002']
related_slack: ['SLK-ENG-BE-002']
related_emails: ['none']
related_meetings: ['MEET-ENG-001']
related_project: Internal Platform
created_date: 2026-06-06
updated_date: 2026-06-08
source_type: github
tags: ['hybrid-search', 'bm25', 'dense-retrieval', 'cross-encoder']
---

# [Discussion] Hybrid Search improvements - BM25 + Dense Retrieval + Cross-Encoder

## Description
Discussion on the hybrid search pipeline: combining BM25 lexical search with dense retrieval and Cross-Encoder reranking for the internal platform.

The hybrid search currently uses a balance of BM25 and dense retrieval. With the Cross-Encoder reranker optimization (PR GH-PR-005), we should evaluate:

1. Optimal BM25 vs dense retrieval weightings
2. Cross-Encoder top-k reranking size
3. Latency budget per query

## Replies
- Rahul Sharma: The reranker optimization reduced latency by 40%. We can now afford a larger top-k.
- Sunita Rao: Let's benchmark different weightings on the internal query set.
- Neha Kapoor: I'll update the benchmark suite to include the new reranker settings.

---
*End of GH-DISC-004*
