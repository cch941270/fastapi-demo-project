from app.auth import get_current_user
from app.db import get_async_session
from app.models import DiscussionThread, User

from datetime import datetime, UTC
from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col
from typing import Annotated


router = APIRouter(
    prefix="/discussion_threads",
    tags=["discussion_threads"],
)


async def get_discussion_thread(
    discussion_thread_id: int, session: AsyncSession = Depends(get_async_session)
):
    statement = select(DiscussionThread).where(
        DiscussionThread.id == discussion_thread_id
    )
    results = await session.execute(statement)
    discussion_thread = results.scalar()
    if discussion_thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Discussion thread not found"
        )
    return discussion_thread


@router.get("/")
async def list_discussion_threads(
    search_title: Annotated[str | None, Query(max_length=20)] = None,
    session: AsyncSession = Depends(get_async_session)
):
    if search_title is None:
        statement = select(DiscussionThread)
    else:
        statement = select(DiscussionThread).where(
            col(DiscussionThread.title).contains(search_title)
        )
    results = await session.execute(statement)
    discussion_threads = results.scalars().all()
    return discussion_threads


@router.post("/create/")
async def create_discussion_thread(
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
):
    try:
        new_discussion_thread = DiscussionThread(
            user_id=current_user.id, title=title, content=content
        )
        session.add(new_discussion_thread)
        await session.commit()
        return {"message": "New discussion thread created"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@router.get("/{discussion_thread_id}/")
async def read_discussion_thread(
    discussion_thread: DiscussionThread = Depends(get_discussion_thread),
):
    return discussion_thread


@router.patch("/{discussion_thread_id}/")
async def update_discussion_thread(
    content: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    discussion_thread: DiscussionThread = Depends(get_discussion_thread),
    session: AsyncSession = Depends(get_async_session),
):
    if discussion_thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This is not your discussion thread",
        )
    try:
        discussion_thread.content = content
        discussion_thread.updated_at = datetime.now(UTC)
        session.add(discussion_thread)
        await session.commit()
        return discussion_thread
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@router.delete("/{discussion_thread_id}/")
async def delete_discussion_thread(
    current_user: Annotated[User, Depends(get_current_user)],
    discussion_thread: DiscussionThread = Depends(get_discussion_thread),
    session: AsyncSession = Depends(get_async_session),
):
    if discussion_thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This is not your discussion thread",
        )
    try:
        await session.delete(discussion_thread)
        await session.commit()
        return {"message": "Discussion thread deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )
