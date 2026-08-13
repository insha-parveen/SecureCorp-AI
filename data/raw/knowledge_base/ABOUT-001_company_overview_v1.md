---
document_id: ABOUT-001
title: NexaCore Company Overview
document_type: knowledge_base_article
department: ADMIN
classification: public
allowed_roles:
  - employee
  - manager
  - hr
  - finance
  - it
  - admin
allowed_departments:
  - "*"
owner_department: ADMIN
document_version: v1
effective_date: 2026-01-01
status: active
created_date: 2026-01-01
last_reviewed_date: 2026-01-01
supersedes_document_version: null
related_documents:
  - HR-001
  - HR-002
  - HR-003
  - HR-006
tags:
  - company-overview
  - about
  - mission
  - locations
  - departments
source_type: knowledge_base
---

# NexaCore Company Overview

## 1. Purpose

This document is the canonical company-level reference for the facts that
employees and other stakeholders most commonly ask about NexaCore Solutions
Pvt. Ltd. — what the company does, where it operates, how many people it
employs, when it was founded, and who leads each function. For deeper
policy detail, refer to the related documents listed above.

## 2. Company at a Glance

| Field | Value |
|---|---|
| **Legal name** | NexaCore Solutions Pvt. Ltd. |
| **Industry** | Technology — software consulting, cloud solutions, managed IT services |
| **Founded** | 2014 |
| **Approximate size** | ~250 employees |
| **Fiscal year** | April 1 – March 31 (Indian FY convention; headquarters are in Lucknow) |
| **Headquarters** | Lucknow, India (location code `LKO`) |

## 3. What NexaCore Does

NexaCore Solutions Pvt. Ltd. operates as a technology and managed-IT
services partner for enterprise customers. The company's practice areas
span four closely related lines of business:

- **Software consulting** — architecture advisory, custom application
  development, and engineering enablement for client teams.
- **Cloud solutions** — cloud architecture, migration planning, and
  ongoing cloud-platform operations.
- **Managed IT services** — outsourced operations for client
  infrastructure, observability, and incident response.
- **Software products** — internal platforms (for example, Project
  Orion, the company's flagship managed-services platform) used to
  differentiate the delivery of the services above.

## 4. Locations

NexaCore operates from four primary locations. The headquarters is in
Lucknow.

| Code | City | Country | Role |
|---|---|---|---|
| `LKO` | Lucknow | India | **Headquarters** — Engineering, Administration |
| `BLR` | Bengaluru | India | Engineering, Sales |
| `DXB` | Dubai | UAE | Sales, Client Delivery (MEA region) |
| `SIN` | Singapore | Singapore | APAC regional office |

## 5. Departments

NexaCore is organized into the seven departments listed below. Department
head counts are approximate and intended for high-level context only;
authoritative employee counts are maintained in the structured employee
dataset, not in this document.

| Department | Code | Approx. Head Count |
|---|---|---|
| Human Resources | `HR` | 12 |
| Engineering | `ENG` | 95 |
| Finance | `FIN` | 20 |
| Operations | `OPS` | 30 |
| Sales | `SALES` | 40 |
| IT and Security | `ITSEC` | 25 |
| Administration | `ADMIN` | 28 |

## 6. Leadership

The following named individuals lead NexaCore's major functions. Each is
referenced by canonical `employee_id` (per the project-wide ID scheme) so
that downstream documents and structured records can cite them without
ambiguity.

| Name | Role | Department | Location | Employee ID |
|---|---|---|---|---|
| Arvind Malhotra | CEO | Administration | Lucknow | `EMP-0001` |
| Sunita Rao | VP Engineering | Engineering | Bengaluru | `EMP-0002` |
| Kabir Nair | CFO | Finance | Lucknow | `EMP-0003` |
| Farah Hussain | Head of HR | Human Resources | Lucknow | `EMP-0004` |
| Rohit Verma | Head of IT & Security (CISO) | IT and Security | Lucknow | `EMP-0005` |
| Meera Iyer | VP Sales | Sales | Dubai | `EMP-0006` |
| Daniel Lim | APAC Regional Manager | Sales | Singapore | `EMP-0007` |
| Ayesha Khan | Head of Operations | Operations | Lucknow | `EMP-0008` |

## 7. Canonical Business Rules

The following values are company-wide canonical rules, consistent across
all NexaCore policies and procedures. They are reproduced here so that
"how many leave days do employees get" or "what is the expense
submission deadline" can be answered from a single overview document;
the underlying policies (linked above) remain authoritative for
exception handling.

| Rule | Canonical Value |
|---|---|
| Annual Leave entitlement | 18 days per year |
| Sick Leave entitlement | 10 days per year |
| Remote Work standard weekly limit | 2 days per week |
| Extended Remote Work approval | Requires Reporting Manager + HR sign-off, reviewed quarterly |
| Expense Reimbursement submission deadline | Within 30 days of expense date |
| Invoice approval — up to ₹50,000 | Department Manager approval |
| Invoice approval — ₹50,001 to ₹500,000 | Finance Manager approval |
| Invoice approval — above ₹500,000 | CFO (Kabir Nair, `EMP-0003`) approval |

## 8. How to Use This Document

This document is intentionally short. For anything more specific, refer
to the linked policies:

- **What the company does day-to-day** — Employee Handbook (`HR-001`),
  Engineering Handbook (`ENG-004`).
- **Time off, sick leave, parental leave** — Leave Policy (`HR-002`).
- **Remote work rules and approvals** — Remote Work Policy (`HR-003`).
- **Conduct, ethics, and grievance handling** — Code of Conduct
  (`HR-006`), Workplace Complaint and Grievance Procedure (`HR-008`).

For structured facts that change more frequently (current employee
headcount by department, open ticket count, pending invoice approvals),
use the structured-data path rather than this document.

## 9. Provenance

All factual content in this document is derived from the project-wide
canonical reference (`docs/company_bible.md`), Sections 1, 2, 3, 4,
and 7c. No facts have been introduced that are not present in that
source.
</content>
</invoke>