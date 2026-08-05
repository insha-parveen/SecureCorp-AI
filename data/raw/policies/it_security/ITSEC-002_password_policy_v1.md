---
document_id: ITSEC-002
title: Password Policy
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
  - ITSEC-003
  - ITSEC-005
  - ITSEC-008
  - HR-006
tags:
  - security
  - password
  - authentication
  - mfa
  - policy
source_type: generated
---

# Password Policy

## 1. Purpose
The purpose of this policy is to establish the minimum standards for the creation, use, storage, and management of passwords and authentication credentials across NexaCore Solutions Pvt. Ltd. Passwords are the first line of defense against unauthorized access to corporate systems, client environments, and sensitive data. Weak or compromised credentials are among the most common causes of **Security Incidents**, including account takeover, data exfiltration, and ransomware attacks. This policy ensures that all employees, contractors, and third-party users adopt strong authentication practices that protect both NexaCore and its clients.

This policy is subordinate to and must be read in conjunction with the Information Security Policy (ITSEC-001), which establishes the overarching security framework for the organization.

## 2. Scope
This policy applies to all users who access NexaCore systems, networks, applications, or data, including:
- All full-time, part-time, and contractual employees.
- Interns and trainees.
- Consultants and third-party contractors.
- Any external party granted temporary access to NexaCore resources.

The policy covers all authentication mechanisms, including passwords, passphrases, PINs, multi-factor authentication (MFA) tokens, and API keys used to access corporate systems.

## 3. Password Creation Standards

