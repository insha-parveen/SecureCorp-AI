"""PostgreSQL database management for structured enterprise records.

This module handles the connection to the PostgreSQL instance and provides
a way to execute parameterized queries against structured tables.
"""

import logging
from typing import Any

from psycopg import Connection, connect
from psycopg.rows import dict_row

from hybridrag.config import Settings, get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages the connection and schema for the structured data store."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._conn_url = self._settings.database_url

    def get_connection(self) -> Connection[Any]:
        """Return a new connection to the PostgreSQL database."""
        return connect(self._conn_url, row_factory=dict_row)

    def initialize_schema(self) -> None:
        """Create the structured tables if they do not exist.

        Includes basic indexes on tenant_id for isolation performance.
        """
        schema = """
        CREATE TABLE IF NOT EXISTS employees (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            role VARCHAR(100),
            department VARCHAR(100),
            email VARCHAR(255),
            hire_date DATE,
            manager_id VARCHAR(50),
            tenant_id VARCHAR(50) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_emp_tenant ON employees(tenant_id);

        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id VARCHAR(50) PRIMARY KEY,
            amount DECIMAL(12, 2) NOT NULL,
            date DATE NOT NULL,
            vendor VARCHAR(255),
            status VARCHAR(50),
            tenant_id VARCHAR(50) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_inv_tenant ON invoices(tenant_id);

        CREATE TABLE IF NOT EXISTS expense_claims (
            claim_id VARCHAR(50) PRIMARY KEY,
            employee_id VARCHAR(50) REFERENCES employees(id),
            amount DECIMAL(12, 2) NOT NULL,
            category VARCHAR(100),
            date DATE NOT NULL,
            status VARCHAR(50),
            tenant_id VARCHAR(50) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_exp_tenant ON expense_claims(tenant_id);

        CREATE TABLE IF NOT EXISTS it_tickets (
            ticket_id VARCHAR(50) PRIMARY KEY,
            reporter_id VARCHAR(50) REFERENCES employees(id),
            summary TEXT,
            priority VARCHAR(50),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tenant_id VARCHAR(50) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tic_tenant ON it_tickets(tenant_id);
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema)
                conn.commit()
            logger.info("Successfully initialized PostgreSQL schema.")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
            raise

    def execute_read(self, query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        """Execute a read-only parameterized query.

        Returns results as a list of dictionaries.
        """
        try:
            with self.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Database read error: {e} | Query: {query}")
            return []
