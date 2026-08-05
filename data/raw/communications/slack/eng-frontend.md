# Slack Channel: #eng-frontend

## Thread 1: Dashboard Rendering Bug

```yaml
thread_id: SLK-ENG-FE-001
channel: eng-frontend
participants: [Sunita Rao, Neha Kapoor, Rahul Sharma, Ayesha Khan]
related_project: Project Orion
classification: department_internal
allowed_roles: [manager, it, admin]
source_type: slack
created_date: 2026-03-20
```

---

**2026-03-20 11:30 — Neha Kapoor**

Is anyone else seeing the dashboard fail to load for the ACME Manufacturing tenant? The charts are blank after the last frontend deploy.

---

**2026-03-20 11:33 — Rahul Sharma**

I think it's a CORS issue with the new analytics endpoint. The browser is blocking the response.

---

**2026-03-20 11:36 — Neha Kapoor**

That matches. I see CORS errors in the console. Did we update the allowed origins?

---

**2026-03-20 11:40 — Sunita Rao**

We added the new tenant origin but I think the wildcard config was removed. Let me check the API gateway config. The API guidelines in ENG-003 cover this.

---

**2026-03-20 11:44 — Rahul Sharma**

That's it. The API gateway only allows origins listed explicitly. ACME's origin wasn't added.

---

**2026-03-20 11:48 — Sunita Rao**

Let's add it and redeploy. Ayesha, can you confirm ACME is actively using the dashboard right now?

---

**2026-03-20 11:50 — Ayesha Khan**

Yes, their team is doing UAT this week per CLIENT-001. It would be good to get this fixed quickly.

---

**2026-03-20 11:54 — Rahul Sharma**

Config updated and redeploying now.

---

**2026-03-20 11:58 — Neha Kapoor**

Dashboard is loading now for the ACME tenant. Confirmed.

---

**2026-03-20 12:02 — Sunita Rao**

Good. Let's add an automated check that validates allowed origins cover all active tenants. This is the kind of issue SEC-001 highlighted about configuration drift.

---

**2026-03-20 12:06 — Rahul Sharma**

I'll add it to the CI pipeline.

---

## Thread 2: New Component Library

```yaml
thread_id: SLK-ENG-FE-002
channel: eng-frontend
participants: [Sunita Rao, Neha Kapoor, Rahul Sharma]
related_project: Project Orion
classification: department_internal
allowed_roles: [manager, it, admin]
source_type: slack
created_date: 2026-03-25
```

---

**2026-03-25 15:00 — Neha Kapoor**

Heads up - I'm rolling out a new component library for the dashboards. It aligns with the design system we discussed in the architecture review.

---

**2026-03-25 15:05 — Rahul Sharma**

Will this affect the incident detail view? I'm working on that page.

---

**2026-03-25 15:08 — Neha Kapoor**

Yes, but I'll keep the API contract the same. Only visual changes. No need to change the endpoints.

---

**2026-03-25 15:12 — Sunita Rao**

Make sure to test on the ACME tenant as well. They have custom styling requirements per CLIENT-001.

---

**2026-03-25 15:16 — Neha Kapoor**

I'll add a feature flag so we can roll out gradually.

---

**2026-03-25 15:20 — Rahul Sharma**

Good idea. Let me know when it's ready for me to test the incident views.

---

**2026-03-25 15:24 — Neha Kapoor**

Will do. Expect a build later today.

---

*End of Channel: #eng-frontend*
