---
document_id: FIN-002
title: Invoice Approval SOP
document_type: sop
department: Finance
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
owner_department: Finance
document_version: v1
effective_date: 2025-01-01
status: active
created_date: 2024-11-15
last_reviewed_date: 2025-01-01
supersedes_document_version: null
source_type: generated
---

# Invoice Approval SOP

## 1. Introduction and Purpose
This Standard Operating Procedure (SOP) provides a detailed, step-by-step guide for the receipt, validation, approval, and payment of vendor invoices at NexaCore Solutions Pvt. Ltd. The purpose of this SOP is to ensure that the company maintains absolute financial control over its expenditures, prevents fraudulent payments, and ensures that vendors are paid accurately and on time.

Strict adherence to this SOP is mandatory for all Finance staff and any manager authorized to approve expenditures. This process is the operational implementation of the **Procurement Policy (FIN-001)**. Any deviation from these steps without written approval from the CFO is considered a breach of financial control.

## 2. Scope
This SOP applies to all external vendor invoices processed by NexaCore Solutions. It covers the full lifecycle of an invoice: from the moment it is received in the email inbox to the final execution of the payment and the archival of the record.

## 3. Phase 1: Invoice Receipt and Intake

### 3.1 Primary Submission Channel
To ensure a centralized and auditable trail, all vendors must be instructed to send invoices electronically to `accounts-payable@nexacore.com`. 

### 3.2 Handling Alternative Submissions
Invoices received through other channels (e.g., physical mail, direct email to a project manager, or Slack) must be handled as follows:
- **Employee Action:** The employee who received the invoice must forward it to the Accounts Payable (AP) team immediately.
- **Vendor Communication:** The AP team will contact the vendor to request that all future invoices be sent to the official AP email address to avoid payment delays.

### 3.3 Initial Document Validation
Upon receipt, the AP team performs a "Sanity Check" on the document. An invoice is rejected and returned to the vendor if any of the following are missing or incorrect:
- **Vendor Identification:** The vendor's legal name and unique Vendor ID (`VEN-NNN`).
- **Invoice Number:** A unique invoice identifier (`INV-YYYY-NNNN`).
- **Date of Issue:** The date the invoice was generated.
- **Itemization:** A clear breakdown of the goods or services provided, including quantities and unit prices.
- **Tax Information:** Correct GST/VAT calculations and registration numbers.
- **Total Amount:** The final amount due, clearly stated in the agreed-upon currency.

---

## 4. Phase 2: Vendor Verification and PO Matching

### 4.1 Vendor System Check
The AP team verifies that the vendor on the invoice is active and approved in the Finance portal. If the vendor is not registered, the invoice is placed on a "Pending Onboarding" hold, and the requester is notified to initiate the onboarding process as per **FIN-001**.

### 4.2 The Three-Way Match Execution
The core of the invoice approval process is the "Three-Way Match." This control ensures that NexaCore only pays for what was authorized and actually delivered.

**Step 1: Retrieve the Purchase Order (PO)**
The AP team searches the Finance portal for the PO (`PO-NNNN`) referenced on the invoice. They verify that the itemized list and the total amount on the invoice do not exceed the authorized amount on the PO. If the invoice exceeds the PO amount, it is flagged for a "PO Amendment."

**Step 2: Verify Delivery (The Receiving Report)**
The AP team checks for a "Receiving Report" or a "Delivery Note." This is a confirmation—either a digital sign-off in the portal or a physical document—from the employee who requested the item, stating that the goods were received in good condition or the services were rendered as specified. For software/SaaS, this is replaced by a "Service Acceptance" sign-off.

**Step 3: Invoice Comparison**
The AP team compares the PO, the Delivery Note, and the Invoice. 
- **Match Found:** If the quantity and price align across all three documents, the invoice is marked as "Matched" and proceeds to the Approval Routing phase.
- **Mismatch/Discrepancy:** If there is a variance (e.g., the invoice is for 10 units but the PO was for 8, or the price has increased), the invoice is flagged as "Disputed."

### 4.3 Managing Disputed Invoices and Variance
When a mismatch occurs, the following steps are taken:
1. **Internal Query:** The AP team contacts the requesting employee to verify if the variance was authorized (e.g., a lapped change in scope).
2. **Vendor Query:** The AP team contacts the vendor to request a correction or a credit note.
3. **Resolution:** The invoice remains on hold until a corrected invoice is received or the PO is officially amended to match the invoice.

