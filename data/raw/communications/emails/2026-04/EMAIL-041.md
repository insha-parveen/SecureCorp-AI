---
email_id: EMAIL-041
source_type: email
classification: department_internal
allowed_roles: ['manager', 'it', 'admin']
department: OPS
owner: Ayesha Khan
participants: ['Ayesha Khan', 'Sunita Rao', 'Rahul Sharma', 'Neha Kapoor']
related_project: Project Orion
related_documents: ['ENG-001']
created_date: 2026-04-12
tags: ['operations', 'performance', 'incident', 'project-orion']
---

# Analytics Latency Issue - Investigation

**From:** Ayesha Khan

**To:** Sunita Rao; Rahul Sharma; Neha Kapoor

**Date:** 2026-04-12

**Time:** 14:00

**Subject:** Analytics Latency Issue - Investigation

**Priority:** High

**Classification:** department_internal

**Department:** OPS

**Project:** Project Orion

**Attachments:** None

**Body:**

Hi team,

The analytics dashboard is showing old data - it's lagging by about an hour. This was reported in #project-orion.

Rahul is investigating the ingestion pipeline. The queue depth is high, suggesting a backpressure issue. We may need to scale the ingestion workers per the architecture in ENG-001.

Please prioritize this - the client is asking about the delay.

Best regards,
Ayesha Khan
Head of Operations, NexaCore Solutions Pvt. Ltd.
EMP-0008
