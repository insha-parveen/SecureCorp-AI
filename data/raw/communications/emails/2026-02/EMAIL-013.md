---
email_id: EMAIL-013
source_type: email
classification: department_internal
allowed_roles: ['manager', 'it', 'admin']
department: ENG
owner: Sunita Rao
participants: ['Sunita Rao', 'Rohit Verma', 'Kabir Nair']
related_project: Project Orion
related_documents: ['ENG-001', 'ITSEC-002']
created_date: 2026-02-08
tags: ['engineering', 'security', 'architecture-review', 'project-orion']
---

# Project Orion Architecture Review - Security Section

**From:** Sunita Rao

**To:** Rohit Verma

**CC:** Kabir Nair

**Date:** 2026-02-08

**Time:** 14:00

**Subject:** Project Orion Architecture Review - Security Section

**Priority:** High

**Classification:** department_internal

**Department:** ENG

**Project:** Project Orion

**Attachments:** ENG-001_Architecture_v3.pdf

**Body:**

Hi Rohit,

During today's architecture review we noticed that the authentication service still doesn't fully align with ITSEC-002 Password Policy. The refresh token validation needs to be updated before the next release.

Could you review the proposed changes before tomorrow's release? The architecture is documented in ENG-001.

Also, we discussed this in #project-orion on Slack - please see that thread for context.

Thanks,
Sunita Rao
VP Engineering, NexaCore Solutions Pvt. Ltd.
EMP-0002
