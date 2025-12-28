from app.auth import get_current_user
from app.db import get_async_session
from app.models import DiscussionThread, User

from datetime import datetime, UTC
from dotenv import dotenv_values
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    status,
    UploadFile
)
import os
import re
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col
from time import time
from typing import Annotated, TypeGuard


router = APIRouter(
    prefix="/discussion_threads",
    tags=["discussion_threads"],
)

def to_camel_case(snake_case: str) -> str:
    return re.sub(r'_([a-z])', lambda match: match.group(1).upper(),snake_case)

def transform_keys_camel_case(discussion_threads) -> list:
    lst = []
    for discussion_thread in discussion_threads:
        lst.append({
            to_camel_case(key): value for (key, value) in discussion_thread.items()
        })
    return lst

def substitute_user_id_username(query_results) -> list:
    lst = []
    for (discussion_thread, user) in query_results:
        discussion_thread_dict = vars(discussion_thread)
        del discussion_thread_dict["user_id"]
        del discussion_thread_dict["_sa_instance_state"]
        discussion_thread_dict.update({"author": user.username})
        lst.append(discussion_thread_dict)
    return lst

def format_discussion_threads(query_results) -> list:
    substituted_list = substitute_user_id_username(query_results)
    return transform_keys_camel_case(substituted_list)

def remove_image(image_path: str):
    relative_image_path = f".{image_path}"
    if os.path.exists(relative_image_path):
        try:
            os.remove(relative_image_path)
        except OSError as e:
            print(f"{relative_image_path} cannot be removed", str(e))
    else:
        print(f"Trying to remove {relative_image_path}, but path not found")

def is_image(image: UploadFile | None) -> TypeGuard[UploadFile]:
    if image is None:
        return False
    if image.content_type and re.match("image/.+", image.content_type) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Uploaded file is not an image"
        )
    return True

async def save_image(image: UploadFile, username: str, title: str) -> str:
    file_extension_search = image.filename and re.search(r"\..+$", image.filename)
    if not file_extension_search:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Uploaded file is not an image"
        )
    config = dotenv_values(".env")
    image_path = "{}/{}_{}_{}{}".format(
        config.get("IMAGE_PATH"),
        int(time()),
        username,
        title,
        file_extension_search.group()
    )
    try:
        with open(f".{image_path}", "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            return image_path
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))

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
        statement = select(DiscussionThread, User) \
            .where(DiscussionThread.user_id == User.id) \
            .order_by(col(DiscussionThread.created_at).desc())
    else:
        statement = select(DiscussionThread, User) \
            .where(DiscussionThread.user_id == User.id) \
            .where(col(DiscussionThread.title).contains(search_title)) \
            .order_by(col(DiscussionThread.created_at).desc())
    results = await session.execute(statement)
    return format_discussion_threads(results)


@router.post("/create/")
async def create_discussion_thread(
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
    image: UploadFile | None = None,
):
    if is_image(image):
        image_path = await save_image(image, current_user.username, title)
    else:
        image_path = None
    try:
        new_discussion_thread = DiscussionThread(
            user_id=current_user.id,
            title=title,
            content=content,
            image_path=image_path,
        )
        session.add(new_discussion_thread)
        await session.commit()
        return new_discussion_thread
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
    background_tasks: BackgroundTasks,
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
        image_path = discussion_thread.image_path
        if image_path:
            background_tasks.add_task(remove_image, image_path)
        return {"message": "Discussion thread deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )
