"""Seed the PostgreSQL database with synthetic enterprise records for NexaCore Solutions.

This script generates realistic employees, invoices, expense claims, and IT tickets
across multiple tenants to verify multi-tenant isolation.
"""

import logging
import random
import sys
from urllib.parse import urlsplit

from faker import Faker

from hybridrag.config import get_settings
from hybridrag.structured.db import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hosts that mean "no real database was configured" — the app's local-dev
# default (config.py) points here. On Railway, a wired DATABASE_URL resolves
# to an internal service host, never one of these.
_LOCAL_DB_HOSTS = {"localhost", "127.0.0.1", "::1", ""}


def _database_is_configured(database_url: str) -> bool:
    """True when database_url points somewhere other than a local default.

    Used by the deploy seed step to distinguish "no Postgres wired yet"
    (skip and let the deploy proceed) from "a real DB that is unreachable"
    (a genuine misconfiguration that should fail loudly).
    """
    try:
        host = urlsplit(database_url).hostname or ""
    except ValueError:
        # An unparseable URL is a real, configured-but-broken value — do not
        # treat it as "unconfigured".
        return True
    return host.lower() not in _LOCAL_DB_HOSTS


def seed_data() -> None:
    settings = get_settings()
    db = DatabaseManager(settings)
    db.initialize_schema()

    fake = Faker()
    tenants = ["nexacore_main", "nexacore_global"]
    departments = [
        "HR",
        "Engineering",
        "Finance",
        "Operations",
        "IT and Security",
        "Administration",
    ]
    roles = ["employee", "manager", "director", "vp"]

    for t_idx, tenant in enumerate(tenants):
        # The primary tenant (index 0, nexacore_main — where the demo users
        # live) gets the canonical IDs documented in CLAUDE.md §10:
        # EMP-0104, INV-2026-0108, INC-1042. Additional tenants are offset by
        # 500 per index so primary keys never collide across tenants (the id
        # columns are globally-unique PKs) and cross-tenant isolation stays
        # genuinely testable. Max per-table count (40) << 500, so no overlap.
        offset = 500 * t_idx
        emp_base = 104 + offset
        inv_base = 108 + offset
        exp_base = 301 + offset
        inc_base = 1042 + offset
        logger.info(f"Seeding data for tenant: {tenant}")

        # 1. Seed Employees
        employee_ids = []
        for i in range(20):
            emp_id = f"EMP-{emp_base + i:04d}"
            employee_ids.append(emp_id)

            name = fake.name()
            role = random.choice(roles)
            dept = random.choice(departments)
            email = f"{name.lower().replace(' ', '.')}@nexacore.com"
            hire_date = fake.date_between(start_date="-5y", end_date="today")

            # Random manager from previous employees
            manager_id = random.choice(employee_ids[:-1]) if len(employee_ids) > 1 else None

            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO employees "
                        "(id, name, role, department, email, hire_date, manager_id, tenant_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (id) DO NOTHING",
                        (emp_id, name, role, dept, email, hire_date, manager_id, tenant),
                    )
                conn.commit()

        # 2. Seed Invoices
        for i in range(30):
            inv_id = f"INV-2026-{inv_base + i:04d}"
            amount = fake.pydecimal(left_digits=4, right_digits=2, positive=True, min_value=100)
            inv_date = fake.date_between(start_date="-1y", end_date="today")
            vendor = fake.company()
            status = random.choice(["Paid", "Pending", "Overdue"])

            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO invoices "
                        "(invoice_id, amount, date, vendor, status, tenant_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (invoice_id) DO NOTHING",
                        (inv_id, amount, inv_date, vendor, status, tenant),
                    )
                conn.commit()

        # 3. Seed Expense Claims
        for i in range(40):
            claim_id = f"EXP-{exp_base + i:04d}"
            emp_id = random.choice(employee_ids)
            amount = fake.pydecimal(left_digits=3, right_digits=2, positive=True, min_value=10)
            category = random.choice(["Travel", "Hardware", "Software", "Meals", "Education"])
            claim_date = fake.date_between(start_date="-1y", end_date="today")
            status = random.choice(["Approved", "Rejected", "Pending"])

            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO expense_claims "
                        "(claim_id, employee_id, amount, category, date, status, tenant_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (claim_id) DO NOTHING",
                        (claim_id, emp_id, amount, category, claim_date, status, tenant),
                    )
                conn.commit()

        # 4. Seed IT Tickets
        # Canonical incident IDs (CLAUDE.md §10: INC-1042). The router's ticket
        # regex matches inc/tkt/ticket prefixes, so INC- is the correct prefix.
        for i in range(30):
            ticket_id = f"INC-{inc_base + i:04d}"
            emp_id = random.choice(employee_ids)
            summary = fake.sentence(nb_words=6)
            priority = random.choice(["Low", "Medium", "High", "Critical"])
            status = random.choice(["Open", "In Progress", "Resolved", "Closed"])

            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO it_tickets "
                        "(ticket_id, reporter_id, summary, priority, status, tenant_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (ticket_id) DO NOTHING",
                        (ticket_id, emp_id, summary, priority, status, tenant),
                    )
                conn.commit()

    logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    # Entry point for the Railway preDeployCommand (and local `python
    # scripts/seed_db.py`). The seed is idempotent, so re-running on every
    # deploy is safe.
    #
    # Deploy-ordering safety net: if no real database is wired yet (the URL is
    # still the local default), skip the seed and exit 0 so the deploy proceeds
    # in document-RAG-only mode instead of hard-failing. Once Postgres is
    # provisioned and DATABASE_URL is set, this branch is not taken.
    if not _database_is_configured(get_settings().database_url):
        logger.warning(
            "Postgres not configured (DATABASE_URL still points at a local "
            "default); skipping seed. Structured-SQL features are disabled "
            "until a real DATABASE_URL / HYBRIDRAG_DATABASE_URL is set."
        )
        sys.exit(0)

    # A real DB is configured: seed it. If it is unreachable or the seed
    # fails, exit non-zero so Railway aborts the deploy rather than starting
    # the API against an unseeded / misconfigured database.
    try:
        seed_data()
    except Exception:
        logger.exception("Database seeding failed; aborting deploy.")
        sys.exit(1)
