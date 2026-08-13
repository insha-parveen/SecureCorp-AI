"""PostgreSQL database management for structured enterprise records.

This module handles the connection to the PostgreSQL instance and provides
a way to execute parameterized queries against structured tables.

Improvements over the original implementation:

  * **Connection pooling.** Uses ``psycopg_pool.ConnectionPool`` so
    connections are reused across queries instead of opening a new
    connection per request. This dramatically reduces latency and
    connection churn under load.
  * **Graceful degradation.** If the database is unreachable,
    ``execute_read`` returns an empty list and logs the error instead
    of raising and breaking the request path.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from hybridrag.config import Settings, get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages the connection pool and schema for the structured data store."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._conn_url = self._settings.database_url
        self._pool: ConnectionPool | None = None

    def _get_pool(self) -> ConnectionPool:
        """Lazily create the connection pool on first use.

        The pool is created on first access rather than at construction
        so that importing the module (e.g., in tests or the CLI) never
        opens a database connection as a side effect.
        """
        if self._pool is None:
            self._pool = ConnectionPool(
                self._conn_url,
                min_size=1,
                max_size=10,
                kwargs={"row_factory": dict_row},
                open=False,
            )
            self._pool.open()
        return self._pool

    @contextmanager
    def get_connection(self) -> Iterator[Any]:
        """Yield a pooled connection as a context manager.

        Public accessor over the lazily-opened pool, used by write paths
        such as ``scripts/seed_db.py``. The connection is returned to the
        pool on exit. Callers own their own transaction (``conn.commit()``).
        """
        with self._get_pool().connection() as conn:
            yield conn

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

        CREATE TABLE IF NOT EXISTS query_logs (
            query_id UUID PRIMARY KEY,
            tenant_id VARCHAR(50) NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            query_text TEXT NOT NULL,
            route VARCHAR(50),
            latency_ms INT,
            cache_hit VARCHAR(20),
            response_time_ms INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_ql_tenant ON query_logs(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_ql_created ON query_logs(created_at);
        """
        try:
            with self._get_pool().connection() as conn, conn.cursor() as cur:
                cur.execute(schema)
                conn.commit()
            logger.info("Successfully initialized PostgreSQL schema.")
        except Exception as e:
            logger.error("Failed to initialize PostgreSQL schema: %s", e)
            raise

    def execute_read(self, query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        """Execute a read-only parameterized query.

        Returns results as a list of dictionaries. Returns an empty list
        on any database error (graceful degradation).
        """
        try:
            with self._get_pool().connection() as conn, conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Database read error: %s | Query: %s", e, query)
            return []

    def log_query(
        self,
        query_id: str,
        tenant_id: str,
        user_id: str,
        query_text: str,
        route: str,
        latency_ms: int,
        cache_hit: str,
        response_time_ms: int,
    ) -> None:
        """Log a query execution for analytics.

        Does not raise on failure; logs and skips to avoid breaking the request path.
        """
        try:
            with self._get_pool().connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO query_logs (
                        query_id, tenant_id, user_id, query_text, route,
                        latency_ms, cache_hit, response_time_ms
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        query_id,
                        tenant_id,
                        user_id,
                        query_text,
                        route,
                        latency_ms,
                        cache_hit,
                        response_time_ms,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.warning("Failed to log query: %s", e)

    def close(self) -> None:
        """Close the connection pool. Called on application shutdown."""
        if self._pool is not None:
            self._pool.close()
            self._pool = None

    def ping(self) -> bool:
        """Return True if the database is reachable."""
        try:
            with self._get_pool().connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception:  # noqa: BLE001
            return False
