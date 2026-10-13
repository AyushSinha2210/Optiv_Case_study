"""SQLAlchemy Database engine and session management with strict foreign keys."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from src.cadence_tprm.config import settings

# Configure SQLite engine with foreign key constraints enabled
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Enable foreign key constraint enforcement in SQLite
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None):
    """Safely creates tables and syncs schema for existing SQLite databases non-destructively."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)
    if "sqlite" in settings.DATABASE_URL:
        try:
            with eng.connect() as conn:
                from sqlalchemy import text
                for table_name, table in Base.metadata.tables.items():
                    res = conn.execute(text(f"PRAGMA table_info({table_name})"))
                    existing_cols = {row[1] for row in res.fetchall()}
                    for col in table.columns:
                        if col.name not in existing_cols:
                            col_type = "TEXT"
                            type_str = str(col.type).upper()
                            if "INT" in type_str:
                                col_type = "INTEGER"
                            elif "BOOL" in type_str:
                                col_type = "BOOLEAN"
                            elif "FLOAT" in type_str or "NUMERIC" in type_str:
                                col_type = "FLOAT"
                            elif "DATETIME" in type_str:
                                col_type = "DATETIME"
                            elif "JSON" in type_str:
                                col_type = "JSON"
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}"))
                conn.commit()
        except Exception:
            pass

