from datetime import datetime, UTC
from sqlalchemy import Integer, String, Text, Uuid
from sqlmodel import Column, DateTime, Field, ForeignKey, SQLModel
import uuid


class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(
        sa_column=Column(String(50), unique=True, index=True, nullable=False)
    )
    hashed_password: str = Field(sa_column=Column(String(128), nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class DiscussionThread(SQLModel, table=True):
    __tablename__: str = "discussion_threads"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    user_id: uuid.UUID = Field(
        sa_column=Column(Uuid, ForeignKey("users.id"), index=True, nullable=False)
    )
    title: str = Field(sa_column=Column(String(200), index=True, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    image_path: str | None = Field(sa_column=Column(String(300), nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class DiscussionComment(SQLModel, table=True):
    __tablename__: str = "discussion_comments"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    user_id: uuid.UUID = Field(
        sa_column=Column(Uuid, ForeignKey("users.id"), index=True, nullable=False)
    )
    discussion_thread_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("discussion_threads.id"), index=True, nullable=False
        )
    )
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
