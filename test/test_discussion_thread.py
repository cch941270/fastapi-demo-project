import pytest

@pytest.mark.asyncio
async def test_list_threads(async_client):
    response = await async_client.get("/discussion_threads/")
    assert response.status_code == 200
    assert len(response.json()) == 2

@pytest.mark.asyncio
async def test_create_thread(async_client):
    data = {"title": f"newtitle", "content": f"newcontent"}
    response = await async_client.post("/discussion_threads/create/", data=data)
    assert response.status_code == 200
    assert response.json().get("title") == data.get("title")
    assert response.json().get("content") == data.get("content")

@pytest.mark.asyncio
async def test_get_thread(async_client, mock_discussion_thread):
    response = await async_client.get(f"/discussion_threads/{mock_discussion_thread.id}/")
    assert response.status_code == 200
    assert response.json().get("id") == mock_discussion_thread.id

@pytest.mark.asyncio
async def test_update_thread(async_client, mock_discussion_thread):
    data = {"content": "updatedcontent"}
    response = await async_client.patch(f"/discussion_threads/{mock_discussion_thread.id}/", data=data)
    assert response.status_code == 200
    assert response.json().get("content") == data.get("content")

@pytest.mark.asyncio
async def test_update_thread_unauthorized(async_client, another_mock_discussion_threads):
    data = {"content": "updatedcontent"}
    response = await async_client.patch(f"/discussion_threads/{another_mock_discussion_threads.id}/", data=data)
    assert response.status_code == 401
    assert response.json() == {"detail": "This is not your discussion thread"}

@pytest.mark.asyncio
async def test_delete_thread(async_client, mock_discussion_thread):
    response = await async_client.delete(f"/discussion_threads/{mock_discussion_thread.id}/")
    assert response.status_code == 200
    assert response.json() == {"message": "Discussion thread deleted"}

@pytest.mark.asyncio
async def test_delete_thread_unauthorized(async_client, another_mock_discussion_threads):
    response = await async_client.delete(f"/discussion_threads/{another_mock_discussion_threads.id}/")
    assert response.status_code == 401
    assert response.json() == {"detail": "This is not your discussion thread"}

@pytest.mark.asyncio
async def test_my_discussion_threads(async_client):
    response = await async_client.get("/user/discussion_threads/")
    assert response.status_code == 200
    assert len(response.json()) == 1
