---
issue_id: JIRA-CLOUD-001
project: Cloud Migration
issue_type: Task
priority: High
status: Done
classification: department_internal
allowed_roles: [manager, it, admin]
assignee: Rahul Sharma
reporter: Sunita Rao
department: ENG
related_documents: ['ENG-002', 'ITSEC-001', 'ITSEC-002', 'ITSEC-006']
related_emails: ['EMAIL-023']
related_slack: ['SLK-ORION-001']
related_meetings: ['MEET-MIG-001']
created_date: 2026-03-02
updated_date: 2026-05-15
source_type: jira
tags: ['cloud-migration', 'landing-zone', 'task']
---

# Deploy secure cloud landing zone for Wave 1

## Description
Deploy the cloud landing zone with VPCs, subnets, IAM, and logging for Wave 1 of the cloud migration per the migration plan.

## Background
The landing zone is the foundation for migrating ingestion and core services to the cloud as part of ENG-002.

## Steps to Reproduce
1. Apply IaC landing zone template.
2. Verify network segmentation.
3. Confirm logging configuration.

## Expected Behaviour
Secure landing zone with proper IAM, VPC, and logging.

## Actual Behaviour
Landing zone not yet deployed.

## Business Impact
Blocks Wave 1 migration of Orion services.

## Technical Notes
Security baseline per ITSEC-001 and ITSEC-006 required.

## Acceptance Criteria
1. Landing zone deployed.
2. MFA enforcement per ITSEC-002.
3. Monitoring integrated with Orion.

## Comments
- **Sunita Rao:** Wave 1 scheduled to begin next week. Confirm landing zone readiness.
- **Rohit Verma:** Security baseline complete. All controls align with ITSEC-001 and ITSEC-006.
- **Rahul Sharma:** Landing zone deployed and verified.

## Activity Log
- 2026-03-02 10:00: Created by Sunita Rao
- 2026-05-15 14:00: Landing zone deployed, Done

## Attachments
['Deployment_Checklist.md']

---
*End of Issue JIRA-CLOUD-001*
