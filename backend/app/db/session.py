"""Database session factory placeholder.

When PostgreSQL is added, this module should own the SQLAlchemy engine,
session dependency, transaction boundaries, and test database overrides.
"""


async def get_db_session():
    raise NotImplementedError("Database session is not wired yet.")

