# Slack Channel: #eng-backend

## Thread 1: Authentication Service Failure

```yaml
thread_id: SLK-ENG-BE-001
channel: eng-backend
participants: [Sunita Rao, Rahul Sharma, Neha Kapoor, Rohit Verma]
related_project: Project Orion
classification: department_internal
allowed_roles: [manager, it, admin]
source_type: slack
created_date: 2026-03-14
```

---

**2026-03-14 09:22 — Sunita Rao**

Morning team. The Project Orion authentication service is failing after yesterday's deployment. Anyone seeing errors on their side?

---

**2026-03-14 09:25 — Rahul Sharma**

Looks related to refresh token validation. I'm seeing 401s on the token refresh endpoint since the 09:00 deploy.

---

**2026-03-14 09:28 — Neha Kapoor**

I can reproduce. The JWT expiry check is failing because the clock skew tolerance was removed in the last change. Refer to the API Design Guidelines ENG-003 for the expected behavior.

---

**2026-03-14 09:31 — Rohit Verma**

Please verify compliance with ITSEC-002 Password Policy before deploying a fix. Token handling must align with our authentication standards.

👍 4

---

**2026-03-14 09:35 — Sunita Rao**

Good catch. Let's roll back the clock skew change first, then fix properly. Rahul, can you prepare the rollback?

---

**2026-03-14 09:38 — Rahul Sharma**

On it. Rollback PR is ready, just need approval.

---

**2026-03-14 09:42 — Neha Kapoor**

I'll add a regression test for the clock skew scenario so this doesn't happen again.

---

**2026-03-14 09:45 — Sunita Rao**

Approved. Deploy the rollback and monitor. Let's do a post-incident review tomorrow per ITSEC-005.

---

**2026-03-14 09:50 — Rahul Sharma**

Rollback deployed. Auth service is back up. Monitoring now.

---

**2026-03-14 10:05 — Neha Kapoor**

Confirmed healthy. Error rate back to baseline.

---

**2026-03-14 10:10 — Rohit Verma**

Good. Please log the incident and reference the fix in the incident report. This aligns with the findings in SEC-001.

---

**2026-03-14 10:15 — Sunita Rao**

Thanks all. Let's schedule the post-incident review for 10:00 tomorrow.

---

## Thread 2: API Design Review

```yaml
thread_id: SLK-ENG-BE-002
channel: eng-backend
participants: [Sunita Rao, Rahul Sharma, Neha Kapoor, Meera Iyer]
related_project: Project Orion
classification: department_internal
allowed_roles: [manager, it, admin]
source_type: slack
created_date: 2026-03-18
```

---

**2026-03-18 14:00 — Sunita Rao**

Team, we need to review the new incident API design before it goes to the client. Please review the OpenAPI spec I shared.

📎 API_Guidelines.pdf

---

**2026-03-18 14:05 — Rahul Sharma**

The resource naming looks good, but I think we should use PATCH instead of PUT for partial updates. Refer to ENG-003.

---

**2026-03-18 14:10 — Neha Kapoor**

Agreed. Also, the error format should follow the standard envelope we defined. I see a few endpoints returning a different structure.

---

**2026-03-18 14:15 — Sunita Rao**

Good points. Let's align all endpoints to the standard error format. Rahul, can you update the spec?

---

**2026-03-18 14:20 — Rahul Sharma**

Sure. I'll also add rate limiting headers as per the guidelines.

---

**2026-03-18 14:25 — Meera Iyer**

Quick question - will this API be exposed to ACME Manufacturing? They're asking about incident data access.

---

**2026-03-18 14:30 — Sunita Rao**

Yes, this will be part of the client-facing API. We need to ensure it's documented in the customer portal per CLIENT-001.

---

**2026-03-18 14:35 — Neha Kapoor**

I'll make sure the OpenAPI spec is published to the developer portal once approved.

---

**2026-03-18 14:40 — Rahul Sharma**

Updated the spec. Please review the changes.

---

**2026-03-18 14:45 — Sunita Rao**

Looks good. Let's get security review from Rohit before finalizing.

---

**2026-03-18 14:50 — Meera Iyer**

Thanks. I'll let ACME know the timeline.

---

*End of Channel: #eng-backend*
