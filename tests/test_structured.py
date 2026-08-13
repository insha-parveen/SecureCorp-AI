"""Tests for the structured data path and query routing.

Verifies tenant isolation, RBAC, and routing accuracy.
"""

import pytest

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.routing.router import QueryRouter, Route
from hybridrag.structured.db import DatabaseManager
from hybridrag.structured.query_path import StructuredQueryPath


@pytest.fixture
def db_setup():
    settings = get_settings()
    db = DatabaseManager(settings)
    if not db.ping():
        pytest.skip("PostgreSQL unavailable; skipping structured-data test")
    db.initialize_schema()

    # Seed minimal data for testing
    with db._get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO employees "
                "(id, name, role, department, tenant_id) "
                "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                ("EMP-MAIN-001", "Alice", "hr", "HR", "nexacore_main"),
            )
            cur.execute(
                "INSERT INTO employees "
                "(id, name, role, department, tenant_id) "
                "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                ("EMP-GLOB-001", "Bob", "employee", "Sales", "nexacore_global"),
            )
            cur.execute(
                "INSERT INTO invoices "
                "(invoice_id, amount, date, vendor, status, tenant_id) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (invoice_id) DO NOTHING",
                ("INV-MAIN-001", 1500.00, "2026-01-01", "Vendor A", "Paid", "nexacore_main"),
            )
            cur.execute(
                "INSERT INTO invoices "
                "(invoice_id, amount, date, vendor, status, tenant_id) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (invoice_id) DO NOTHING",
                ("INV-GLOB-001", 2000.00, "2026-01-01", "Vendor B", "Paid", "nexacore_global"),
            )
        conn.commit()
    return db


def test_tenant_isolation(db_setup):
    path = StructuredQueryPath(db_setup)

    # User from nexacore_main
    user_main = UserContext(user_id="u1", roles=("admin",), tenant_id="nexacore_main")

    # Query for an invoice that belongs to nexacore_global
    result = path.query("What is the total of invoice INV-GLOB-001?", user_main)

    # Should return not found or error, NOT the data from other tenant
    assert "not found" in result["error"].lower() or result.get("data") == []


def test_rbac_denial(db_setup):
    path = StructuredQueryPath(db_setup)

    # User with no HR/Admin roles
    user_low = UserContext(user_id="u2", roles=("employee",), tenant_id="nexacore_main")

    # Attempt to query employees - needs to trigger the employee branch first
    result = path.query("Who is the employee in the HR department?", user_low)

    assert "Access denied" in result["error"]


def test_functional_lookup(db_setup):
    path = StructuredQueryPath(db_setup)
    user_admin = UserContext(user_id="u1", roles=("admin",), tenant_id="nexacore_main")

    result = path.query("What is the total of invoice INV-MAIN-001?", user_admin)

    assert "data" in result
    assert result["data"][0]["amount"] == 1500.00


def test_routing_logic():
    # Use a fake provider for routing tests
    class FakeProvider:
        def __init__(self, response):
            self.response = response

        def generate(self, prompt, system_prompt=None):
            return type("obj", (object,), {"text": self.response})()

    # Test SQL Route
    router = QueryRouter(FakeProvider("STRUCTURED_SQL"))
    assert router.route("How many invoices are there?") == Route.STRUCTURED_SQL

    # Test RAG Route
    router = QueryRouter(FakeProvider("DOCUMENT_RAG"))
    assert router.route("What is the travel policy?") == Route.DOCUMENT_RAG

    # Test Refuse Route
    router = QueryRouter(FakeProvider("REFUSE"))
    assert router.route("How do I make a sandwich?") == Route.REFUSE
