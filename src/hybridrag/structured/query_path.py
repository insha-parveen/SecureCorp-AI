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
        if "ticket" in query_text:
            return self._handle_ticket_query(query_text, user_context)
        # Employee intent: match employee noun, employee-ID pattern (EMP-NNN or
        # EMP-NEX-NNN), or the word "headcount" so the department-by-department
        # template is reachable without forcing the word "employee".
        import re as _re

        if (
            "employee" in query_text
            or "headcount" in query_text
            or "staff" in query_text
            or _re.search(r"\bemp(?:-\w+)?-\d+\b", query_text) is not None
        ):
            return self._handle_employee_query(query_text, user_context)
        if "expense" in query_text or "claim" in query_text:
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

        # Template 3: Invoices above a threshold
        # Example: "invoices over 500000" / "invoices above 100k"
        if "above" in text or "over" in text or "greater" in text:
            threshold = _extract_amount(text)
            if threshold is not None:
                sql = (
                    "SELECT invoice_id, amount, vendor, status FROM invoices "
                    "WHERE amount > %s AND tenant_id = %s "
                    "ORDER BY amount DESC LIMIT 25"
                )
                results = self._db.execute_read(sql, (threshold, user_context.tenant_id))
                return {"table": "invoices", "data": results, "query": sql}

        # Template 4: Invoices by vendor
        # Example: "invoices from Bluewave" / "open invoices from Acme"
        for vendor in _VENDOR_HINTS:
            if vendor in text:
                sql = (
                    "SELECT invoice_id, amount, vendor, status, date FROM invoices "
                    "WHERE vendor ILIKE %s AND tenant_id = %s "
                    "ORDER BY date DESC LIMIT 25"
                )
                results = self._db.execute_read(sql, (f"%{vendor}%", user_context.tenant_id))
                return {"table": "invoices", "data": results, "query": sql}

        return {
            "error": (
                "I can look up a specific invoice (e.g., 'total of INV-2026-0108'), "
                "sum all invoices, list invoices above a threshold "
                "(e.g., 'invoices over 500000'), or list invoices by vendor "
                "(e.g., 'invoices from Bluewave')."
            )
        }

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

        # Template 2: Tickets by priority
        # Example: "show high priority tickets"
        for priority in ("high", "medium", "low"):
            if priority in text and "priority" in text:
                sql = (
                    "SELECT ticket_id, summary, status, priority FROM it_tickets "
                    "WHERE priority = %s AND tenant_id = %s "
                    "ORDER BY created_at DESC LIMIT 25"
                )
                results = self._db.execute_read(
                    sql, (priority.capitalize(), user_context.tenant_id)
                )
                return {"table": "it_tickets", "data": results, "query": sql}

        # Template 3: Recent tickets (default fallback if "ticket" was matched)
        if "recent" in text or "latest" in text or "last" in text:
            sql = (
                "SELECT ticket_id, summary, status, priority, created_at "
                "FROM it_tickets WHERE tenant_id = %s "
                "ORDER BY created_at DESC LIMIT 10"
            )
            results = self._db.execute_read(sql, (user_context.tenant_id,))
            return {"table": "it_tickets", "data": results, "query": sql}

        return {
            "error": (
                "I can count IT tickets (optionally by status), list tickets by priority "
                "(e.g., 'show high priority tickets'), or show recent tickets "
                "(e.g., 'latest tickets')."
            )
        }

    def _handle_employee_query(self, text: str, user_context: UserContext) -> dict[str, Any]:
        if not self._check_access("employees", user_context):
            return {"error": "Access denied to employee records."}

        # Template 1: Employee Count
        # Note: "headcount" must NOT match here — it triggers the per-department
        # template below. Check the more specific "headcount" phrase first.
        if "headcount" in text:
            pass  # fall through to Template 3
        elif "how many" in text or "count" in text:
            sql = "SELECT COUNT(*) as count FROM employees WHERE tenant_id = %s"
            results = self._db.execute_read(sql, (user_context.tenant_id,))
            return {"table": "employees", "data": results, "query": sql}

        # Template 2: Department list
        if "department" in text and ("who" in text or "list" in text):
            # Simple search for department names
            for dept in ["HR", "Engineering", "Finance", "Operations", "IT and Security"]:
                if dept.lower() in text.lower():
                    sql = (
                        "SELECT name, role FROM employees WHERE department = %s AND tenant_id = %s"
                    )
                    results = self._db.execute_read(sql, (dept, user_context.tenant_id))
                    return {"table": "employees", "data": results, "query": sql}

        # Template 3: Department count breakdown
        # Example: "employees per department" / "headcount by department"
        if "per department" in text or "by department" in text or "headcount" in text:
            sql = (
                "SELECT department, COUNT(*) as count FROM employees "
                "WHERE tenant_id = %s GROUP BY department ORDER BY count DESC"
            )
            results = self._db.execute_read(sql, (user_context.tenant_id,))
            return {"table": "employees", "data": results, "query": sql}

        # Template 4: Employee lookup by id or name fragment
        # Example: "who is EMP-0003" / "who is EMP-NEX-100" / "find employee Rohit"
        if "who is" in text or "find employee" in text or "lookup employee" in text:
            import re

            # Match EMP, optional NEX prefix, then digits.
            # Examples that must match: emp-0003, emp-nex-100, emp-12345
            id_match = re.search(r"emp(?:-nex)?-\d+", text)
            if id_match:
                emp_id = id_match.group(0).upper()
                sql = (
                    "SELECT name, role, department, email FROM employees "
                    "WHERE id = %s AND tenant_id = %s"
                )
                results = self._db.execute_read(sql, (emp_id, user_context.tenant_id))
                if results:
                    return {"table": "employees", "data": results, "query": sql}
                return {"error": f"Employee {emp_id} not found."}

        return {
            "error": (
                "I can count total employees, list employees by department "
                "(e.g., 'Who is in the HR department?'), show headcount per department, "
                "or look up an employee by ID (e.g., 'who is EMP-0003')."
            )
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

        # Template 2: Largest expense claims overall
        # Example: "top expenses" / "biggest expense claims"
        if "top" in text or "biggest" in text or "largest" in text or "highest" in text:
            sql = (
                "SELECT claim_id, amount, category, date, status FROM expense_claims "
                "WHERE tenant_id = %s ORDER BY amount DESC LIMIT 10"
            )
            results = self._db.execute_read(sql, (user_context.tenant_id,))
            return {"table": "expense_claims", "data": results, "query": sql}

        # Template 3: Expenses by status
        # Example: "pending expense claims" / "approved expenses"
        for status in ("pending", "approved", "rejected"):
            if status in text:
                sql = (
                    "SELECT COUNT(*) as count, COALESCE(SUM(amount),0) as total "
                    "FROM expense_claims WHERE status = %s AND tenant_id = %s"
                )
                results = self._db.execute_read(sql, (status.capitalize(), user_context.tenant_id))
                return {"table": "expense_claims", "data": results, "query": sql}

        # Template 4: Expense total / sum
        # Example: "total expenses" / "sum of expenses"
        if "total" in text or "sum" in text:
            sql = (
                "SELECT COALESCE(SUM(amount),0) as total, COUNT(*) as count "
                "FROM expense_claims WHERE tenant_id = %s"
            )
            results = self._db.execute_read(sql, (user_context.tenant_id,))
            return {"table": "expense_claims", "data": results, "query": sql}

        return {
            "error": (
                "I can show your own expense claims (e.g., 'my expenses'), "
                "list top/largest expense claims, count or sum expenses by status "
                "(e.g., 'pending expenses', 'total expenses')."
            )
        }


# Helpers used by the templates above. Module-level so they are easy to test
# and reuse; kept tiny and side-effect free.


def _extract_amount(text: str) -> float | None:
    """Extract a numeric threshold from a query.

    Handles:
      - bare integers and decimals ("500000", "50000.50")
      - Indian-style lakhs/crores ("5 lakh", "2 crore")
      - shorthand "k" / "100k"
    """
    import re

    m = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|crore|k)?", text)
    if not m:
        return None
    value = float(m.group(1))
    suffix = m.group(2)
    if suffix == "k":
        value *= 1_000
    elif suffix == "lakh":
        value *= 100_000
    elif suffix == "crore":
        value *= 10_000_000
    return value


# Vendor-name hints. In a production system this would come from the
# `vendors` table; for the demo we seed a handful from the bible + corpus.
_VENDOR_HINTS = (
    "bluewave",
    "acme",
    "orion",
    "nexacloud",
    "amazon",
    "aws",
    "google",
    "microsoft",
    "azure",
)
