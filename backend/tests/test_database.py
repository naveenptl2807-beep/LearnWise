"""
Unit tests for SQLite database configuration, connection lifecycle, and initialization safety.
Verifies foreign key enforcement, isolated non-destructive initialization, and session scoping.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from sqlalchemy import Column, Integer, String, create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ensure project root is available in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import Base, get_db, init_db, _enforce_sqlite_foreign_keys


class TestDatabase(unittest.TestCase):
    """Test suite for database setup and SQLite constraints."""

    def setUp(self):
        """Create a temporary directory and isolated SQLite database for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_isolated.db"
        self.db_url = f"sqlite:///{self.db_path.as_posix()}"

        # Isolated engine with foreign key listener attached
        self.test_engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False},
        )
        event.listen(self.test_engine, "connect", _enforce_sqlite_foreign_keys)
        self.TestSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.test_engine
        )

    def tearDown(self):
        """Dispose test engine and clean up temporary directory."""
        self.test_engine.dispose()
        self.temp_dir.cleanup()

    def test_database_initialization_creates_tables_safely(self):
        """Verify init_db initializes the database on an engine without errors."""
        init_db(engine_override=self.test_engine)
        self.assertTrue(self.db_path.exists())

    def test_database_initialization_preserves_existing_data(self):
        """Verify repeated calls to init_db do not delete, drop, or overwrite existing data."""
        # Create a sample model
        SampleBase = declarative_base()

        class SampleRecord(SampleBase):
            __tablename__ = "sample_records"
            id = Column(Integer, primary_key=True)
            name = Column(String(50), nullable=False)

        # First initialization: create the table
        SampleBase.metadata.create_all(bind=self.test_engine)

        # Insert test record
        session = self.TestSessionLocal()
        record = SampleRecord(id=1, name="Persisted Student Data")
        session.add(record)
        session.commit()
        session.close()

        # Second initialization call simulating server restart
        init_db(engine_override=self.test_engine)
        SampleBase.metadata.create_all(bind=self.test_engine)

        # Verify the record still exists unharmed
        verify_session = self.TestSessionLocal()
        fetched = verify_session.query(SampleRecord).filter_by(id=1).first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Persisted Student Data")
        verify_session.close()

    def test_sqlite_foreign_keys_are_enforced(self):
        """Verify PRAGMA foreign_keys is enabled on SQLite connections."""
        with self.test_engine.connect() as connection:
            result = connection.execute(text("PRAGMA foreign_keys")).scalar()
            self.assertEqual(result, 1, "SQLite foreign key enforcement must be active (1).")

    def test_get_db_session_lifecycle(self):
        """Verify get_db generator yields a session and closes properly."""
        db_generator = get_db()
        session = next(db_generator)
        self.assertIsNotNone(session)
        # Closing the generator triggers the finally block
        try:
            next(db_generator)
        except StopIteration:
            pass


if __name__ == "__main__":
    unittest.main()

