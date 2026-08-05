---
github_id: GH-PR-004
repository: cloud-migration
artifact_type: pull_request
classification: department_internal
allowed_roles: [manager, it, admin]
author: Rahul Sharma
reviewers: ['Sunita Rao', 'Rohit Verma', 'Ayesha Khan']
assignees: ['Rahul Sharma']
related_documents: ['ENG-002', 'ITSEC-001', 'ITSEC-006']
related_jira: ['JIRA-CLOUD-001']
related_slack: ['SLK-ORION-001']
related_emails: ['EMAIL-023']
related_meetings: ['MEET-MIG-001']
related_project: Cloud Migration
created_date: 2026-05-10
updated_date: 2026-05-15
source_type: github
tags: ['cloud', 'landing-zone', 'terraform', 'iac']
---

# [PR] Deploy secure cloud landing zone for Wave 1 migration

## Description
Applies the Infrastructure-as-Code landing zone template for Wave 1 of the cloud migration, with VPCs, subnets, IAM, and logging per ENG-002. Includes security baselines per ITSEC-001 and ITSEC-006.

Resolves JIRA-CLOUD-001.

## Files Changed
- terraform/landing_zone/main.tf
- terraform/landing_zone/network.tf
- terraform/landing_zone/iam.tf
- terraform/landing_zone/logging.tf

## Commits
- a2b3c4d Add landing zone VPC and networking
- e5f6a7b Add IAM roles and policies
- c8d9e0f Configure centralized logging

## Code Review Comments
- Rohit Verma: MFA enforcement on admin roles is confirmed per ITSEC-002. Good.
- Ayesha Khan: Monitoring integration with Orion confirmed.
- Sunita Rao: The landing zone matches the reference architecture in ENG-001. Approved.

## Requested Changes
Rohit Verma: Add encryption for the S3 buckets used for logging.

## Approvals
Sunita Rao, Rohit Verma, Ayesha Khan

## Merge Status
MERGED

---
*End of GH-PR-004*
