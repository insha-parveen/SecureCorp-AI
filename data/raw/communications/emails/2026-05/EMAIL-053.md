---
email_id: EMAIL-053
source_type: email
classification: restricted
allowed_roles: ['manager', 'admin']
department: SALES
owner: Meera Iyer
participants: ['Meera Iyer', 'Ayesha Khan', 'Sunita Rao', 'Arvind Malhotra']
related_project: ACME Manufacturing
related_documents: ['ENG-001']
created_date: 2026-05-18
tags: ['sales', 'acme', 'performance', 'issue']
---

# ACME Manufacturing - Performance Issue Report

**From:** Meera Iyer

**To:** Ayesha Khan; Sunita Rao

**CC:** Arvind Malhotra

**Date:** 2026-05-18

**Time:** 14:00

**Subject:** ACME Manufacturing - Performance Issue Report

**Priority:** Normal

**Classification:** restricted

**Department:** SALES

**Project:** ACME Manufacturing

**Attachments:** None

**Body:**

Hi Ayesha and Sunita,

ACME reported that the dashboard is slow when viewing historical data for more than 7 days. This was discussed in #customer-acme.

Rahul is checking the query performance. The issue is that cold storage queries are not optimized for large time ranges. We may need to add caching for common historical queries per the data lifecycle section in ENG-001.

Timeline: Caching fix by end of week, pre-aggregation in the next sprint.

Best regards,
Meera Iyer
VP Sales, NexaCore Solutions Pvt. Ltd.
EMP-0006
