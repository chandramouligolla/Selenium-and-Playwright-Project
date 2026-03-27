"""
Multi-DB Connector Utility
============================
Provides connection management for Oracle, PostgreSQL and IBM DB2.
Used across API tests, DB assertion suite and test data provisioning.
"""

import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class OracleConnector:
    """Oracle DB connector using cx_Oracle."""

    def __init__(self):
        self.connection = None
        self.dsn = os.getenv("ORACLE_DSN", "localhost:1521/ORCL")
        self.user = os.getenv("ORACLE_USER", "test_user")
        self.password = os.getenv("ORACLE_PASSWORD", "")

    def connect(self):
        try:
            import cx_Oracle
            self.connection = cx_Oracle.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            logger.info("Oracle connection established")
        except Exception as e:
            logger.error(f"Oracle connection failed: {e}")
            raise

    def execute_query(self, query: str, params: dict = None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or {})
        return cursor.fetchall()

    def execute_dml(self, query: str, params: dict = None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or {})
        self.connection.commit()
        return cursor.rowcount

    def disconnect(self):
        if self.connection:
            self.connection.close()
            logger.info("Oracle connection closed")


class PostgresConnector:
    """PostgreSQL connector using psycopg2."""

    def __init__(self):
        self.connection = None
        self.config = {
            "host":     os.getenv("PG_HOST", "localhost"),
            "port":     int(os.getenv("PG_PORT", 5432)),
            "database": os.getenv("PG_DB", "banking_db"),
            "user":     os.getenv("PG_USER", "test_user"),
            "password": os.getenv("PG_PASSWORD", ""),
        }

    def connect(self):
        try:
            import psycopg2
            self.connection = psycopg2.connect(**self.config)
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def execute_dml(self, query: str, params: tuple = None):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor.rowcount

    def disconnect(self):
        if self.connection:
            self.connection.close()
            logger.info("PostgreSQL connection closed")


class DB2Connector:
    """IBM DB2 connector using ibm_db."""

    def __init__(self):
        self.connection = None
        self.conn_str = (
            f"DATABASE={os.getenv('DB2_DATABASE', 'BANKING')};"
            f"HOSTNAME={os.getenv('DB2_HOST', 'localhost')};"
            f"PORT={os.getenv('DB2_PORT', '50000')};"
            f"PROTOCOL=TCPIP;"
            f"UID={os.getenv('DB2_USER', 'test_user')};"
            f"PWD={os.getenv('DB2_PASSWORD', '')};"
        )

    def connect(self):
        try:
            import ibm_db
            self.connection = ibm_db.connect(self.conn_str, "", "")
            logger.info("IBM DB2 connection established")
        except Exception as e:
            logger.error(f"IBM DB2 connection failed: {e}")
            raise

    def execute_query(self, query: str):
        import ibm_db
        stmt = ibm_db.exec_immediate(self.connection, query)
        results = []
        row = ibm_db.fetch_tuple(stmt)
        while row:
            results.append(row)
            row = ibm_db.fetch_tuple(stmt)
        return results

    def disconnect(self):
        if self.connection:
            import ibm_db
            ibm_db.close(self.connection)
            logger.info("IBM DB2 connection closed")
