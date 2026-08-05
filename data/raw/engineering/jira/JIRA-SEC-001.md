---
issue_id: JIRA-SEC-001
project: Security
issue_type: Incident
priority: Critical
status: Closed
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rohit Verma
reporter: Ayesha Khan
department: ITSEC
related_documents: ['ITSEC-005', 'HR-006']
related_emails: ['EMAIL-024']
related_slack: ['SLK-SEC-002']
related_meetings: ['MEET-SEC-001']
created_date: 2026-03-17
updated_date: 2026-03-18
source_type: jira
tags: ['security', 'phishing', 'incident']
---

# Security incident - targeted phishing campaign

## Description
A targeted phishing campaign impersonating the cloud provider was detected. Several employees received the emails.

## Background
The phishing emails appeared legitimate but contained links to suspicious domains. The incident is being tracked under the Incident Response Plan (ITSEC-005).

## Steps to Reproduce
1. Employees receive phishing email.
2. Email links to suspicious domain.
3. Employee reports or clicks.

## Expected Behaviour
No employee compromise.

## Actual Behaviour
Phishing attempt detected; no compromise confirmed.

## Business Impact
Potential credential compromise if employees clicked links.

## Technical Notes
Alert employees, update detection rules, and monitor per ITSEC-005.

## Acceptance Criteria
1. Phishing alert sent.
2. Detection rules updated.
3. No compromise confirmed.

## Comments
- **Rohit Verma:** We've seen a targeted phishing email going to several employees.
- **Farah Hussain:** Let's send an internal alert so others know per HR-006.
- **Neha Kapoor:** No one I know clicked the link. Forwarding to security.

## Activity Log
- 2026-03-17 15:00: Created by Rohit Verma
- 2026-03-18 10:00: Resolved, Closed

## Attachments
['Incident_Report.pdf']

---
*End of Issue JIRA-SEC-001*
