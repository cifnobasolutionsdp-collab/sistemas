"""Configuración de la base de datos del portal de suscripciones.

Comparte el motor y la sesión con el sistema de reclutamiento cuando se
ejecutan dentro del mismo proceso. Por omisión utiliza SQLite (archivo
``portal.db``); configurable mediante ``PORTAL_DATABASE_URL``.
"""
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get("PORTAL_DATABASE_URL", "sqlite:///./portal.db")

opciones = {}
if DATABASE_URL.startswith("sqlite"):
    opciones["connect_args"] = {"check_same_thread": False}
    if ":memory:" in DATABASE_URL:
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
