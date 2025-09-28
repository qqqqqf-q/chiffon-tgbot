"""Database helpers using SQLAlchemy for Telegram bot."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import config_database

Base = declarative_base()


def _build_database_url() -> str:
    db_conf = getattr(config_database, "database", None)
    if db_conf is None:
        raise RuntimeError("Database configuration missing 'database' section")

    db_type = getattr(db_conf, "type", "sqlite").lower()

    if db_type == "sqlite":
        raw_path = getattr(db_conf, "path", "runtime.db")
        project_root = Path(__file__).resolve().parent.parent
        db_path = (project_root / raw_path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    if db_type == "postgresql":
        username = getattr(db_conf, "username", "")
        password = getattr(db_conf, "password", "")
        host = getattr(db_conf, "host", "localhost")
        port = getattr(db_conf, "port", 5432)
        database = getattr(db_conf, "database", "postgres")
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

    raise ValueError(f"Unsupported database type: {db_type}")


DATABASE_URL = _build_database_url()

echo_flag = bool(getattr(config_database.database, "echo", False))
engine = create_engine(DATABASE_URL, echo=echo_flag, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("telegram_id", name="uq_users_telegram_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(64), nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    role = Column(String(32), nullable=False, default="member")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
        }


class MembershipEvent(Base):
    __tablename__ = "membership_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(64), nullable=False)
    chat_id = Column(String(64), nullable=False)
    chat_title = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    event = Column(String(16), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


@contextmanager
def session_scope() -> Iterator[SessionLocal]:  # type: ignore[type-arg]
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _ensure_sqlite_schema() -> None:
    if not DATABASE_URL.startswith("sqlite:///"):
        return

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(users)"))
        }
        column_defs = {
            "first_name": "TEXT",
            "last_name": "TEXT",
            "is_active": "INTEGER DEFAULT 1",
            "left_at": "DATETIME",
        }
        for column, definition in column_defs.items():
            if column not in columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {column} {definition}"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_schema()


def add_or_update_user(
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    telegram_id_str = str(telegram_id)
    with session_scope() as session:
        user: Optional[User] = session.query(User).filter_by(telegram_id=telegram_id_str).one_or_none()
        if user:
            user.username = username or user.username
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            if role:
                user.role = role
            user.is_active = True
            user.left_at = None
        else:
            user = User(
                telegram_id=telegram_id_str,
                username=username,
                first_name=first_name,
                last_name=last_name,
                role=role or "member",
                is_active=True,
            )
            session.add(user)
        session.flush()
        session.refresh(user)
        return user.to_dict()


def get_user_by_id(telegram_id: int) -> Optional[Dict[str, Optional[str]]]:
    with session_scope() as session:
        user = session.query(User).filter_by(telegram_id=str(telegram_id)).one_or_none()
        return user.to_dict() if user else None


def set_user_role(telegram_id: int, role: str) -> Optional[Dict[str, Optional[str]]]:
    with session_scope() as session:
        user = session.query(User).filter_by(telegram_id=str(telegram_id)).one_or_none()
        if not user:
            return None
        user.role = role
        session.flush()
        session.refresh(user)
        return user.to_dict()


def list_users() -> List[Dict[str, Optional[str]]]:
    with session_scope() as session:
        users = session.query(User).order_by(User.created_at.asc()).all()
        return [user.to_dict() for user in users]


def remove_user(telegram_id: int) -> bool:
    with session_scope() as session:
        user = session.query(User).filter_by(telegram_id=str(telegram_id)).one_or_none()
        if not user:
            return False
        session.delete(user)
        return True


def mark_user_inactive(telegram_id: int) -> Optional[Dict[str, Optional[str]]]:
    with session_scope() as session:
        user = session.query(User).filter_by(telegram_id=str(telegram_id)).one_or_none()
        if not user:
            return None
        user.is_active = False
        user.left_at = datetime.utcnow()
        session.flush()
        session.refresh(user)
        return user.to_dict()


def user_has_role(telegram_id: int, *roles: str) -> bool:
    user = get_user_by_id(telegram_id)
    if not user:
        return False
    return user.get("role") in roles


def record_membership_event(
    telegram_id: int,
    chat_id: int,
    event: str,
    chat_title: Optional[str] = None,
    username: Optional[str] = None,
) -> None:
    if event not in {"join", "leave"}:
        raise ValueError("event must be 'join' or 'leave'")
    with session_scope() as session:
        session.add(
            MembershipEvent(
                telegram_id=str(telegram_id),
                chat_id=str(chat_id),
                chat_title=chat_title,
                username=username,
                event=event,
            )
        )


__all__ = [
    "User",
    "MembershipEvent",
    "engine",
    "SessionLocal",
    "init_db",
    "add_or_update_user",
    "get_user_by_id",
    "set_user_role",
    "list_users",
    "remove_user",
    "user_has_role",
    "mark_user_inactive",
    "record_membership_event",
]
