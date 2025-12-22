from datetime import datetime, UTC
from sqlalchemy import String
from sqlmodel import Column, DateTime, Field, SQLModel
import uuid


class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(sa_column=Column(String(50), unique=True, index=True, nullable=False))
    hashed_password: str = Field(sa_column=Column(String(128), nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
