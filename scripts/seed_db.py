"""Seed the PostgreSQL database with synthetic enterprise records for NexaCore Solutions.

This script generates realistic employees, invoices, expense claims, and IT tickets
across multiple tenants to verify multi-tenant isolation.
"""

import logging
import random
from datetime import date, timedelta
from faker import Faker

from hybridrag.config import get_settings
from hybridrag.structured.db import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    settings = get_settings()
    db = DatabaseManager(settings)
    db.initialize_schema()

    fake = Faker()
    tenants = ["nexacore_main", "nexacore_global"]
    departments = ["HR", "Engineering", "Finance", "Operations", "IT and Security", "Administration"]
    roles = ["employee", "manager", "director", "vp"]

    for tenant in tenants:
        logger.info(f"Seeding data for tenant: {tenant}")

        # 1. Seed Employees
        employee_ids = []
        for i in range(20):
            emp_id = f"EMP-{tenant[:3].upper()}-{100+i:03d}"
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
                        "INSERT INTO employees (id, name, role, department, email, hire_date, manager_id, tenant_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                        (emp_id, name, role, dept, email, hire_date, manager_id, tenant)
                    )
                conn.commit()

        # 2. Seed Invoices
        for i in range(30):
            inv_id = f"INV-2026-{1000+i:04d}"
            amount = fake.pydecimal(left_digits=4, right_digits=2, positive=True, min_value=100)
            inv_date = fake.date_between(start_date="-1y", end_date="today")
            vendor = fake.company()
            status = random.choice(["Paid", "Pending", "Overdue"])

            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO invoices (invoice_id, amount, date, vendor, status, tenant_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (invoice_id) DO NOTHING",
                        (inv_id, amount, inv_date, vendor, status, tenant)
                    )
                conn.commit()

        # 3. Seed Expense Claims
        for i in range(40):
            claim_id = f"EXP-{tenant[:3].upper()}-{100+i:03d}"
            emp_id = random.choice(employee_ids)
            amount = fake.pydecimal(left_digits=3, right_digits=2, positive=True, min_value=10)
            category = random.choice(["Travel", "Hardware", "Software", "Meals", "Education"])
            claim_date = fake.date_between(start_date="-1y", end_date="today")
            status = random.choice(["Approved", "Rejected", "Pending"])

            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO expense_claims (claim_id, employee_id, amount, category, date, status, tenant_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (claim_id) DO NOTHING",
                        (claim_id, emp_id, amount, category, claim_date, status, tenant)
                    )
                conn.commit()

        # 4. Seed IT Tickets
        for i in range(30):
            ticket_id = f"TIC-{tenant[:3].upper()}-{100+i:03d}"
            emp_id = random.choice(employee_ids)
            summary = fake.sentence(nb_words=6)
            priority = random.choice(["Low", "Medium", "High", "Critical"])
            status = random.choice(["Open", "In Progress", "Resolved", "Closed"])

            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO it_tickets (ticket_id, reporter_id, summary, priority, status, tenant_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (ticket_id) DO NOTHING",
                        (ticket_id, emp_id, summary, priority, status, tenant)
                    )
                conn.commit()

    logger.info("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_data()
