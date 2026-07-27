"""Configuración de la base de datos.

Por omisión utiliza SQLite (archivo local ``sistemas.db``). Para producción
puede apuntarse a otro motor definiendo la variable de entorno
``DATABASE_URL`` (por ejemplo PostgreSQL o SQL Server).
"""
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sistemas.db")

opciones = {}
if DATABASE_URL.startswith("sqlite"):
    opciones["connect_args"] = {"check_same_thread": False}
    if ":memory:" in DATABASE_URL:
        # Una sola conexión compartida para que la base en memoria sea visible
        # desde todos los hilos (pruebas).
        opciones["poolclass"] = StaticPool
engine = create_engine(DATABASE_URL, **opciones)

if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
