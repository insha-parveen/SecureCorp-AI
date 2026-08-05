# Company Bible — NexaCore Solutions Pvt. Ltd.

> **Canonical source of truth for all synthetic corpus generation.**
> Every generated document (policy, SOP, announcement, incident report) and every structured record (employees, invoices, tickets) MUST stay consistent with this file.
> If a new document needs a person, department, ID, or date not listed here — add it here FIRST, then use it. Never invent inline.

---

## 1. Company Overview

- **Name:** NexaCore Solutions Pvt. Ltd.
- **Industry:** Technology / software consulting / cloud solutions / managed IT services
- **Founded:** 2014
- **Size:** ~250 employees
- **Fiscal year:** April 1 – March 31 (Indian FY convention, since HQ is in Lucknow)
- **Current "as of" date for documents:** 2026 (matches project's real-world timeline)

---

## 2. Locations

| Code | City | Country | Role |
|---|---|---|---|
| `LKO` | Lucknow | India | Headquarters, Engineering, Admin |
| `BLR` | Bengaluru | India | Engineering, Sales |
| `DXB` | Dubai | UAE | Sales, Client Delivery (MEA region) |
| `SIN` | Singapore | Singapore | APAC regional office |

---

## 3. Departments

| Department | Code | Head Count (approx) |
|---|---|---|
| Human Resources | `HR` | 12 |
| Engineering | `ENG` | 95 |
| Finance | `FIN` | 20 |
| Operations | `OPS` | 30 |
| Sales | `SALES` | 40 |
| IT and Security | `ITSEC` | 25 |
| Administration | `ADMIN` | 28 |

---

## 4. Key People (use these names consistently — do not invent new leadership)

| Name | Role | Department | Location | Employee ID |
|---|---|---|---|---|
| Arvind Malhotra | CEO | Administration | Lucknow | EMP-0001 |
| Sunita Rao | VP Engineering | Engineering | Bengaluru | EMP-0002 |
| Kabir Nair | CFO | Finance | Lucknow | EMP-0003 |
| Farah Hussain | Head of HR | HR | Lucknow | EMP-0004 |
| Rohit Verma | Head of IT & Security (CISO) | IT and Security | Lucknow | EMP-0005 |
| Meera Iyer | VP Sales | Sales | Dubai | EMP-0006 |
| Daniel Lim | APAC Regional Manager | Sales | Singapore | EMP-0007 |
| Ayesha Khan | Head of Operations | Operations | Lucknow | EMP-0008 |

For all other employees referenced in documents/records, generate names + `EMP-XXXX` IDs on the fly but **log them in Section 8 (Growing Reference Log)** so later documents stay consistent.

---

## 5. ID / Document Numbering Schemes

| Entity | Format | Example |
|---|---|---|
| Employee | `EMP-NNNN` | `EMP-0104` |
| Invoice | `INV-YYYY-NNNN` | `INV-2026-0108` |
| Incident report | `INC-NNNN` | `INC-1042` |
| Purchase order | `PO-NNNN` | `PO-8491` |
| IT asset (laptop) | `LAP-NNN` | `LAP-220` |
| IT ticket | `TCK-NNNN` | `TCK-3305` |
| Expense claim | `EXP-NNNN` | `EXP-0567` |
| Policy document | `<DEPT>-NNN` | `HR-003`, `FIN-002`, `ITSEC-001` |
| Vendor | `VEN-NNN` | `VEN-014` |

**Rule:** IDs are never reused, even across document versions. A new version of `HR-003` stays `HR-003` but gets a new `document_version` (see Section 6).

---

## 6. Document Versioning Convention

- `document_version` format: `v1`, `v2`, `v3`...
- Every policy document type should have **at least one older version** with an earlier `effective_date`, so ingestion/retrieval must handle "which version is current" correctly.
- `status` field: `draft`, `active`, `superseded`, `archived`.
- When a document is superseded, the old version's `status` becomes `superseded` and it stays in the corpus (tests "does retrieval correctly prefer the active version").

---

## 6a. Canonical Document Metadata

Every generated document MUST carry this metadata (used by ingestion, indexing, retrieval, and authorization):

| Field | Meaning |
|---|---|
| `document_id` | Stable ID per Section 5 numbering (e.g. `HR-003`). Never changes across versions. |
| `title` | Human-readable document title. |
| `document_type` | `policy` \| `sop` \| `announcement` \| `incident_report`. |
| `department` | Owning department code from Section 3. |
| `classification` | One of Section 7's levels (`public`, `department_internal`, `restricted`, `confidential`). |
| `allowed_roles` | Roles permitted to view (e.g. `["employee","manager","hr","admin"]`). |
| `allowed_departments` | Departments permitted to view, if scope is department-limited. |
| `owner_department` | Department accountable for the document's accuracy/updates (usually same as `department`). |
| `document_version` | `v1`, `v2`, ... per Section 6. |
| `effective_date` | Date the version takes effect. |
| `status` | `draft` \| `active` \| `superseded` \| `archived`. |
| `created_date` | When this version was authored. |
| `last_reviewed_date` | Most recent review date. |
| `supersedes_document_version` | Prior version this replaces, if any (e.g. `v1`). |
| `source_type` | `generated` (synthetic corpus) — reserved for future non-synthetic sources. |

**Example — `HR-003` v2 (Remote Work Policy):**

```json
{
  "document_id": "HR-003",
  "title": "Remote Work Policy",
  "document_type": "policy",
  "department": "HR",
  "classification": "public",
  "allowed_roles": ["employee", "manager", "hr", "finance", "it", "admin"],
  "allowed_departments": ["*"],
  "owner_department": "HR",
  "document_version": "v2",
  "effective_date": "2026-06-01",
  "status": "active",
  "created_date": "2026-05-20",
  "last_reviewed_date": "2026-05-20",
  "supersedes_document_version": "v1",
  "source_type": "generated"
}
```

---

## 7. Classification & Access Levels (maps to Authorization Model)

| Classification | Meaning | Typically allowed roles |
|---|---|---|
| `public` | All employees | `employee`, `manager`, `hr`, `finance`, `it`, `admin` |
| `department_internal` | Department + managers/admin | department role + `admin` |
| `restricted` | Named roles only | e.g. `hr`, `admin` for personal records |
| `confidential` | Very narrow scope | `admin` + explicit owner/scope |

---

### Authorization Dimensions

Access decisions may depend on any combination of:

1. **Role** — employee / manager / hr / finance / it / admin.
2. **Department** — does the requester belong to the owning/allowed department?
3. **User ownership** — is the requester the subject of a personal record (own leave balance, own expense claim)?
4. **Manager scope** — does the requester manage the record's subject (per `manager_id`)?
5. **Document classification** — Section 7's levels.
6. **Tenant** — reserved for future multi-tenant scope; currently single-tenant (NexaCore only).
7. **Document version/status** — superseded/draft versions are generally not served as current answers.

**RBAC vs attribute-based constraints:** RBAC answers "does this role generally get this category of access?" (e.g., `hr` role → HR policies). Attribute-based constraints narrow that further using record-specific facts the role alone can't capture — ownership, manager scope, department match, or document status. A user can pass the RBAC check (role = `employee`) and still be denied by an attribute check (record's `employee_id` isn't theirs).

**Canonical access behavior:**

- **Employee** — can access `public` company policies; can access their own personal records (leave balance, own expense claims) when policy permits; cannot access another employee's `restricted` records.
- **Manager** — can access authorized records within their reporting/management scope (subordinates' relevant records); cannot automatically access HR-restricted information without separate authorization.
- **HR** — can access authorized HR documents and employee records within HR's mandate.
- **Finance** — can access authorized financial documents and finance records (invoices, expense approvals) within Finance's mandate.
- **IT and Security** — can access authorized IT/security documents and tickets within their mandate.
- **Admin** — broad administrative access, but **not an automatic bypass of every policy** — `confidential` records may still require explicit scope/ownership even for admin, per system policy.

---

## 7a. Structured Record Schemas

Canonical minimum fields for the SQL layer (structured data, separate from the RAG document corpus). IDs follow Section 5 formats.

### Employee
`employee_id, full_name, department, role, designation, manager_id, location, joining_date, employment_status, leave_balance, salary_band`

```json
{"employee_id":"EMP-0104","full_name":"Neha Kapoor","department":"ENG","role":"Software Engineer","designation":"SDE-2","manager_id":"EMP-0002","location":"BLR","joining_date":"2023-08-14","employment_status":"active","leave_balance":14,"salary_band":"E3"}
```

### Invoice
`invoice_id, vendor_id, vendor_name, invoice_date, department, purchase_order_id, description, subtotal, tax, total, currency, payment_status, approver_id`

```json
{"invoice_id":"INV-2026-0108","vendor_id":"VEN-014","vendor_name":"Bluewave Cloud Services","invoice_date":"2026-05-10","department":"ENG","purchase_order_id":"PO-8491","description":"Cloud hosting - May 2026","subtotal":185000,"tax":33300,"total":218300,"currency":"INR","payment_status":"paid","approver_id":"EMP-0003"}
```

### Expense Claim
`expense_id, employee_id, expense_type, expense_date, amount, currency, description, approval_status, approver_id`

```json
{"expense_id":"EXP-0567","employee_id":"EMP-0104","expense_type":"travel","expense_date":"2026-04-22","amount":6200,"currency":"INR","description":"Client visit - Bengaluru to Dubai","approval_status":"approved","approver_id":"EMP-0002"}
```

### IT Ticket
`ticket_id, reported_by, department, category, priority, status, created_at, resolved_at, assigned_to, resolution_summary`

```json
{"ticket_id":"TCK-3305","reported_by":"EMP-0104","department":"ENG","category":"access_request","priority":"medium","status":"resolved","created_at":"2026-03-01T10:15:00","resolved_at":"2026-03-02T09:40:00","assigned_to":"EMP-0005","resolution_summary":"VPN access granted after manager approval."}
```

### Vendor
`vendor_id, vendor_name, category, contact_email, active_status`

### Purchase Order
`purchase_order_id, vendor_id, department, description, amount, currency, status, created_date`

### IT Asset
`asset_id, asset_type, assigned_to, purchase_date, status` (asset_id uses `LAP-NNN` for laptops; extend prefix per asset type if needed)

---

## 7b. Canonical Dataset Reference Date

- **Dataset reference date:** 2026-08-01
- **Current fiscal year:** FY2026-27 (fiscal convention unchanged — April 1 to March 31, per Section 1)

**Consistency rules:**
- Active documents should have an `effective_date` on or before the dataset reference date.
- Future-dated documents should normally be `draft` unless explicitly marked as scheduled.
- Superseded documents remain in the corpus for retrieval/versioning evaluation.
- At any point in time, current/active versions must be clearly distinguishable from superseded ones via `status`.

---

## 7c. Canonical Business Rules

These values are canonical across the entire generated corpus. A rule only changes via an explicit new document version (recorded in the Growing Reference Log).

| Rule | Canonical Value |
|---|---|
| Annual Leave entitlement | 18 days/year |
| Sick Leave entitlement | 10 days/year |
| Remote Work standard weekly limit | 2 days/week |
| Extended Remote Work approval | Requires Reporting Manager + HR sign-off, reviewed quarterly |
| Expense Reimbursement submission deadline | Within 30 days of expense date |
| Invoice approval thresholds | Up to ₹50,000: Department Manager. ₹50,001–₹500,000: Finance Manager (department-level finance approver, `EMP-XXXX` — add to Growing Reference Log when first used). Above ₹500,000: CFO (Kabir Nair, EMP-0003) approval required. |

---

## 8. Growing Reference Log (append as new entities are generated)

> Keep this updated every time a document generation batch introduces a new employee, vendor, or ID — this prevents duplicate/contradictory facts across documents.

### Employees (beyond Section 4)
| Name | Role | Department | Location | Employee ID |
|---|---|---|---|---|
| Siddharth Mehta | Finance Manager | Finance | Lucknow | EMP-0011 |


### Vendors
_(none yet — add as generated)_

### Document Registry (all generated docs, for cross-reference checks)

| Document ID | Title | Type | Dept | Version | Effective Date | Status | Classification | Supersedes | Related Docs | File Path |
|---|---|---|---|---|---|---|---|---|---|---|
| `HR-001` | Employee Handbook | policy | HR | v1 | 2025-01-01 | active | public | null | HR-002, HR-003, HR-006, HR-008 | `data/raw/company_policies/HR-001_employee_handbook_v1.md` |
| `HR-002` | Leave Policy | policy | HR | v1 | 2025-01-01 | active | public | null | HR-001, HR-008 | `data/raw/company_policies/HR-002_leave_policy_v1.md` |
| `HR-003` | Remote Work Policy | policy | HR | v1 | 2025-01-01 | active | public | null | HR-001, ITSEC-001 | `data/raw/company_policies/HR-003_remote_work_policy_v1.md` |
| `HR-004` | Travel and Expense Policy | policy | HR | v1 | 2025-01-01 | active | public | null | HR-001, FIN-001 | `data/raw/company_policies/HR-004_travel_and_expense_policy_v1.md` |
| `HR-005` | Performance Review Policy | policy | HR | v1 | 2025-01-01 | active | public | null | HR-001, HR-006 | `data/raw/company_policies/HR-005_performance_review_policy_v1.md` |
| `HR-006` | Code of Conduct | policy | HR | v1 | 2025-01-01 | active | public | null | HR-001, HR-008, ITSEC-001 | `data/raw/company_policies/HR-006_code_of_conduct_v1.md` |
| `HR-007` | Employee Exit Procedure | policy | HR | v1 | 2025-01-01 | active | public | null | HR-001, ITSEC-001, ITSEC-004 | `data/raw/company_policies/HR-007_employee_exit_procedure_v1.md` |
| `HR-008` | Workplace Complaint and Grievance Procedure | policy | HR | v1 | 2025-01-01 | active | public | null | HR-001, HR-002, HR-006 | `data/raw/company_policies/HR-008_workplace_complaint_grievance_procedure_v1.md` |
| `FIN-001` | Procurement Policy | policy | Finance | v1 | 2025-01-01 | active | public | null | FIN-002, HR-006 | `data/raw/finance/FIN-001_procurement_policy_v1.md` |
| `FIN-002` | Invoice Approval SOP | sop | Finance | v1 | 2025-01-01 | active | public | null | FIN-001, HR-006 | `data/raw/finance/FIN-002_invoice_approval_sop_v1.md` |
| `FIN-003` | Expense Reimbursement Policy | policy | Finance | v1 | 2025-01-01 | active | public | null | HR-004, HR-001 | `data/raw/finance/FIN-003_expense_reimbursement_policy_v1.md` |
| `ITSEC-001` | Information Security Policy | policy | ITSEC | v1 | 2026-01-15 | active | public | null | ITSEC-002, ITSEC-003, ITSEC-005, ITSEC-006, ITSEC-008, HR-003, HR-006, HR-007, FIN-001 | `data/raw/it_security/ITSEC-001_information_security_policy_v1.md` |
| `ITSEC-002` | Password Policy | policy | ITSEC | v1 | 2026-01-15 | active | public | null | ITSEC-001, ITSEC-003, ITSEC-005, ITSEC-008, HR-006 | `data/raw/it_security/ITSEC-002_password_policy_v1.md` |
| `ITSEC-003` | Acceptable Use Policy | policy | ITSEC | v1 | 2026-01-15 | active | public | null | ITSEC-001, ITSEC-002, ITSEC-005, ITSEC-006, HR-006, HR-003 | `data/raw/it_security/ITSEC-003_acceptable_use_policy_v1.md` |
| `ITSEC-004` | Employee Offboarding Checklist | sop | ITSEC | v1 | 2026-01-15 | active | department_internal | null | ITSEC-001, HR-007, FIN-003, HR-002, ITSEC-005 | `data/raw/it_security/ITSEC-004_employee_offboarding_checklist_v1.md` |
| `ITSEC-005` | Incident Response Plan | policy | ITSEC | v1 | 2026-01-15 | active | department_internal | null | ITSEC-001, ITSEC-002, ITSEC-003, ITSEC-006, HR-006, HR-007 | `data/raw/it_security/ITSEC-005_incident_response_plan_v1.md` |
| `ITSEC-006` | Data Classification Policy | policy | ITSEC | v1 | 2026-01-15 | active | public | null | ITSEC-001, ITSEC-003, ITSEC-005, ITSEC-007, HR-006, FIN-001 | `data/raw/it_security/ITSEC-006_data_classification_policy_v1.md` |
| `ITSEC-007` | Backup & Disaster Recovery Policy | policy | ITSEC | v1 | 2026-01-15 | active | department_internal | null | ITSEC-001, ITSEC-005, ITSEC-006, FIN-001 | `data/raw/it_security/ITSEC-007_backup_disaster_recovery_policy_v1.md` |
| `ITSEC-008` | VPN & Remote Access Policy | policy | ITSEC | v1 | 2026-01-15 | active | public | null | ITSEC-001, ITSEC-002, ITSEC-003, ITSEC-006, HR-003, ITSEC-004, ITSEC-005 | `data/raw/it_security/ITSEC-008_vpn_remote_access_policy_v1.md` |
| `ENG-001` | Project Orion Architecture Overview | project_doc | ENG | v1 | 2026-02-10 | active | department_internal | null | ENG-002, ENG-004, SEC-001, ITSEC-001, ITSEC-006, ITSEC-007, OPS-002, PM-001 | `data/raw/google_drive/ENG-001_project_orion_architecture_overview_v1.md` |
| `ENG-002` | Cloud Migration Plan | project_doc | ENG | v1 | 2026-02-20 | active | department_internal | null | ENG-001, ITSEC-001, ITSEC-006, ITSEC-007, ITSEC-008, OPS-001, CLIENT-001, FIN-001, SEC-001 | `data/raw/google_drive/ENG-002_cloud_migration_plan_v1.md` |
| `ENG-003` | API Design Guidelines | engineering_guide | ENG | v1 | 2026-02-15 | active | public | null | ENG-001, ENG-004, ITSEC-001, ITSEC-002, ITSEC-006, OPS-001 | `data/raw/google_drive/ENG-003_api_design_guidelines_v1.md` |
| `ENG-004` | Engineering Handbook | engineering_guide | ENG | v1 | 2026-02-01 | active | department_internal | null | ENG-001, ENG-002, ENG-003, HR-001, HR-005, ITSEC-001, ITSEC-006, PM-001, OPS-001, SEC-001 | `data/raw/google_drive/ENG-004_engineering_handbook_v1.md` |
| `OPS-001` | Customer Onboarding Guide | operations_guide | OPS | v1 | 2026-02-05 | active | department_internal | null | ENG-003, ENG-004, HR-001, HR-003, ITSEC-001, ITSEC-006, CLIENT-001, OPS-003 | `data/raw/google_drive/OPS-001_customer_onboarding_guide_v1.md` |
| `OPS-002` | Disaster Recovery Test Report | incident_report | OPS | v1 | 2026-02-25 | active | department_internal | null | ENG-001, ITSEC-005, ITSEC-006, ITSEC-007, OPS-003, SEC-001 | `data/raw/google_drive/OPS-002_disaster_recovery_test_report_v1.md` |
| `OPS-003` | Quarterly Operations Report | operations_report | OPS | v1 | 2026-04-10 | active | department_internal | null | ENG-001, ENG-002, OPS-001, OPS-002, SEC-001, PM-001, CLIENT-001, ITSEC-007 | `data/raw/google_drive/OPS-003_quarterly_operations_report_v1.md` |
| `SEC-001` | Security Audit Report Q1 2026 | audit_report | ITSEC | v1 | 2026-03-30 | active | restricted | null | ITSEC-001, ITSEC-002, ITSEC-003, ITSEC-005, ITSEC-006, ENG-001, OPS-003, OPS-002 | `data/raw/google_drive/SEC-001_security_audit_report_q1_2026_v1.md` |
| `PM-001` | AI Adoption Strategy | strategy_doc | ADMIN | v1 | 2026-03-15 | active | department_internal | null | ENG-001, ENG-004, ITSEC-001, ITSEC-006, OPS-003, OPS-001, SEC-001 | `data/raw/google_drive/PM-001_ai_adoption_strategy_v1.md` |
| `CLIENT-001` | ACME Manufacturing Implementation Plan | client_plan | OPS | v1 | 2026-03-01 | active | restricted | null | OPS-001, ENG-001, ENG-002, ENG-003, ITSEC-001, ITSEC-006, HR-003, HR-001 | `data/raw/google_drive/CLIENT-001_acme_manufacturing_implementation_plan_v1.md` |
| `SLACK-CORPUS` | Slack Workspace Corpus | slack_corpus | ALL | v1 | 2026-03-03 | active | department_internal | null | HR-001, HR-002, HR-003, HR-004, HR-006, FIN-001, FIN-002, FIN-003, ITSEC-001, ITSEC-002, ITSEC-005, ITSEC-006, ITSEC-007, ITSEC-008, ENG-001, ENG-002, ENG-003, OPS-001, OPS-002, OPS-003, SEC-001, PM-001, CLIENT-001 | `data/raw/slack/` |
| `JIRA-CORPUS` | Jira Project Corpus | jira_corpus | ALL | v1 | 2026-02-08 | active | department_internal | null | ENG-001, ENG-002, ENG-003, ENG-004, ITSEC-001, ITSEC-002, ITSEC-005, ITSEC-006, ITSEC-007, FIN-001, FIN-002, FIN-003, HR-006, SEC-001, OPS-002, OPS-003, PM-001, CLIENT-001 | `data/raw/jira/` |
| `GITHUB-CORPUS` | GitHub Repository Corpus | github_corpus | ALL | v1 | 2026-02-09 | active | department_internal | null | ENG-001, ENG-002, ENG-003, ENG-004, ITSEC-001, ITSEC-002, ITSEC-006, ITSEC-007, FIN-001, FIN-003, SEC-001, OPS-002, PM-001, CLIENT-001 | `data/raw/github/` |
| `EMAIL-CORPUS` | Enterprise Email Archive | email | ALL | v1 | 2026-01-01 | active | mixed | null | ALL | `data/raw/emails/` |
| `MEETING-CORPUS` | Enterprise Meeting Transcripts | meeting | ALL | v1 | 2026-01-01 | active | mixed | null | ALL | `data/raw/meetings/` |


---

## 9. Terminology Glossary (keep consistent — do not vary wording across documents)

| Concept | Canonical term (always use this) | Avoid |
|---|---|---|
| Working from home | "Remote Work" | "WFH", "Work From Home" (unless quoting policy title exactly once) |
| Time off | "Leave" | "Vacation", "PTO" |
| Manager approval chain | "Reporting Manager" | "Line Manager", "Supervisor" |
| Money claims | "Expense Reimbursement" | "Expense Reporting" |
| Security event | "Security Incident" | "Security Event", "Breach" (unless severity warrants) |

---

## 10. Tone & Style Notes for Generated Documents

- Policies: formal, third-person, numbered sections, dated.
- SOPs: imperative/procedural ("Step 1: Submit the request via...").
- Announcements: shorter, first-person plural ("We are updating..."), always include effective date + required action.
- Incident reports: neutral, factual, structured (Summary → Timeline → Root Cause → Recommendations).
- Do not make every document the same length or structure — vary realistically within these target ranges (not hard constraints):

| Document type | Target word count |
|---|---|
| Policy | ~1,500–2,500 |
| SOP | ~1,800–3,000 |
| Announcement | ~400–900 |
| Incident report | ~1,500–3,000 |

---

## 11. Cross-Document Consistency Rules

- A person must have one canonical `employee_id`; a vendor must have one canonical `vendor_id`. IDs are never reused.
- A policy's `document_id` stays stable across versions; `document_version` changes when the policy is revised.
- Only one version should normally be `active` per document at a time; superseded versions remain in the corpus.
- Related documents (e.g. an announcement tied to a policy) must reference each other by canonical `document_id`.
- Canonical business rules (Section 7c) stay fixed unless an explicit version change records the update.
- New entities (people, vendors) must first be added to the Growing Reference Log (Section 8) before appearing in generated documents.
