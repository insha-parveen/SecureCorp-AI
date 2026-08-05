---
document_id: ITSEC-004
title: Employee Offboarding Checklist
document_type: sop
department: ITSEC
classification: department_internal
allowed_roles:
  - manager
  - hr
  - it
  - admin
allowed_departments:
  - ITSEC
  - HR
owner_department: ITSEC
document_version: v1
effective_date: 2026-01-15
status: active
created_date: 2025-12-20
last_reviewed_date: 2026-01-15
supersedes_document_version: null
related_documents:
  - ITSEC-001
  - HR-007
  - FIN-003
  - HR-002
tags:
  - security
  - offboarding
  - access-revocation
  - asset-return
  - sop
source_type: generated
---

# Employee Offboarding Checklist

## 1. Purpose
The purpose of this Standard Operating Procedure (SOP) is to define the step-by-step process for securely offboarding employees from NexaCore Solutions Pvt. Ltd.'s IT systems and infrastructure. A structured offboarding process is critical to protect the company's intellectual property, client data, and internal systems from unauthorized access after an employee's departure. This checklist ensures that all digital access is revoked, all physical assets are returned, and all security obligations are met in a consistent and auditable manner.

This SOP is subordinate to and must be read in conjunction with the Information Security Policy (ITSEC-001) and the Employee Exit Procedure (HR-007), which define the overall exit framework and the responsibilities of each department.

## 2. Scope
This SOP applies to all employees of NexaCore Solutions globally, including full-time, part-time, and contractual staff, as well as interns and consultants, who are departing the company for any reason, including voluntary resignation, retirement, or termination.

## 3. Roles and Responsibilities

### 3.1 IT and Security Department
The IT and Security department, under the leadership of the CISO, **Rohit Verma**, is responsible for:
- Revoking all digital access to corporate systems.
- Collecting and verifying the return of all physical IT assets.
- Conducting a final security audit of the departing employee's activity.
- Coordinating with HR and Finance to confirm clearance.

### 3.2 Human Resources Department
The HR department, under the leadership of **Farah Hussain**, is responsible for:
- Initiating the offboarding process upon receipt of resignation or termination notice.
- Coordinating the exit interview and administrative clearance.
- Notifying the IT and Security department of the departure date.

### 3.3 Reporting Manager
The departing employee's **Reporting Manager** is responsible for:
- Confirming that all knowledge transfer is complete.
- Verifying that all project documentation is updated.
- Approving the final clearance for the employee.

### 3.4 Finance Department
The Finance department, under the leadership of the CFO, **Kabir Nair**, is responsible for:
- Confirming that there are no outstanding financial obligations.
- Processing the final settlement, including leave encashment as per the Leave Policy (HR-002).

## 4. Offboarding Timeline

### 4.1 Standard Exit
For standard exits with a notice period, the offboarding process begins as soon as the resignation is accepted and is completed by the employee's last working day.

### 4.2 Immediate Exit
For terminations for cause or other immediate exits, the offboarding process is initiated immediately, and all access is revoked at the moment the termination meeting concludes.

## 5. Step-by-Step Offboarding Procedure

### Step 1: Initiate Offboarding Ticket
The HR department creates an offboarding ticket in the IT service management system upon confirmation of the departure date. The ticket must include:
- Employee name and employee ID.
- Department and location.
- Last working day.
- Reason for departure (voluntary, termination, retirement).

### Step 2: Notify IT and Security
The HR department notifies the IT and Security department of the upcoming departure at least 5 business days before the last working day for standard exits. For immediate exits, notification is provided immediately.

### Step 3: Schedule Access Revocation
The IT and Security department schedules the revocation of all digital access for the close of business on the employee's last working day, or immediately for immediate exits. Access to be revoked includes:
- Corporate email and collaboration tools (Slack, Teams).
- VPN and remote access (refer to ITSEC-008).
- Cloud consoles (AWS, Azure, GCP).
- Internal applications and databases.
- Client portals and external systems.
- Physical badge and door access.

### Step 4: Collect Physical Assets
The IT and Security department coordinates the return of all physical assets, including:
- Laptop and charger.
- Monitor, keyboard, and mouse.
- Headset and mobile phone.
- Physical badges and access cards.
- Any specialized peripherals or equipment.

The returned assets are inspected for damage and completeness, and the asset records are updated in the IT asset management system.

### Step 5: Conduct Security Audit
The IT and Security department conducts a final audit of the departing employee's activity logs to identify any unusual behavior, such as:
- Large data downloads or exports.
- Access to sensitive systems outside of normal working hours.
- Forwarding of corporate emails to personal accounts.
- Attempts to access systems after the departure date.

Any suspicious activity is escalated to the CISO and may be investigated under the Incident Response Plan (ITSEC-005).

### Step 6: Confirm Financial Clearance
The Finance department confirms that the departing employee has no outstanding financial obligations, including:
- Unsettled travel advances.
- Outstanding loans or salary advances.
- Unreimbursed expenses (refer to FIN-003).

Any deductions for unreturned or damaged assets are processed as part of the final settlement.

### Step 7: Complete HR Clearance
The HR department confirms that all administrative requirements are met, including:
- Return of the employee ID badge.
- Completion of the exit interview.
- Return of any HR-issued documents or materials.

### Step 8: Final Clearance and Settlement
Once all departments have confirmed clearance, the Finance department processes the final settlement, including salary, accrued bonuses, and leave encashment as per the Leave Policy (HR-002).

## 6. Post-Offboarding Verification

### 6.1 Access Verification
Within 24 hours after the employee's last working day, the IT and Security department verifies that all access has been successfully revoked by attempting to access the employee's accounts and confirming that access is denied.

### 6.2 Account Archival
The departing employee's email and files are archived for a period of 12 months in accordance with the Data Classification Policy (ITSEC-006) and any legal or contractual retention requirements. Archived data is accessible only to authorized personnel with a legitimate business need.

### 6.3 License Reclamation
Software licenses assigned to the departing employee are reclaimed and made available for reassignment, ensuring that the company does not pay for unused licenses.

## 7. Offboarding Checklist Summary

| # | Task | Responsible | Completed |
|---|---|---|---|
| 1 | Create offboarding ticket | HR | ☐ |
| 2 | Notify IT and Security | HR | ☐ |
| 3 | Schedule access revocation | ITSEC | ☐ |
| 4 | Collect physical assets | ITSEC | ☐ |
| 5 | Conduct security audit | ITSEC | ☐ |
| 6 | Confirm financial clearance | Finance | ☐ |
| 7 | Complete HR clearance | HR | ☐ |
| 8 | Final clearance and settlement | Finance | ☐ |
| 9 | Verify access revocation | ITSEC | ☐ |
| 10 | Archive accounts and reclaim licenses | ITSEC | ☐ |

## 8. Related Documents
- **ITSEC-001 — Information Security Policy**: Overarching security framework.
- **HR-007 — Employee Exit Procedure**: Overall exit process and responsibilities.
- **HR-002 — Leave Policy**: Leave encashment rules for final settlement.
- **FIN-003 — Expense Reimbursement Policy**: Outstanding expense obligations.
- **ITSEC-005 — Incident Response Plan**: Escalation of suspicious activity.

---

## 9. Revision History

| Version | Date | Change Description | Author | Approved By |
|---|---|---|---|---|
| v1 | 2026-01-15 | Initial Release of Employee Offboarding Checklist | Rohit Verma | Arvind Malhotra |

---
*End of Document*