### 3.1 Minimum Complexity Requirements
All passwords used to access NexaCore systems must meet the following minimum requirements:
- **Length:** A minimum of 12 characters.
- **Character Types:** Must include at least three of the following four character classes: uppercase letters (A–Z), lowercase letters (a–z), numbers (0–9), and special characters (!@#$%^&*).
- **No Personal Information:** Passwords must not contain the user's name, employee ID, date of birth, or any other easily guessable personal information.
- **No Dictionary Words:** Passwords must not contain common dictionary words, sequential characters (e.g., "123456", "abcdef"), or repeated characters (e.g., "aaaaaa").

### 3.2 Passphrases
NexaCore encourages the use of passphrases—sequences of random words or a memorable sentence—as they are both more secure and easier to remember than complex random strings. For example, a passphrase such as "BlueRiver!Mountain42" is acceptable, provided it does not contain personal information and is not reused across accounts.

### 3.3 Prohibited Practices
The following practices are strictly prohibited:
- **Password Sharing:** Sharing passwords with colleagues, even temporarily, is prohibited. Each user must have unique credentials.
- **Password Reuse:** Reusing a password across multiple corporate systems, or between corporate and personal accounts, is prohibited.
- **Default Passwords:** Using default or vendor-supplied passwords without changing them is prohibited.
- **Written Passwords:** Writing passwords on sticky notes, notebooks, or any physical medium that could be accessed by others is prohibited.

## 4. Multi-Factor Authentication (MFA)

### 4.1 Mandatory MFA
Multi-factor authentication is mandatory for all users accessing NexaCore systems, including:
- Corporate email and collaboration tools.
- VPN and remote access (refer to the VPN & Remote Access Policy, ITSEC-008).
- Cloud consoles (AWS, Azure, GCP).
- Any system containing data classified as `restricted` or `confidential` under the Data Classification Policy (ITSEC-006).

### 4.2 MFA Methods
Approved MFA methods include:
- Authenticator applications (e.g., Microsoft Authenticator, Google Authenticator).
- Hardware security keys (e.g., YubiKey).
- Biometric verification where supported by the platform.

SMS-based one-time passcodes (OTP) are permitted only as a fallback method and are not considered a primary MFA mechanism due to known vulnerabilities such as SIM-swapping.

### 4.3 MFA Recovery
Users who lose their MFA device must contact the IT and Security department immediately to initiate a secure recovery process. The recovery process requires identity verification and may involve temporary access restrictions until a new MFA device is provisioned.

## 5. Password Storage and Management

### 5.1 Corporate Systems
NexaCore systems store passwords using strong, salted hashing algorithms. Plain-text passwords are never stored. The IT and Security department is responsible for ensuring that all authentication systems comply with industry best practices for password storage.

### 5.2 Password Managers
NexaCore provides a company-approved password manager to all employees. Employees are strongly encouraged to use the password manager to generate and store unique, complex passwords for all corporate accounts. The master password for the password manager must be exceptionally strong and must never be shared.

### 5.3 Personal Accounts
Employees are encouraged to apply the same password hygiene standards to their personal accounts, particularly those that use the same email address as their corporate account. A compromise of a personal account can be leveraged to attack corporate systems through password reuse or phishing.

## 6. Password Expiration and Rotation

### 6.1 Standard Rotation
NexaCore requires passwords to be rotated every 90 days for systems that do not support MFA. For systems protected by MFA, password rotation is required every 180 days, as the additional authentication factor reduces the risk of credential compromise.

### 6.2 Forced Rotation
Passwords must be changed immediately, without waiting for the scheduled rotation date, in the following circumstances:
- **Suspected Compromise:** If a user suspects their password has been compromised or observed by another person.
- **Phishing Incident:** If a user has entered their credentials into a phishing website, even if they did not submit the form.
- **Shared Device:** If a user has logged into a corporate system on a device that is not fully trusted.
- **Notification by IT:** If the IT and Security department notifies a user of a potential credential exposure.

### 6.3 History Requirements
When rotating a password, users must not reuse any of their previous five passwords. This prevents the cycling between a small set of known passwords.

## 7. Account Lockout and Failed Login Attempts

### 7.1 Lockout Policy
To mitigate brute-force attacks, NexaCore systems enforce an account lockout policy:
- **Threshold:** After five consecutive failed login attempts, the account is locked for 15 minutes.
- **Escalation:** After ten consecutive failed attempts, the account is locked until the user contacts the IT and Security department to verify their identity and unlock the account.

### 7.2 Notification
Users will receive an email notification when their account is locked due to failed login attempts. If the user did not initiate the failed attempts, they must report the incident to the IT and Security department immediately, as it may indicate an attempted unauthorized access.

## 8. Service Accounts and Privileged Access

### 8.1 Service Accounts
Service accounts used for automated processes must:
- Have passwords that are at least 20 characters in length.
- Be stored securely in the company's secrets management solution, never in plain-text configuration files or source code.
- Be rotated at least every 90 days.
- Be reviewed quarterly by the IT and Security department to ensure they are still required.

### 8.2 Privileged Accounts
Accounts with administrative or elevated privileges are subject to additional controls:
- **Separate Credentials:** Privileged accounts must use credentials that are distinct from standard user accounts.
- **MFA Mandatory:** MFA is mandatory for all privileged accounts.
- **Session Monitoring:** Privileged sessions may be monitored and logged for audit purposes.
- **Approval:** Creation of new privileged accounts requires approval from the CISO, **Rohit Verma**, or a designated deputy.
- **Financial Systems:** Accounts with access to financial systems and records (managed jointly with the Finance department under the CFO, **Kabir Nair**) are classified as privileged and are subject to the strictest password and MFA controls.

## 9. Employee Responsibilities
Every user is responsible for:
- Creating and maintaining strong passwords in accordance with this policy.
- Enabling MFA on all supported accounts.
- Reporting any suspected credential compromise to the IT and Security department immediately.
- Never disclosing passwords or MFA codes to anyone, including IT support staff. IT staff will never ask for a user's password.

## 10. Enforcement and Consequences
Failure to comply with this policy may result in disciplinary action, up to and including termination of employment, in accordance with the Code of Conduct (HR-006). Security incidents caused by negligent password practices will be investigated under the Incident Response Plan (ITSEC-005), and the findings may inform disciplinary decisions.

## 11. Related Documents
- **ITSEC-001 — Information Security Policy**: Overarching security framework.
- **ITSEC-003 — Acceptable Use Policy**: Rules for using company systems.
- **ITSEC-005 — Incident Response Plan**: Procedures for reporting credential compromise.
- **ITSEC-008 — VPN & Remote Access Policy**: MFA requirements for remote access.
- **HR-006 — Code of Conduct**: Disciplinary framework for policy violations.

---

## 12. Revision History

| Version | Date | Change Description | Author | Approved By |
|---|---|---|---|---|
| v1 | 2026-01-15 | Initial Release of Password Policy | Rohit Verma | Arvind Malhotra |

---
*End of Document*
