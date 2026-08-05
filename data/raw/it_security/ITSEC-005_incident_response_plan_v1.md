---
document_id: ITSEC-005
title: Incident Response Plan
document_type: policy
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
  - OPS
owner_department: ITSEC
document_version: v1
effective_date: 2026-01-15
status: active
created_date: 2025-12-20
last_reviewed_date: 2026-01-15
supersedes_document_version: null
related_documents:
  - ITSEC-001
  - ITSEC-002
  - ITSEC-003
  - ITSEC-006
  - HR-006
  - HR-007
tags:
  - security
  - incident-response
  - security-incident
  - escalation
  - policy
source_type: generated
---

# Incident Response Plan

## 1. Purpose
The purpose of this Incident Response Plan is to establish a structured, consistent, and effective approach for detecting, responding to, containing, eradicating, and recovering from **Security Incidents** at NexaCore Solutions Pvt. Ltd. A well-defined incident response capability is essential to minimize the impact of security incidents on the company's operations, reputation, client relationships, and regulatory compliance. This plan defines the roles, responsibilities, procedures, and communication protocols that guide the organization's response to security incidents of all severity levels.

This plan is subordinate to and must be read in conjunction with the Information Security Policy (ITSEC-001), which establishes the overarching security framework for the organization.

## 2. Scope
This plan applies to all Security Incidents that affect NexaCore's information assets, including:
- **Data Breaches:** Unauthorized access, disclosure, or exfiltration of data.
- **Malware Infections:** Ransomware, trojans, worms, or other malicious software.
- **Phishing and Social Engineering:** Attempts to deceive employees into disclosing credentials or sensitive information.
- **Account Compromise:** Unauthorized access to user accounts or privileged accounts.
- **Denial of Service (DoS):** Attacks that disrupt the availability of systems or services.
- **Physical Security Incidents:** Theft or loss of company devices or assets.
- **Insider Threats:** Malicious or negligent actions by employees or contractors.

## 3. Incident Response Team

### 3.1 Incident Commander
The CISO, **Rohit Verma**, serves as the Incident Commander and has overall authority for coordinating the incident response effort. The Incident Commander is responsible for:
- Declaring the severity level of an incident.
- Approving containment and eradication actions.
- Authorizing external communications.
- Escalating to executive leadership as required.

### 3.2 Core Response Team
The core response team includes:
- **IT and Security Analysts:** Responsible for technical investigation, containment, and eradication.
- **Engineering Representative:** Provides technical expertise for affected systems and applications.
- **Operations Representative:** Coordinates business continuity and operational impact assessment.
- **HR Representative:** Handles personnel-related aspects, including insider threat investigations and disciplinary coordination.
- **Legal/Compliance Representative:** Advises on legal obligations, regulatory reporting, and evidence preservation.

### 3.3 Executive Liaison
The CEO, **Arvind Malhotra**, is notified for incidents of high severity. The CFO, **Kabir Nair**, is notified for incidents with potential financial impact, including fraud or financial data compromise. The Finance department coordinates with the IT and Security team to assess the financial impact of incidents and to support any regulatory reporting obligations.

## 4. Incident Severity Classification

### 4.1 Severity Levels
Incidents are classified into three severity levels based on their potential impact:

| Severity | Definition | Examples | Response Time |
|---|---|---|---|
| **Low** | Minimal impact, contained, no sensitive data involved | Single phishing email reported, minor policy violation | Within 24 hours |
| **Medium** | Moderate impact, potential data exposure, limited scope | Malware on a single device, account compromise of a standard user | Within 4 hours |
| **High** | Significant impact, sensitive data involved, widespread scope | Ransomware, data breach involving client data, compromise of privileged accounts | Immediate |

### 4.2 Severity Escalation
The Incident Commander may escalate or de-escalate the severity level as the investigation progresses and more information becomes available.

## 5. Incident Response Phases

### Phase 1: Preparation
Preparation is an ongoing activity that ensures the organization is ready to respond effectively to incidents. Key preparation activities include:
- Maintaining and testing the incident response plan.
- Conducting regular security awareness training for all employees.
- Ensuring that monitoring and logging systems are operational.
- Maintaining contact lists for the incident response team and external partners.
- Conducting tabletop exercises to validate the plan.

