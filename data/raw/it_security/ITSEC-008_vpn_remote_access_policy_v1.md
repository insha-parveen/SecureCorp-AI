---
document_id: ITSEC-008
title: VPN & Remote Access Policy
document_type: policy
department: ITSEC
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
  - HR-003
tags:
  - security
  - vpn
  - remote-access
  - mfa
  - policy
source_type: generated
---

# VPN & Remote Access Policy

## 1. Purpose
The purpose of this policy is to define the requirements and procedures for secure remote access to NexaCore Solutions Pvt. Ltd.'s corporate network and resources. As a technology consulting and managed IT services organization with offices in Lucknow, Bengaluru, Dubai, and Singapore, NexaCore supports flexible working arrangements, including **Remote Work** as defined in the Remote Work Policy (HR-003). Remote access introduces additional security risks, including exposure to unsecured networks, device compromise, and unauthorized access. This policy establishes the controls required to ensure that all remote access is conducted securely and in a manner that protects NexaCore's data, systems, and client information.

This policy is subordinate to and must be read in conjunction with the Information Security Policy (ITSEC-001), which establishes the overarching security framework for the organization.

## 2. Scope
This policy applies to all employees, contractors, and third-party partners who require remote access to NexaCore's corporate network, systems, or data. This includes:
- Employees working remotely under the Remote Work Policy (HR-003).
- Employees traveling on business.
- Contractors and consultants engaged on client projects.
- Any other individual granted remote access privileges.

## 3. Remote Access Methods

### 3.1 VPN (Virtual Private Network)
The company-approved VPN is the primary and mandatory method for remote access to NexaCore's internal network and resources. All remote access to corporate systems, cloud consoles, and client environments must be conducted through the VPN. Direct access to corporate resources over the public internet is strictly prohibited.

### 3.2 Cloud-Based Access
Access to cloud-based applications and services (e.g., email, collaboration tools, cloud consoles) may be provided through the cloud provider's native access controls, provided that:
- Multi-factor authentication (MFA) is enabled.
- Access is granted on a least-privilege basis.
- The service is approved by the IT and Security department.

## 4. VPN Access Requirements

### 4.1 Eligibility
VPN access is granted to employees whose roles require remote access to internal resources. Access is provisioned by the IT and Security department upon:
- Completion of onboarding and security awareness training.
- Approval by the employee's **Reporting Manager**.
- Confirmation that the employee has a company-issued device.

### 4.2 Multi-Factor Authentication (MFA)
MFA is mandatory for all VPN connections. Users must authenticate using at least two of the following factors:
- Something they know (password or PIN).
- Something they have (authenticator app, hardware token).
- Something they are (biometric verification).

Refer to the Password Policy (ITSEC-002) for detailed MFA requirements.

### 4.3 Approved Devices
VPN access is only permitted from company-issued devices that:
- Run a current, supported operating system.
- Have all security updates and patches installed.
- Have endpoint protection (antivirus/EDR) enabled and up to date.
- Are not rooted or jailbroken.

The use of personal devices for VPN access is prohibited unless explicitly authorized by the IT and Security department for a specific use case.

## 5. Secure Connection Requirements

### 5.1 Network Security
Employees connecting via VPN must ensure that their network connection is secure:
- **Home Networks:** Use a secure, password-protected home Wi-Fi network with WPA2 or WPA3 encryption.
- **Public Networks:** Do not use public, unsecured Wi-Fi (e.g., in cafes, airports, hotels) for VPN connections. If a public network must be used, a company-authorized personal hotspot or a secure VPN tunnel must be used.
- **Network Privacy:** Never connect to corporate resources over an unsecured or untrusted network.

### 5.2 Session Security
- **Screen Lock:** Devices must be configured to lock automatically after a period of inactivity.
- **Physical Privacy:** Ensure that screens are not visible to unauthorized individuals when working in public or shared spaces.
- **Session Termination:** VPN sessions must be terminated when not in use, particularly when the device is left unattended.

## 6. Remote Work and Travel

### 6.1 Remote Work
Employees working remotely must comply with the Remote Work Policy (HR-003) and must use the VPN for all access to internal resources. The standard remote work arrangement is a maximum of 2 days per week, as defined in HR-003.

### 6.2 Business Travel
Employees traveling on business must:
- Use the VPN for all access to corporate resources.
- Not access corporate systems from public or shared computers.
- Report any loss or theft of a company device to the IT and Security department immediately.
- Be aware of heightened security risks when traveling, including surveillance and device seizure in certain jurisdictions.

## 7. Access Control and Monitoring

### 7.1 Least Privilege
VPN access is granted on a least-privilege basis. Users are granted access only to the systems and resources required for their job functions. Requests for additional access must be justified and approved.

### 7.2 Monitoring
NexaCore monitors VPN connections for security purposes, including:
- Login attempts and authentication failures.
- Connection duration and data transfer volumes.
- Access to sensitive systems and data.

Monitoring is conducted in accordance with the Acceptable Use Policy (ITSEC-003) and the Information Security Policy (ITSEC-001).

### 7.3 Access Review
The IT and Security department conducts quarterly reviews of VPN access to:
- Verify that all active accounts are still required.
- Remove access for users who no longer require it.
- Identify and remediate any anomalous access patterns.

Access to financial systems and invoice processing platforms via VPN is coordinated with the Finance department, and any access to these systems is logged and reviewed in accordance with the Procurement Policy (FIN-001).

## 8. Offboarding and Access Revocation
VPN access is revoked as part of the employee offboarding process, in accordance with the Employee Offboarding Checklist (ITSEC-004) and the Employee Exit Procedure (HR-007). Access is revoked at the close of business on the employee's last working day for standard exits, or immediately for terminations for cause.

## 9. Incident Reporting
Any suspected security incident involving VPN access, including:
- Unauthorized access attempts.
- Compromised credentials.
- Lost or stolen devices.
- Unusual VPN activity.

must be reported to the IT and Security department immediately, in accordance with the Incident Response Plan (ITSEC-005).

## 10. Enforcement
Failure to comply with this policy may result in:
- Revocation of VPN and remote access privileges.
- Disciplinary action, up to and including termination of employment, in accordance with the Code of Conduct (HR-006).
- Investigation under the Incident Response Plan (ITSEC-005) for security incidents.

## 11. Related Documents
- **ITSEC-001 — Information Security Policy**: Overarching security framework.
- **ITSEC-002 — Password Policy**: MFA and authentication requirements.
- **ITSEC-003 — Acceptable Use Policy**: Device and network usage requirements.
- **ITSEC-006 — Data Classification Policy**: Data handling requirements for remote access.
- **HR-003 — Remote Work Policy**: Framework for remote work arrangements.
- **ITSEC-004 — Employee Offboarding Checklist**: Access revocation on exit.
- **ITSEC-005 — Incident Response Plan**: Reporting and response to security incidents.

---

## 12. Revision History

| Version | Date | Change Description | Author | Approved By |
|---|---|---|---|---|
| v1 | 2026-01-15 | Initial Release of VPN & Remote Access Policy | Rohit Verma | Arvind Malhotra |

---
*End of Document*