---

## 5. Phase 3: Approval Routing and Thresholds

Once a "Three-Way Match" is successfully completed, the invoice is routed through the electronic approval chain. The level of approval required is determined by the total value of the invoice.

### 5.1 Tier 1: Departmental Approval
- **Value:** Up to ₹50,000.
- **Approver:** The **Department Manager** of the cost center associated with the purchase.
- **Review Criteria:** The manager confirms that the expenditure was necessary, that the service/product is satisfactory, and that the amount is within the monthly departmental budget.

### 5.2 Tier 2: Finance Management Approval
- **Value:** ₹50,001 to ₹500,000.
- **Approver:** **Siddharth Mehta (Finance Manager, EMP-0011)**.
- **Review Criteria:** Siddharth Mehta reviews the lapped budget for the department and ensures the Three-Way Match was performed correctly. He verifies that the spend is aligned with the quarterly financial forecast and that no "split purchasing" has occurred.

### 5.3 Tier 3: Executive Approval
- **Value:** Above ₹500,000.
- **Approver:** **Kabir Nair (CFO, EMP-0003)**.
- **Review Criteria:** The CFO performs a strategic review of the expenditure. For these high-value payments, the CFO typically requires a brief "Justification Memo" from the Department Head explaining the ROI, the criticality of the purchase, and why a competitive bid was chosen.

---

## 6. Phase 4: Handling Special Cases and Exceptions

### 6.1 Duplicate Invoice Detection
The Finance portal automatically flags any invoice with a duplicate `INV-YYYY-NNNN` identifier for the same vendor. 
- **Action:** The AP team must manually verify if the invoice is a legitimate duplicate or if the vendor has reused a number. If it is a duplicate, the invoice is cancelled and archived.

### 6.2 Credit Notes and Adjustments
When a vendor issues a credit note (to correct an overcharge or for returned goods), it is processed as a "Negative Invoice."
- **Application:** The credit note is linked to the original invoice in the portal.
- **Approval:** Credit notes must be approved by the Finance Manager to ensure the balance is correctly adjusted before the next payment cycle.

### 6.3 Pre-paid Expenses and Deposits
In cases where a vendor requires a deposit before work begins (e.g., 50% upfront for a custom software build):
1. A PO is issued for the full amount.
2. A "Deposit Invoice" is processed through the standard approval chain.
3. The remaining balance is paid only upon final delivery and a completed Three-Way Match.

---

## 7. Phase 5: Final Processing and Payment

### 7.1 Payment Scheduling
Once the final authorized approval is received, the invoice status changes to "Approved for Payment."
- **Payment Terms:** The Finance team schedules the payment according to the terms agreed upon in the PO (e.g., Net 30 days from invoice date).
- **Batch Processing:** Payments are typically processed in weekly batches every Thursday.

### 7.2 Execution and Notification
- **Payment Method:** All payments are made via electronic bank transfer (ACH/Wire).
- **Vendor Notification:** Upon execution, the Finance portal automatically sends a "Remittance Advice" email to the vendor, specifying the invoice numbers that have been paid.

---

## 8. Audit Trail and Records Management

### 8.1 The Digital Audit Trail
Every invoice processed must have a complete, immutable history in the Finance portal, including:
- The timestamp of receipt.
- The identity of the AP staff who performed the Three-Way Match.
- The timestamps and identities of every approver in the chain.
- The payment confirmation number and date.

### 8.2 Document Retention
All procurement-related documents (PRs, POs, Invoices, and Delivery Notes) must be archived digitally. These records are retained for 7 years to ensure compliance with Indian tax laws and corporate audit requirements.

## 9. Related Documents
- **FIN-001 — Procurement Policy**: The high-level rules and logic for buying goods/services.
- **HR-006 — Code of Conduct**: Ethical guidelines for managing vendor relations.
- **docs/company_bible.md**: For canonical IDs and personnel data.

---

## 10. Revision History

| Version | Date | Change Description | Author | Approved By |
|---|---|---|---|---|
| v1 | 2025-01-01 | Initial Release of Invoice Approval SOP | Siddharth Mehta | Kabir Nair |

---
*End of Document*
