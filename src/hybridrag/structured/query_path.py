"""Implementation of the authorized structured data query path.

This module translates user intent into safe, parameterized SQL queries,
enforcing multi-tenant isolation and role-based access control.
"""

import logging
from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.structured.db import DatabaseManager

logger = logging.getLogger(__name__)

# Table access map: Table Name -> Required Roles (any of these)
# If empty, table is accessible to all authenticated users of that tenant.
ACCESS_CONTROL_MAP = {
    "employees": {"hr", "admin"},
    "invoices": {"finance", "admin"},
    "expense_claims": {"finance", "admin"},
    "it_tickets": {"it", "admin"},
}


class StructuredQueryPath:
    """Handles NL-to-SQL translation via safe templates and enforces security."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def query(self, query_text: str, user_context: UserContext) -> dict[str, Any]:
        """Route a query to a safe SQL template and return results.

        This replaces an agentic Text-to-SQL system with a deterministic
        template-based approach for reliability and security.
        """
        query_text = query_text.lower()

        # 1. Identify intent and map to template
        # In a production system, this could be a small classifier or regex.
        # For the portfolio, we use clear keyword mapping to safe templates.

        if "invoice" in query_text:
            return self._handle_invoice_query(query_text, user_context)
        elif "ticket" in query_text:
            return self._handle_ticket_query(query_text, user_context)
        elif "employee" in query_text:
            return self._handle_employee_query(query_text, user_context)
        elif "expense" in query_text or "claim" in query_text:
            return self._handle_expense_query(query_text, user_context)

        return {"error": "I couldn't find any structured records matching your request."}

    def _check_access(self, table: str, user_context: UserContext) -> bool:
        """Verify if the user's roles allow access to the specified table."""
        required_roles = ACCESS_CONTROL_MAP.get(table)
        if not required_roles:
            return True  # Open table
        return any(role in required_roles for role in user_context.roles)

    def _handle_invoice_query(self, text: str, user_context: UserContext) -> dict[str, Any]:
        if not self._check_access("invoices", user_context):
            return {"error": "Access denied to invoice records."}

        # Template 1: Invoice Lookup
        # Example: "What is the total of invoice INV-1001?"
        if "total" in text or "amount" in text:
            # Simple extraction of the ID (e.g., INV-XXXX)
            import re

            match = re.search(r"inv-[\w-]+", text)
            if match:
                inv_id = match.group(0).upper()
                sql = (
                    "SELECT amount, vendor, status FROM invoices "
                    "WHERE invoice_id = %s AND tenant_id = %s"
                )
                results = self._db.execute_read(sql, (inv_id, user_context.tenant_id))
                if results:
                    return {"table": "invoices", "data": results, "query": sql}
                return {"error": f"Invoice {inv_id} not found."}

        # Template 2: Invoice Aggregation
        if "total" in text and "all" in text:
            sql = "SELECT SUM(amount) as total_amount FROM invoices WHERE tenant_id = %s"
            results = self._db.execute_read(sql, (user_context.tenant_id,))
            return {"table": "invoices", "data": results, "query": sql}

        return {"error": "I can lookup specific invoice amounts or the total for all invoices."}

    def _handle_ticket_query(self, text: str, user_context: UserContext) -> dict[str, Any]:
        if not self._check_access("it_tickets", user_context):
            return {"error": "Access denied to IT ticket records."}

        # Template 1: Ticket Count
        if "how many" in text or "count" in text:
            # Optional filter by status
            status = None
            if "open" in text:
                status = "Open"
            elif "closed" in text:
                status = "Closed"

            params: tuple[Any, ...]
            if status:
                sql = (
                    "SELECT COUNT(*) as count FROM it_tickets WHERE status = %s AND tenant_id = %s"
                )
                params = (status, user_context.tenant_id)
            else:
                sql = "SELECT COUNT(*) as count FROM it_tickets WHERE tenant_id = %s"
                params = (user_context.tenant_id,)

            results = self._db.execute_read(sql, params)
            return {"table": "it_tickets", "data": results, "query": sql}

        return {
            "error": (
                "I can count IT tickets or filter them by status (e.g., 'How many open tickets?')."
            )
        }

    def _handle_employee_query(self, text: str, user_context: UserContext) -> dict[str, Any]:
        if not self._check_access("employees", user_context):
            return {"error": "Access denied to employee records."}

        # Template 1: Department list
        if "department" in text and ("who" in text or "list" in text):
            # Simple search for department names
            for dept in ["HR", "Engineering", "Finance", "Operations", "IT and Security"]:
                if dept.lower() in text.lower():
                    sql = (
                        "SELECT name, role FROM employees WHERE department = %s AND tenant_id = %s"
                    )
                    results = self._db.execute_read(sql, (dept, user_context.tenant_id))
                    return {"table": "employees", "data": results, "query": sql}

        return {
            "error": "I can list employees by department (e.g., 'Who is in the HR department?')."
        }

    def _handle_expense_query(self, text: str, user_context: UserContext) -> dict[str, Any]:
        if not self._check_access("expense_claims", user_context):
            return {"error": "Access denied to expense claims."}

        # Template 1: User's own expenses (Row-level security)
        if "my" in text or "own" in text:
            sql = (
                "SELECT amount, category, date, status FROM expense_claims "
                "WHERE employee_id = %s AND tenant_id = %s"
            )
            results = self._db.execute_read(sql, (user_context.user_id, user_context.tenant_id))
            return {"table": "expense_claims", "data": results, "query": sql}

        return {"error": "I can show you your own expense claims."}
