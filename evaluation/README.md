# SecureCorp AI Hybrid RAG Evaluation Dataset

Enterprise evaluation corpus for the Hybrid RAG project. All questions, answers, and expected documents reference real entities from the existing NexaCore enterprise corpus. No fabricated content is included.

## Directory Structure

```
evaluation/
  golden_set/
    qa_pairs.json          - 120 golden QA pairs
    qa_pairs_hard.json     - 40 hard multi-document QA pairs
  retrieval_eval/
    retrieval_queries.json - 80 retrieval queries
    expected_chunks.json   - 80 expected chunk annotations
  security_eval/
    rbac_queries.json       - 50 RBAC authorization queries
    forbidden_queries.json  - 40 security attack / injection queries
  README.md                - This file
```

## Datasets

### 1. Golden QA Set (qa_pairs.json)

120 QA pairs. Each entry has: id, question, expected_answer, expected_documents, expected_roles, difficulty, category.

Category distribution: HR 30, Finance 20, IT Security 20, Knowledge Base 15, Email 10, Slack 10, Meetings 10, Jira/GitHub 5.

Difficulty distribution: Easy 40, Medium 50, Hard 30.

Question types: single-document lookup, multiple-document reasoning, policy comparison, timeline reasoning, cross-source reasoning (meeting+email+Jira, Slack+policy, GitHub+policy).

### 2. Hard QA Set (qa_pairs_hard.json)

40 difficult questions requiring reasoning across 3-5 documents spanning multiple sources (meeting+email+Jira, knowledge base+GitHub+policy, Finance+HR+Security).

### 3. Retrieval Evaluation

- retrieval_queries.json: 80 queries with query, expected_chunk_sources (exact document IDs), top_k=5.
- expected_chunks.json: 80 entries with expected_documents, expected_sections, expected_metadata, expected_document_types.

### 4. RBAC Evaluation