### Phase 2: Detection and Reporting
Early detection and reporting are critical to minimizing the impact of an incident. All employees are required to report any suspected Security Incident to the IT and Security department immediately. Indicators of a potential incident include:
- Unusual system behavior or performance degradation.
- Unexpected pop-ups, ransomware messages, or system lockouts.
- Phishing emails or suspicious links.
- Unauthorized access attempts or failed login notifications.
- Missing or encrypted files.
- Unusual network traffic or data transfers.

**Reporting Channels:**
- Email the IT and Security team at the designated security mailbox.
- Submit an IT ticket through the service management system.
- Contact the IT and Security department directly by phone for urgent incidents.

### Phase 3: Triage and Assessment
Upon receiving a report, the IT and Security team assesses the incident to determine:
- Whether it is a genuine Security Incident or a false positive.
- The severity level based on the classification in Section 4.
- The affected systems, data, and users.
- The potential impact on business operations and clients.

The Incident Commander is notified for Medium and High severity incidents.

### Phase 4: Containment
Containment actions are taken to limit the spread and impact of the incident. Containment strategies may include:
- **Isolation:** Disconnecting affected systems from the network.
- **Account Suspension:** Disabling compromised user accounts.
- **Credential Reset:** Forcing password changes and MFA resets for affected users.
- **Network Segmentation:** Blocking malicious IP addresses or domains at the firewall.
- **Backup Preservation:** Ensuring that backups are protected from the incident (e.g., disconnecting backup systems from the network).

Containment actions must be documented, and evidence must be preserved for investigation and potential legal proceedings.

### Phase 5: Eradication
Eradication involves removing the root cause of the incident from affected systems. Activities include:
- Removing malware or malicious files.
- Patching vulnerabilities that were exploited.
- Rebuilding compromised systems from clean images.
- Revoking compromised credentials and tokens.
- Verifying that the threat has been fully eliminated.

### Phase 6: Recovery
Recovery involves restoring affected systems and data to normal operation. Activities include:
- Restoring data from verified backups.
- Reconnecting systems to the network after verification.
- Monitoring systems for signs of re-infection or continued compromise.
- Validating that business operations have resumed normally.

### Phase 7: Lessons Learned
After the incident is resolved, the incident response team conducts a post-incident review to:
- Document the timeline, root cause, and response actions.
- Identify gaps in controls, processes, or training.
- Recommend improvements to prevent recurrence.
- Update the incident response plan and related policies as needed.

The findings are documented in an incident report and shared with relevant stakeholders, including the Security Committee.

## 6. Communication and Notification

### 6.1 Internal Communication
Internal communication during an incident must be coordinated by the Incident Commander to ensure consistency and prevent misinformation. Employees are instructed not to discuss incident details externally or on social media.

### 6.2 External Communication
External communication, including notifications to clients, regulators, and law enforcement, is authorized only by the Incident Commander in coordination with the CEO and Legal. Unauthorized external communication about an incident is a violation of this plan and may result in disciplinary action.

### 6.3 Regulatory Notification
NexaCore will comply with all applicable legal and regulatory notification requirements, including data breach notification laws in the jurisdictions where it operates (India, UAE, Singapore).

## 7. Evidence Preservation and Forensics
For incidents involving potential legal action or regulatory investigation, the IT and Security team will:
- Preserve all relevant logs, system images, and communications.
- Maintain a chain of custody for all evidence.
- Engage external forensic experts where required.
- Coordinate with law enforcement as directed by the CEO and Legal.

## 8. Employee Responsibilities
All employees have a responsibility to:
- Report suspected Security Incidents immediately through the designated channels.
- Not attempt to investigate or contain an incident independently.
- Preserve any evidence (e.g., phishing emails) without deleting or modifying it.
- Cooperate fully with the incident response team during an investigation.

## 9. Related Documents
- **ITSEC-001 — Information Security Policy**: Overarching security framework.
- **ITSEC-002 — Password Policy**: Credential compromise response.
- **ITSEC-003 — Acceptable Use Policy**: Policy violations that may constitute incidents.
- **ITSEC-006 — Data Classification Policy**: Data sensitivity and breach impact assessment.
- **HR-006 — Code of Conduct**: Disciplinary framework for policy violations.
- **HR-007 — Employee Exit Procedure**: Offboarding of employees involved in incidents.

---

## 10. Revision History

| Version | Date | Change Description | Author | Approved By |
|---|---|---|---|---|
| v1 | 2026-01-15 | Initial Release of Incident Response Plan | Rohit Verma | Arvind Malhotra |

---
*End of Document*
